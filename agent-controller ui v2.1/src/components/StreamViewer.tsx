import { useState, useEffect, useRef } from 'react';
import { useSocket } from './SocketProvider';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Play, 
  Pause, 
  Square, 
  Volume2, 
  VolumeX, 
  Maximize2, 
  Settings,
  Monitor,
  Camera,
  Mic,
  AlertCircle
} from 'lucide-react';
import { cn } from './ui/utils';
import { toast } from 'sonner';

interface StreamViewerProps {
  agentId: string | null;
  type: 'screen' | 'camera' | 'audio';
  title: string;
}

export function StreamViewer({ agentId, type, title }: StreamViewerProps) {
  const { sendCommand, socket } = useSocket();
  const [isStreaming, setIsStreaming] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [quality, setQuality] = useState('high');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [lastFrameTime, setLastFrameTime] = useState<number>(0);
  const [fps, setFps] = useState(0);
  const [bandwidth, setBandwidth] = useState(0);
  const [hasError, setHasError] = useState(false);
  
  const imgRef = useRef<HTMLImageElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingAudioRef = useRef(false);
  const fpsIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const frameCountRef = useRef(0);

  const getStreamIcon = () => {
    switch (type) {
      case 'screen': return Monitor;
      case 'camera': return Camera;
      case 'audio': return Mic;
      default: return Monitor;
    }
  };

  const StreamIcon = getStreamIcon();

  // Initialize Audio Context
  const initAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 44100,
        latencyHint: 'interactive'
      });
    }
    return audioContextRef.current;
  };

  // Play audio frame using Web Audio API
  const playAudioFrame = async (base64Data: string) => {
    try {
      const audioContext = initAudioContext();
      
      // Decode base64 to binary
      const binaryString = atob(base64Data);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      
      // For PCM audio (16-bit samples)
      // Convert bytes to Float32Array for Web Audio API
      const samples = new Int16Array(bytes.buffer);
      const floatSamples = new Float32Array(samples.length);
      for (let i = 0; i < samples.length; i++) {
        floatSamples[i] = samples[i] / 32768.0; // Convert to -1.0 to 1.0 range
      }
      
      // Add to audio queue
      audioQueueRef.current.push(floatSamples);
      
      // Start playing if not already playing
      if (!isPlayingAudioRef.current) {
        isPlayingAudioRef.current = true;
        scheduleAudioPlayback();
      }
    } catch (error) {
      console.error('Error processing audio frame:', error);
    }
  };

  // Schedule audio playback from queue
  const scheduleAudioPlayback = () => {
    const audioContext = audioContextRef.current;
    if (!audioContext) return;

    const playNextChunk = () => {
      if (audioQueueRef.current.length === 0) {
        isPlayingAudioRef.current = false;
        return;
      }

      const samples = audioQueueRef.current.shift();
      if (!samples) return;

      // Create audio buffer
      const audioBuffer = audioContext.createBuffer(1, samples.length, 44100);
      const channelData = audioBuffer.getChannelData(0);
      channelData.set(samples);

      // Create buffer source and play
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      source.start();

      // Schedule next chunk
      const duration = samples.length / 44100;
      setTimeout(playNextChunk, duration * 1000 * 0.9); // Slight overlap to prevent gaps
    };

    playNextChunk();
  };

  // Cleanup audio context on unmount
  useEffect(() => {
    return () => {
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      audioQueueRef.current = [];
      isPlayingAudioRef.current = false;
    };
  }, []);

  // Calculate FPS every second
  useEffect(() => {
    if (isStreaming) {
      fpsIntervalRef.current = setInterval(() => {
        setFps(frameCountRef.current);
        frameCountRef.current = 0;
      }, 1000);
    } else {
      if (fpsIntervalRef.current) {
        clearInterval(fpsIntervalRef.current);
        fpsIntervalRef.current = null;
      }
      setFps(0);
      frameCountRef.current = 0;
    }

    return () => {
      if (fpsIntervalRef.current) {
        clearInterval(fpsIntervalRef.current);
      }
    };
  }, [isStreaming]);

  // Listen for frame events
  useEffect(() => {
    if (!isStreaming || !agentId) return;

    const eventName = type === 'screen' ? 'screen_frame' : type === 'camera' ? 'camera_frame' : 'audio_frame';

    const handleFrame = (event: any) => {
      const data = event.detail;
      
      // Check if frame is for this agent
      if (data.agent_id !== agentId) return;

      setHasError(false);
      
      try {
        const frame = data.frame;
        
        if (type === 'audio') {
          // Audio handling - decode and play
          try {
            playAudioFrame(frame);
            frameCountRef.current++;
            setFrameCount(prev => prev + 1);
          } catch (audioError) {
            console.error('Error playing audio frame:', audioError);
          }
        } else {
          // Video frame handling
          if (imgRef.current) {
            // If frame is already a data URL, use it directly
            if (typeof frame === 'string' && frame.startsWith('data:')) {
              imgRef.current.src = frame;
            } else {
              // Otherwise, assume it's base64 encoded
              imgRef.current.src = `data:image/jpeg;base64,${frame}`;
            }
            
            // Update frame counter and stats
            frameCountRef.current++;
            setFrameCount(prev => prev + 1);
            
            const now = Date.now();
            if (lastFrameTime > 0) {
              const timeDiff = now - lastFrameTime;
              if (timeDiff > 0) {
                const currentFps = 1000 / timeDiff;
                // Estimate bandwidth (assuming JPEG frame ~50KB average)
                setBandwidth(Math.round((currentFps * 50) / 1024)); // MB/s
              }
            }
            setLastFrameTime(now);
          }
        }
      } catch (error) {
        console.error(`Error displaying ${type} frame:`, error);
        setHasError(true);
      }
    };

    window.addEventListener(eventName, handleFrame);

    return () => {
      window.removeEventListener(eventName, handleFrame);
    };
  }, [isStreaming, agentId, type, lastFrameTime]);

  const handleStartStop = () => {
    if (!agentId) {
      toast.error('Please select an agent first');
      return;
    }

    if (isStreaming) {
      // Stop streaming
      let command = '';
      switch (type) {
        case 'screen':
          command = 'stop-stream';
          break;
        case 'camera':
          command = 'stop-camera';
          break;
        case 'audio':
          command = 'stop-audio';
          break;
      }
      
      sendCommand(agentId, command);
      setIsStreaming(false);
      setFrameCount(0);
      setFps(0);
      setBandwidth(0);
      setHasError(false);
      
      if (imgRef.current) {
        imgRef.current.src = '';
      }
      
      // Cleanup audio context for audio streams
      if (type === 'audio' && audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
        audioQueueRef.current = [];
        isPlayingAudioRef.current = false;
      }
      
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} stream stopped`);
    } else {
      // Start streaming
      let command = '';
      switch (type) {
        case 'screen':
          command = 'start-stream';
          break;
        case 'camera':
          command = 'start-camera';
          break;
        case 'audio':
          command = 'start-audio';
          break;
      }
      
      sendCommand(agentId, command);
      setIsStreaming(true);
      setHasError(false);
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} stream started`);
    }
  };

  const handleQualityChange = (newQuality: string) => {
    setQuality(newQuality);
    toast.info(`Quality set to ${newQuality}`);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Reset streaming state when agent changes
  useEffect(() => {
    if (isStreaming) {
      setIsStreaming(false);
      setFrameCount(0);
      setFps(0);
      setBandwidth(0);
      if (imgRef.current) {
        imgRef.current.src = '';
      }
    }
  }, [agentId]);

  return (
    <Card className={cn("transition-all", isFullscreen && "fixed inset-4 z-50")}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <StreamIcon className="h-4 w-4" />
            <CardTitle className="text-sm">{title}</CardTitle>
            {agentId && (
              <Badge variant="outline" className="text-xs">
                {agentId.substring(0, 8)}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Select value={quality} onValueChange={handleQualityChange}>
              <SelectTrigger className="w-20 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Med</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="ultra">Ultra</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="ghost" size="sm" onClick={toggleFullscreen}>
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Button 
              size="sm" 
              variant={isStreaming ? "destructive" : "default"}
              onClick={handleStartStop}
              disabled={!agentId}
            >
              {isStreaming ? (
                <>
                  <Square className="h-3 w-3 mr-1" />
                  Stop
                </>
              ) : (
                <>
                  <Play className="h-3 w-3 mr-1" />
                  Start
                </>
              )}
            </Button>
            
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setIsMuted(!isMuted);
                // Mute/unmute audio context if it's an audio stream
                if (type === 'audio' && audioContextRef.current) {
                  if (!isMuted) {
                    audioContextRef.current.suspend();
                  } else {
                    audioContextRef.current.resume();
                  }
                }
              }}
              disabled={!isStreaming}
            >
              {isMuted ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
            </Button>
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            {isStreaming && !hasError && (
              <>
                <Badge variant="secondary">{fps} FPS</Badge>
                <Badge variant="secondary">{bandwidth.toFixed(1)} MB/s</Badge>
                <Badge variant="secondary">{frameCount} frames</Badge>
              </>
            )}
            {hasError && (
              <Badge variant="destructive" className="text-xs">
                <AlertCircle className="h-3 w-3 mr-1" />
                Error
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="aspect-video bg-black rounded-lg flex items-center justify-center relative overflow-hidden">
          {!agentId ? (
            <div className="text-center text-muted-foreground">
              <StreamIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Select an agent to view stream</p>
            </div>
          ) : !isStreaming ? (
            <div className="text-center text-muted-foreground">
              <StreamIcon className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p className="text-sm">Stream not active</p>
              <p className="text-xs mt-1">Click Start to begin streaming</p>
            </div>
          ) : hasError ? (
            <div className="text-center text-red-400">
              <AlertCircle className="h-12 w-12 mx-auto mb-2" />
              <p className="text-sm">Stream Error</p>
              <p className="text-xs mt-1">No frames received</p>
            </div>
          ) : type === 'audio' ? (
            <div className="w-full h-full bg-gradient-to-br from-purple-900 to-pink-900 flex items-center justify-center">
              <div className="text-white text-center">
                <Mic className="h-16 w-16 mx-auto mb-4 animate-pulse" />
                <p className="text-lg font-medium">Audio Stream Active</p>
                <p className="text-sm opacity-80">Agent: {agentId.substring(0, 8)}</p>
                <div className="mt-4 flex justify-center space-x-1">
                  {[...Array(10)].map((_, i) => (
                    <div 
                      key={i}
                      className="w-1 bg-green-500 rounded-full animate-pulse"
                      style={{ 
                        height: `${Math.random() * 40 + 20}px`,
                        animationDelay: `${i * 0.1}s`
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <>
              <img 
                ref={imgRef}
                alt={`${type} stream`}
                className="w-full h-full object-contain"
                style={{ display: frameCount > 0 ? 'block' : 'none' }}
              />
              {frameCount === 0 && (
                <div className="text-center text-muted-foreground">
                  <StreamIcon className="h-12 w-12 mx-auto mb-2 animate-pulse" />
                  <p className="text-sm">Waiting for frames...</p>
                  <p className="text-xs mt-1">Connecting to agent</p>
                </div>
              )}
            </>
          )}
          
          {isStreaming && frameCount > 0 && !hasError && (
            <div className="absolute top-2 left-2 flex items-center space-x-2">
              <div className="flex items-center space-x-1 bg-black/70 text-white px-2 py-1 rounded text-xs">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span>LIVE</span>
              </div>
              <div className="bg-black/70 text-white px-2 py-1 rounded text-xs">
                {quality.toUpperCase()}
              </div>
              <div className="bg-black/70 text-white px-2 py-1 rounded text-xs">
                {fps} FPS
              </div>
            </div>
          )}
        </div>
        
        {isStreaming && frameCount > 0 && !hasError && (
          <div className="mt-4 text-xs text-muted-foreground">
            <div className="flex justify-between items-center">
              <span>Status: Active • Frames: {frameCount}</span>
              <span>Bandwidth: {bandwidth.toFixed(1)} MB/s</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
