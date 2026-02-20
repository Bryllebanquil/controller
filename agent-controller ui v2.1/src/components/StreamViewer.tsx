import React, { useState, useEffect, useRef } from 'react';
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
  AlertCircle,
  Keyboard,
  Camera as CameraIcon
} from 'lucide-react';
import { cn } from './ui/utils';
import { toast } from 'sonner';
import apiClient from '../services/api';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';

interface StreamViewerProps {
  agentId: string | null;
  type: 'screen' | 'camera' | 'audio';
  title: string;
  defaultCaptureMouse?: boolean;
  defaultCaptureKeyboard?: boolean;
  autoResume?: boolean;
  hideCursor?: boolean;
}

export function StreamViewer({ agentId, type, title, defaultCaptureMouse, defaultCaptureKeyboard, autoResume = true, hideCursor = true }: StreamViewerProps) {
  const { sendCommand, socket, setLastActivity, agents } = useSocket();
  const [isStreaming, setIsStreaming] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [quality, setQuality] = useState('high');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [frameCount, setFrameCount] = useState(0);
  const [lastFrameTime, setLastFrameTime] = useState<number>(0);
  const [fps, setFps] = useState(0);
  const [bandwidth, setBandwidth] = useState(0);
  const [hasError, setHasError] = useState(false);
  const [isWebRTCActive, setIsWebRTCActive] = useState(false);
  const [transportMode, setTransportMode] = useState<'auto' | 'webrtc' | 'fallback'>('auto');
  const [webrtcIceServers, setWebrtcIceServers] = useState<RTCIceServer[]>([]);
  const [captureKeyboard, setCaptureKeyboard] = useState(typeof defaultCaptureKeyboard === 'boolean' ? defaultCaptureKeyboard : true);
  const [captureMouse, setCaptureMouse] = useState(typeof defaultCaptureMouse === 'boolean' ? defaultCaptureMouse : false);
  const [modCtrl, setModCtrl] = useState(false);
  const [modAlt, setModAlt] = useState(false);
  const [modShift, setModShift] = useState(false);
  const [modMeta, setModMeta] = useState(false);
  const [textToSend, setTextToSend] = useState('');
  
  const imgRef = useRef<HTMLImageElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const audioElRef = useRef<HTMLAudioElement | null>(null);
  const rtcPcRef = useRef<RTCPeerConnection | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<Float32Array[]>([]);
  const isPlayingAudioRef = useRef(false);
  const audioDecoderRef = useRef<any | null>(null);
  const opusInitializedRef = useRef(false);
  const webrtcTimeoutRef = useRef<number | null>(null);
  const fallbackTriggeredRef = useRef(false);
  const fpsIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const frameCountRef = useRef(0);
  const prevCountRef = useRef(0);
  const lastFrameTimeRef = useRef(0);
  const frameQueueRef = useRef<{ frame: string | Uint8Array; receivedAt: number }[]>([]);
  const renderLoopRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const renderFpsRef = useRef(20);
  const latestBaselineRef = useRef<number>(0);
  const lastMouseEmitRef = useRef<number>(0);
  const [remoteCursor, setRemoteCursor] = useState<{ x: number; y: number; visible: boolean } | null>(null);
  const lastKeyEmitRef = useRef<number>(0);
  const [webrtcAudioBridge, setWebrtcAudioBridge] = useState(false);
  const [showRemoteCursor, setShowRemoteCursor] = useState(false);
  const [agentCursorEmit, setAgentCursorEmit] = useState(false);
  const [preRollActive, setPreRollActive] = useState(false);
  const preRollMsRef = useRef(3000);
  const preRollStartRef = useRef(0);

  const getStreamIcon = () => {
    switch (type) {
      case 'screen': return Monitor;
      case 'camera': return Camera;
      case 'audio': return Mic;
      default: return Monitor;
    }
  };

  const StreamIcon = getStreamIcon();

  // Screenshot capture function
  const handleScreenshot = async () => {
    if (!isStreaming) {
      toast.error('Stream must be active to capture screenshot');
      return;
    }

    try {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (type === 'audio') {
        toast.error('Cannot capture screenshot from audio stream');
        return;
      }

      let source: HTMLVideoElement | HTMLImageElement | null = null;
      
      if (type === 'screen' || type === 'camera') {
        if (videoRef.current && videoRef.current.videoWidth > 0) {
          source = videoRef.current;
        } else if (imgRef.current && imgRef.current.naturalWidth > 0) {
          source = imgRef.current;
        }
      }

      if (!source) {
        toast.error('No active video source found');
        return;
      }

      if (source instanceof HTMLVideoElement) {
        canvas.width = source.videoWidth;
        canvas.height = source.videoHeight;
      } else {
        canvas.width = source.naturalWidth;
        canvas.height = source.naturalHeight;
      }
      
      ctx?.drawImage(source, 0, 0, canvas.width, canvas.height);
      
      // Convert to blob and download
      canvas.toBlob((blob) => {
        if (!blob) {
          toast.error('Failed to create screenshot');
          return;
        }
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `screenshot-${agentId}-${type}-${Date.now()}.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        toast.success('Screenshot captured successfully');
      }, 'image/png');
      
    } catch (error) {
      console.error('Screenshot capture error:', error);
      toast.error('Failed to capture screenshot');
    }
  };

  // Initialize Audio Context
  const initAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 44100,
        latencyHint: 'interactive'
      });
      try {
        audioContextRef.current.resume().catch(() => {});
      } catch {}
    }
    return audioContextRef.current;
  };

  // Play audio frame using Web Audio API
  const playAudioFrame = async (payload: string | ArrayBuffer | Uint8Array) => {
    try {
      const audioContext = initAudioContext();
      try {
        if (audioContext.state === 'suspended') {
          await audioContext.resume();
        }
      } catch {}
      
      // Normalize payload to Uint8Array
      let bytes: Uint8Array;
      if (typeof payload === 'string') {
        const binaryString = atob(payload);
        bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
      } else if (payload instanceof Uint8Array) {
        bytes = payload;
      } else if (payload instanceof ArrayBuffer) {
        bytes = new Uint8Array(payload);
      } else {
        return;
      }
      
      const isLikelyPCM16 = bytes.length % 2 === 0;
      const isOgg = bytes.length >= 4 && bytes[0] === 0x4f && bytes[1] === 0x67 && bytes[2] === 0x67 && bytes[3] === 0x53;
      const isWebM = bytes.length >= 4 && bytes[0] === 0x1a && bytes[1] === 0x45 && bytes[2] === 0xdf && bytes[3] === 0xa3;
      const canUseWebCodecs = typeof (window as any).AudioDecoder !== 'undefined';
      
      if (!isLikelyPCM16 && canUseWebCodecs) {
        try {
          await decodeOpusFrame(bytes);
          return;
        } catch {
          /* fallthrough to PCM */
        }
      }
      
      // For PCM audio (16-bit samples)
      // Convert bytes to Float32Array for Web Audio API (respect byteOffset)
      const samples16 = new Int16Array(bytes.buffer, bytes.byteOffset, Math.floor(bytes.byteLength / 2));
      const floatSamples = new Float32Array(samples16.length);
      for (let i = 0; i < samples16.length; i++) {
        floatSamples[i] = samples16[i] / 32768.0;
      }
      
      // Add to audio queue
      audioQueueRef.current.push(floatSamples);
      
      // Start playing if not already playing; wait for a minimal pre-roll to prevent crackle
      if (!isPlayingAudioRef.current) {
        const prerollBuffers = 2;
        if (audioQueueRef.current.length < prerollBuffers) {
          // Allow a tiny delay to accumulate samples
          setTimeout(() => {
            if (!isPlayingAudioRef.current) {
              isPlayingAudioRef.current = true;
              scheduleAudioPlayback();
            }
          }, 20);
        } else {
          isPlayingAudioRef.current = true;
          scheduleAudioPlayback();
        }
      }
    } catch (error) {
      console.error('Error processing audio frame:', error);
    }
  };

  const normalizeFramePayload = (payload: any): string | Uint8Array | null => {
    if (typeof payload === 'string') {
      const s = payload.startsWith('data:') ? payload.split(',')[1] || '' : payload;
      return s || null;
    }
    if (payload instanceof Uint8Array) return payload;
    if (payload instanceof ArrayBuffer) return new Uint8Array(payload);
    if (payload && typeof payload === 'object' && 'byteLength' in payload) {
      return new Uint8Array(payload as ArrayBuffer);
    }
    return null;
  };

  const drawFrameToCanvas = (payload: string | Uint8Array) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let blob: Blob | null = null;
    if (typeof payload === 'string') {
      if (!payload) return;
      const binary = atob(payload);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      blob = new Blob([bytes], { type: 'image/jpeg' });
    } else {
      const view = payload instanceof Uint8Array ? payload : new Uint8Array(payload);
      const copy = new Uint8Array(view.byteLength);
      copy.set(view);
      blob = new Blob([copy.buffer], { type: 'image/jpeg' });
    }
    if (!blob) return;
    createImageBitmap(blob).then((bitmap) => {
      if (!canvas) return;
      if (canvas.width !== bitmap.width || canvas.height !== bitmap.height) {
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;
      }
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(bitmap, 0, 0);
      }
    }).catch(() => {});
  };
  const drawTileToCanvas = (x: number, y: number, w: number, h: number, payload: string | Uint8Array) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    let blob: Blob | null = null;
    if (typeof payload === 'string') {
      if (!payload) return;
      const binary = atob(payload);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) {
        bytes[i] = binary.charCodeAt(i);
      }
      blob = new Blob([bytes], { type: 'image/jpeg' });
    } else {
      const view = payload instanceof Uint8Array ? payload : new Uint8Array(payload);
      const copy = new Uint8Array(view.byteLength);
      copy.set(view);
      blob = new Blob([copy.buffer], { type: 'image/jpeg' });
    }
    if (!blob) return;
    createImageBitmap(blob).then((bitmap) => {
      const ctx = canvas?.getContext('2d');
      if (!ctx || !canvas) return;
      // Ensure canvas exists with correct size; tiles rely on keyframe establishing dimensions
      const dw = w || bitmap.width;
      const dh = h || bitmap.height;
      ctx.drawImage(bitmap, x, y, dw, dh);
    }).catch(() => {});
  };

  const ensureAudioDecoder = () => {
    if (audioDecoderRef.current) return audioDecoderRef.current;
    const AudioDecoderCtor = (window as any).AudioDecoder;
    if (!AudioDecoderCtor) return null;
    const audioContext = initAudioContext();
    const decoder = new AudioDecoderCtor({
      output: (audioData: any) => {
        try {
          const sampleRate = audioData.sampleRate || 48000;
          const frames = audioData.numberOfFrames || 0;
          if (!frames) return;
          const buffer = audioContext.createBuffer(audioData.numberOfChannels || 1, frames, sampleRate);
          for (let ch = 0; ch < buffer.numberOfChannels; ch++) {
            const arr = new Float32Array(frames);
            audioData.copyTo(arr, { planeIndex: ch });
            buffer.getChannelData(ch).set(arr);
          }
          const source = audioContext.createBufferSource();
          source.buffer = buffer;
          source.connect(audioContext.destination);
          source.start();
        } catch (e) {
        }
      },
      error: (_e: any) => {
      }
    });
    try {
      decoder.configure({ codec: 'opus', sampleRate: 48000, numberOfChannels: 1 });
      opusInitializedRef.current = true;
    } catch {
      opusInitializedRef.current = false;
    }
    audioDecoderRef.current = decoder;
    return decoder;
  };

  const decodeOpusFrame = async (bytes: Uint8Array) => {
    const decoder = ensureAudioDecoder();
    if (!decoder || !opusInitializedRef.current) throw new Error('AudioDecoder not available');
    const ts = performance.now();
    const chunk = new (window as any).EncodedAudioChunk({
      type: 'key',
      timestamp: Math.floor(ts * 1000),
      data: bytes
    });
    decoder.decode(chunk);
  };

  // Schedule audio playback from queue
  const playHeadRef = useRef<number>(0);
  const scheduleAudioPlayback = () => {
    const audioContext = audioContextRef.current;
    if (!audioContext) return;
    if (audioQueueRef.current.length === 0) {
      isPlayingAudioRef.current = false;
      return;
    }
    // Initialize play head slightly in the future
    if (playHeadRef.current <= audioContext.currentTime) {
      playHeadRef.current = audioContext.currentTime + 0.05;
    }
    while (audioQueueRef.current.length) {
      const samples = audioQueueRef.current.shift();
      if (!samples) break;
      const duration = samples.length / 44100;
      const audioBuffer = audioContext.createBuffer(1, samples.length, 44100);
      const channelData = audioBuffer.getChannelData(0);
      channelData.set(samples);
      const source = audioContext.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(audioContext.destination);
      try {
        source.start(playHeadRef.current);
      } catch {
        source.start();
      }
      playHeadRef.current += duration;
    }
    isPlayingAudioRef.current = false;
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
        const avg = Math.round((prevCountRef.current + frameCountRef.current) / 2);
        setFps(avg);
        prevCountRef.current = frameCountRef.current;
        frameCountRef.current = 0;
      }, 1000);
    } else {
      if (fpsIntervalRef.current) {
        clearInterval(fpsIntervalRef.current);
        fpsIntervalRef.current = null;
      }
      setFps(0);
      frameCountRef.current = 0;
      prevCountRef.current = 0;
    }

    return () => {
      if (fpsIntervalRef.current) {
        clearInterval(fpsIntervalRef.current);
      }
    };
  }, [isStreaming]);

  useEffect(() => {
    let active = true;
    (async () => {
      const s = await apiClient.getSettings();
      const arr = (s?.data?.webrtc?.iceServers || []) as string[];
      const servers: RTCIceServer[] = Array.isArray(arr)
        ? arr.map((u: any) => typeof u === 'string' ? ({ urls: u }) : u)
        : [];
      if (active) setWebrtcIceServers(servers);
    })();
    return () => { active = false; };
  }, []);

  // Socket.IO buffered streaming: listen for frames
  useEffect(() => {
    if (!isStreaming || !agentId) return;
    const eventName = type === 'screen' ? 'screen_frame' : type === 'camera' ? 'camera_frame' : 'audio_frame';
    const handleFrame = (event: any) => {
      const data = event.detail;
      if (data.agent_id !== agentId) return;
      setHasError(false);
      try {
        const frame = data.frame;
        if (type === 'audio') {
          try {
            playAudioFrame(frame);
            frameCountRef.current++;
            setFrameCount((prev: number) => prev + 1);
          } catch {}
        } else {
          const normalized = normalizeFramePayload(frame);
          if (normalized) {
            const queue = frameQueueRef.current;
            queue.push({ frame: normalized, receivedAt: Date.now() });
          }
        }
      } catch {
        setHasError(true);
      }
    };
    window.addEventListener(eventName, handleFrame);
    return () => {
      window.removeEventListener(eventName, handleFrame);
    };
  }, [isStreaming, agentId, type]);

  useEffect(() => {
    if (!isStreaming || !agentId) return;
    if (type === 'audio') return;
    const intervalMs = Math.max(10, Math.floor(1000 / Math.max(1, renderFpsRef.current)));
    if (renderLoopRef.current) {
      clearInterval(renderLoopRef.current);
      renderLoopRef.current = null;
    }
    renderLoopRef.current = setInterval(() => {
      const queue = frameQueueRef.current;
      if (!queue.length) return;
      const cap = Math.max(30, Math.floor((preRollMsRef.current / 1000) * renderFpsRef.current) * 2);
      if (queue.length > cap) queue.splice(0, queue.length - cap);
      const nowTs = Date.now();
      if (preRollActive) {
        const oldest = queue[0];
        if (!oldest) return;
        const age = nowTs - oldest.receivedAt;
        if (age < preRollMsRef.current) return;
        setPreRollActive(false);
      }
      let item: { frame: any; receivedAt: number } | null = null;
      while (queue.length) {
        const age = nowTs - queue[0].receivedAt;
        if (age >= preRollMsRef.current) {
          item = queue.shift() as any;
        } else {
          break;
        }
      }
      if (!item) {
        item = queue.shift() as any;
        if (!item) return;
      }
      drawFrameToCanvas(item.frame);
      frameCountRef.current++;
      setFrameCount((prev: number) => prev + 1);
      const now = Date.now();
      const prev = lastFrameTimeRef.current;
      if (prev > 0) {
        const timeDiff = now - prev;
        if (timeDiff > 0) {
          const currentFps = 1000 / timeDiff;
          setBandwidth(Math.round((currentFps * 50) / 1024));
        }
      }
      lastFrameTimeRef.current = now;
      setLastFrameTime(now);
    }, intervalMs);
    return () => {
      if (renderLoopRef.current) {
        clearInterval(renderLoopRef.current);
        renderLoopRef.current = null;
      }
      frameQueueRef.current = [];
    };
  }, [isStreaming, agentId, type]);
  useEffect(() => {
    if (!isStreaming || !agentId || type !== 'screen') return;
    const onKeyframe = (event: any) => {
      const data = event.detail || {};
      if (data.agent_id !== agentId) return;
      const fid = Number(data.frame_id || 0);
      if (Number.isFinite(fid) && fid > 0) latestBaselineRef.current = fid;
      try {
        const canvas = canvasRef.current;
        if (canvas) {
          const w = Number(data.width || 0);
          const h = Number(data.height || 0);
          if (w > 0 && h > 0) {
            canvas.width = w;
            canvas.height = h;
          }
        }
      } catch {}
      const payload = data.frame as any;
      drawFrameToCanvas(payload);
      setFrameCount(prev => prev + 1);
      const now = Date.now();
      lastFrameTimeRef.current = now;
      setLastFrameTime(now);
    };
    const onTile = (event: any) => {
      const data = event.detail || {};
      if (data.agent_id !== agentId) return;
      const fid = Number(data.frame_id || 0);
      if (!latestBaselineRef.current || (Number.isFinite(fid) && fid < latestBaselineRef.current)) return;
      const payload = data.frame as any;
      const x = Number(data.x || 0);
      const y = Number(data.y || 0);
      const w = Number(data.w || 0);
      const h = Number(data.h || 0);
      drawTileToCanvas(x, y, w, h, payload);
      setFrameCount(prev => prev + 1);
    };
    window.addEventListener('screen_keyframe', onKeyframe);
    window.addEventListener('screen_tile', onTile);
    return () => {
      window.removeEventListener('screen_keyframe', onKeyframe);
      window.removeEventListener('screen_tile', onTile);
    };
  }, [isStreaming, agentId, type]);

  useEffect(() => {
    if (!socket || !isStreaming || !agentId) return;
    const req = () => {
      if (type === 'screen') {
        socket.emit('request_video_frame', { agent_id: agentId });
      } else if (type === 'camera') {
        socket.emit('request_camera_frame', { agent_id: agentId });
      } else {
        socket.emit('request_audio_frame', { agent_id: agentId });
      }
    };
    req();
    const interval = window.setInterval(() => {
      if (frameCountRef.current === 0 && (!frameQueueRef.current || frameQueueRef.current.length === 0)) req();
    }, 1500);
    return () => {
      window.clearInterval(interval);
    };
  }, [socket, isStreaming, agentId, type]);
  // Also listen for audio frames when viewing screen/camera in fallback mode
  useEffect(() => {
    if (!isStreaming || !agentId) return;
    if (!(type === 'screen' || type === 'camera')) return;
    const handleAudioFrame = (event: any) => {
      const data = event.detail;
      if (data.agent_id !== agentId) return;
      try {
        playAudioFrame(data.frame);
      } catch {}
    };
    window.addEventListener('audio_frame', handleAudioFrame);
    return () => {
      window.removeEventListener('audio_frame', handleAudioFrame);
    };
  }, [isStreaming, agentId, type]);

  const getFpsForQuality = (q: string, t: 'screen' | 'camera' | 'audio'): number => {
    if (t === 'audio') return 10;
    const qq = String(q || '').toLowerCase();
    if (qq === 'low') return 15;
    if (qq === 'medium') return 20;
    if (qq === 'high') return 25;
    return 30;
  };
  const getPreRollMs = (q: string, t: 'screen' | 'camera' | 'audio'): number => {
    if (t === 'audio') return 0;
    const qq = String(q || '').toLowerCase();
    if (qq === 'low') return 3000;
    if (qq === 'medium') return 5000;
    if (qq === 'high') return 8000;
    return 10000;
  };

  const handleStartStop = async () => {
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
      try {
        await apiClient.stopStream(agentId, type as 'screen' | 'camera' | 'audio');
      } catch {}
      setIsStreaming(false);
      try {
        const key = `stream:last:${agentId}`;
        const raw = localStorage.getItem(key);
        const prev = raw ? JSON.parse(raw) : {};
        localStorage.setItem(key, JSON.stringify({ ...prev, [type]: false }));
      } catch {}
      try { setLastActivity(`stream:${type}`, 'stopped', agentId); } catch {}
      setFrameCount(0);
      setFps(0);
      setBandwidth(0);
      setLastFrameTime(0);
      lastFrameTimeRef.current = 0;
      frameQueueRef.current = [];
      setHasError(false);
      try {
        const a = audioElRef.current;
        if (a) {
          a.pause();
          (a as any).srcObject = null;
        }
      } catch {}
      if (imgRef.current) {
        imgRef.current.src = '';
      }
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
        }
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
        const fps = getFpsForQuality(quality, type as 'screen' | 'camera' | 'audio');
        if (socket && (type === 'screen' || type === 'camera')) {
          socket.emit('set_stream_mode', { agent_id: agentId, type: type, mode: 'realtime', fps, buffer_frames: 10 });
        }
        const res = await apiClient.startStream(
          agentId,
          type as 'screen' | 'camera' | 'audio',
          quality,
          'realtime',
          fps,
          10,
        );
        if (!res?.success) {
          const msg = (res?.error || (res?.data as any)?.error || (res?.data as any)?.message || 'Failed to start stream');
          toast.error(String(msg));
          try {
            const key = `stream:last:${agentId}`;
            const raw = localStorage.getItem(key);
            const prev = raw ? JSON.parse(raw) : {};
            localStorage.setItem(key, JSON.stringify({ ...prev, [type]: false }));
          } catch {}
          return;
        }
        setIsStreaming(true);
        if (socket && type === 'screen') {
          try {
            socket.emit('set_stream_params', { type: 'screen', cursor_emit: agentCursorEmit });
          } catch {}
        }
        preRollMsRef.current = getPreRollMs(quality, type as 'screen' | 'camera' | 'audio');
        preRollStartRef.current = Date.now();
        setPreRollActive(true);
        frameQueueRef.current = [];
      try {
        const key = `stream:last:${agentId}`;
        const raw = localStorage.getItem(key);
        const prev = raw ? JSON.parse(raw) : {};
        localStorage.setItem(key, JSON.stringify({ ...prev, [type]: true }));
      } catch {}
      try { setLastActivity(`stream:${type}`, 'started', agentId); } catch {}
      setHasError(false);
      toast.success(`${type.charAt(0).toUpperCase() + type.slice(1)} stream started`);
    }
  };

  const handleQualityChange = (newQuality: string) => {
    setQuality(newQuality);
    
    if (agentId && isStreaming && socket) {
      socket.emit('set_stream_quality', { agent_id: agentId, quality: newQuality });
    }
    
    toast.info(`Quality set to ${newQuality}`);
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };
  
  const applyCursorEmit = (enabled: boolean) => {
    if (!socket) return;
    try {
      socket.emit('set_stream_params', { type: 'screen', cursor_emit: enabled });
    } catch {}
  };

  const lastMousePosRef = useRef<{ nx: number; ny: number; buttons: number } | null>(null);
  const emitMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!socket || !agentId) return;
    if (!isStreaming || !(type === 'screen' || type === 'camera')) return;
    if (!captureMouse) return;
    const now = Date.now();
    if (now - (lastMouseEmitRef.current || 0) < 30) return;
    lastMouseEmitRef.current = now;
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const nx = Math.max(0, Math.min(1, x / rect.width));
    const ny = Math.max(0, Math.min(1, y / rect.height));
    const last = lastMousePosRef.current;
    if (last) {
      const dx = Math.abs(nx - last.nx);
      const dy = Math.abs(ny - last.ny);
      const changedButtons = (last.buttons || 0) !== (e.buttons || 0);
      if (!changedButtons && dx < 0.003 && dy < 0.003) {
        return;
      }
    }
    lastMousePosRef.current = { nx, ny, buttons: e.buttons || 0 };
    socket.emit('live_mouse_move', {
      agent_id: agentId,
      x: nx,
      y: ny,
      buttons: e.buttons || 0,
      width: Math.round(rect.width),
      height: Math.round(rect.height)
    });
  };

  const emitMouseClick = (action: 'down' | 'up', e: React.MouseEvent<HTMLDivElement>) => {
    if (!socket || !agentId) return;
    if (!isStreaming || !(type === 'screen' || type === 'camera')) return;
    if (!captureMouse) return;
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    const nx = Math.max(0, Math.min(1, x / rect.width));
    const ny = Math.max(0, Math.min(1, y / rect.height));
    const btnIndex = e.button;
    const btnMap: Record<number, string> = { 0: 'left', 1: 'middle', 2: 'right' };
    const btnName = btnMap[btnIndex] || 'left';
    socket.emit('live_mouse_click', {
      agent_id: agentId,
      event_type: action,
      button: btnName,
      x: nx,
      y: ny,
      width: Math.round(rect.width),
      height: Math.round(rect.height)
    });
  };

  const emitKey = (action: 'down' | 'up', e: React.KeyboardEvent<HTMLDivElement>) => {
    if (!socket || !agentId) return;
    if (!isStreaming || !(type === 'screen' || type === 'camera')) return;
    if (!captureKeyboard) return;
    const now = Date.now();
    if (now - (lastKeyEmitRef.current || 0) < 10) return;
    lastKeyEmitRef.current = now;
    socket.emit('live_key_press', {
      agent_id: agentId,
      event_type: action,
      key: e.key,
      code: e.code,
      altKey: e.altKey || modAlt,
      ctrlKey: e.ctrlKey || modCtrl,
      shiftKey: e.shiftKey || modShift,
      metaKey: e.metaKey || modMeta
    });
  };
  
  const sendKey = (key: string, code?: string) => {
    if (!socket || !agentId) return;
    if (!isStreaming || !(type === 'screen' || type === 'camera')) return;
    if (!captureKeyboard) return;
    const payload: any = {
      agent_id: agentId,
      event_type: 'down',
      key,
      code: code || key,
      altKey: modAlt,
      ctrlKey: modCtrl,
      shiftKey: modShift,
      metaKey: modMeta
    };
    socket.emit('live_key_press', payload);
    socket.emit('live_key_press', { ...payload, event_type: 'up' });
  };
  
  const sendText = (text: string) => {
    if (!socket || !agentId) return;
    if (!isStreaming || !(type === 'screen' || type === 'camera')) return;
    if (!captureKeyboard) return;
    for (const ch of text) {
      sendKey(ch);
    }
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
  
  useEffect(() => {
    if (!agentId) return;
    if (!autoResume) return;
    try {
      const raw = localStorage.getItem(`stream:last:${agentId}`);
      const saved = raw ? JSON.parse(raw) : {};
      if (saved && saved[type]) {
        let command = '';
        switch (type) {
          case 'screen': command = 'start-stream'; break;
          case 'camera': command = 'start-camera'; break;
          case 'audio': command = 'start-audio'; break;
        }
        if (command) {
          const fps = getFpsForQuality(quality, type as 'screen' | 'camera' | 'audio');
          if (socket && (type === 'screen' || type === 'camera')) {
            socket.emit('set_stream_mode', { agent_id: agentId, type: type, mode: 'realtime', fps, buffer_frames: 10 });
          }
          sendCommand(agentId, command);
          setIsStreaming(true);
        }
      }
    } catch {}
  }, [agentId]);
  
  useEffect(() => {
    if (!isStreaming || !agentId) return;
    const onCursor = (event: any) => {
      const d = event.detail || {};
      if (String(d.agent_id || '') !== String(agentId || '')) return;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const sw = Number(d.screen_w || 0);
      const sh = Number(d.screen_h || 0);
      if (!sw || !sh) return;
      const x = Math.round((Number(d.x || 0) / sw) * canvas.width);
      const y = Math.round((Number(d.y || 0) / sh) * canvas.height);
      setRemoteCursor({ x, y, visible: Boolean(d.visible !== false) });
    };
    window.addEventListener('cursor_update', onCursor);
    return () => {
      window.removeEventListener('cursor_update', onCursor);
    };
  }, [isStreaming, agentId]);
  
  useEffect(() => {
    if (!isStreaming || !socket || type !== 'screen') return;
    applyCursorEmit(agentCursorEmit);
  }, [agentCursorEmit, isStreaming, socket, type]);

  return (
    <Card className={cn("transition-all", isFullscreen && "fixed inset-4 z-50")}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <StreamIcon className="h-4 w-4" />
            <CardTitle className="text-sm">{title}</CardTitle>
            {agentId && (
              <Badge variant="outline" className="text-xs">
                {(() => {
                  const a = agents.find(x => x.id === agentId);
                  return a ? a.name : agentId;
                })()}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Select value={quality} onValueChange={handleQualityChange}>
              <SelectTrigger className="w-20 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="poor">Poor</SelectItem>
                <SelectItem value="low">Low (30 FPS)</SelectItem>
                <SelectItem value="medium">Med (50 FPS)</SelectItem>
                <SelectItem value="high">High (60 FPS)</SelectItem>
                <SelectItem value="ultra">Ultra (60 FPS)</SelectItem>
              </SelectContent>
            </Select>
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="outline" size="sm" disabled={!isStreaming || !(type === 'screen' || type === 'camera')}>
                  <Keyboard className="h-4 w-4 mr-1" />
                  Controls
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-80" align="end">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs">Keyboard</span>
                    <Button
                      size="sm"
                      variant={captureKeyboard ? "default" : "secondary"}
                      onClick={() => setCaptureKeyboard(v => !v)}
                    >
                      {captureKeyboard ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs">Mouse</span>
                    <Button
                      size="sm"
                      variant={captureMouse ? "default" : "secondary"}
                      onClick={() => setCaptureMouse(v => !v)}
                    >
                      {captureMouse ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs">Remote Cursor Overlay</span>
                    <Button
                      size="sm"
                      variant={showRemoteCursor ? "default" : "secondary"}
                      onClick={() => setShowRemoteCursor(v => !v)}
                    >
                      {showRemoteCursor ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs">Agent Cursor Events</span>
                    <Button
                      size="sm"
                      variant={agentCursorEmit ? "default" : "secondary"}
                      onClick={() => {
                        const v = !agentCursorEmit;
                        setAgentCursorEmit(v);
                        applyCursorEmit(v);
                      }}
                    >
                      {agentCursorEmit ? 'On' : 'Off'}
                    </Button>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <Button size="sm" variant={modCtrl ? "default" : "outline"} onClick={() => setModCtrl(v => !v)}>Ctrl</Button>
                    <Button size="sm" variant={modAlt ? "default" : "outline"} onClick={() => setModAlt(v => !v)}>Alt</Button>
                    <Button size="sm" variant={modShift ? "default" : "outline"} onClick={() => setModShift(v => !v)}>Shift</Button>
                    <Button size="sm" variant={modMeta ? "default" : "outline"} onClick={() => setModMeta(v => !v)}>Meta</Button>
                  </div>
                  <div className="grid grid-cols-4 gap-2">
                    <Button size="sm" variant="outline" onClick={() => sendKey('Escape', 'Escape')}>Esc</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('Tab', 'Tab')}>Tab</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('Enter', 'Enter')}>Enter</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('Backspace', 'Backspace')}>Backspace</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('ArrowUp', 'ArrowUp')}>Up</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('ArrowDown', 'ArrowDown')}>Down</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('ArrowLeft', 'ArrowLeft')}>Left</Button>
                    <Button size="sm" variant="outline" onClick={() => sendKey('ArrowRight', 'ArrowRight')}>Right</Button>
                  </div>
                  <div className="flex items-center space-x-2">
                    <input
                      className="flex-1 h-8 px-2 rounded border border-input bg-background text-sm"
                      placeholder="Type text to send"
                      value={textToSend}
                      onChange={(e) => setTextToSend(e.target.value)}
                    />
                    <Button size="sm" onClick={() => { if (textToSend.trim()) { sendText(textToSend); setTextToSend(''); } }}>Send</Button>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
            {isStreaming && (
              <Badge variant="secondary" className="text-xs">
                Fallback
              </Badge>
            )}
            
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
                if (type === 'audio') {
                  if (audioContextRef.current) {
                    if (!isMuted) {
                      audioContextRef.current.suspend();
                    } else {
                      audioContextRef.current.resume();
                    }
                  }
                } else {
                  const a = audioElRef.current;
                  if (a && (type === 'screen' || type === 'camera')) {
                    if (!isMuted) {
                      a.muted = true;
                    } else {
                      a.muted = false;
                      a.play().catch(() => {});
                    }
                  }
                }
              }}
              disabled={!isStreaming}
            >
              {isMuted ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
            </Button>
            
            {/* Screenshot Button */}
            <Button
              size="sm"
              variant="outline"
              onClick={handleScreenshot}
              disabled={!isStreaming || type === 'audio'}
              title="Capture Screenshot"
            >
              <CameraIcon className="h-3 w-3" />
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
        <div
          ref={containerRef}
          tabIndex={0}
          onMouseMove={emitMouseMove}
          onMouseDown={(e) => emitMouseClick('down', e)}
          onMouseUp={(e) => emitMouseClick('up', e)}
          onKeyDown={(e) => emitKey('down', e)}
          onKeyUp={(e) => emitKey('up', e)}
          className={cn(
            "aspect-video bg-black rounded-lg flex items-center justify-center relative overflow-hidden outline-none",
            isStreaming && (captureMouse || hideCursor) ? "cursor-none" : ""
          )}
        >
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
                <p className="text-sm opacity-80">Agent: {(() => {
                  const a = agents.find(x => x.id === (agentId || ''));
                  return a ? a.name : (agentId || '');
                })()}</p>
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
              <canvas
                ref={canvasRef}
                className="w-full h-full object-contain"
                style={{ display: frameCount > 0 ? 'block' : 'none' }}
              />
              {showRemoteCursor && remoteCursor?.visible && (
                <div
                  className="absolute"
                  style={{
                    left: `${remoteCursor.x}px`,
                    top: `${remoteCursor.y}px`,
                    width: '12px',
                    height: '12px',
                    borderRadius: '50%',
                    backgroundColor: '#ffffff',
                    border: '1px solid #000000',
                    transform: 'translate(-50%, -50%)',
                    pointerEvents: 'none'
                  }}
                />
              )}
              {isStreaming && preRollActive && (
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="bg-black/60 text-white px-3 py-1 rounded text-xs">
                    Capturing frames…
                  </div>
                </div>
              )}
              <audio ref={audioElRef} style={{ display: 'none' }} />
              {frameCount === 0 && (
                <div className="text-center text-muted-foreground">
                  <StreamIcon className="h-12 w-12 mx-auto mb-2 animate-pulse" />
                  <p className="text-sm">Waiting for frames...</p>
                  <p className="text-xs mt-1">Connecting to agent</p>
                </div>
              )}
            </>
          )}
          
          {isStreaming && (frameCount > 0 && !hasError) && (
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
        
        {isStreaming && (frameCount > 0 && !hasError) && (
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
