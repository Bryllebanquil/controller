import React from 'react';
import { useState, useEffect, useRef } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";
import { ScrollArea } from "./ui/scroll-area";
import { Progress } from "./ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  Square,
  Settings,
  Trash2,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Clock,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { useSocket } from "./SocketProvider";

interface VoiceCommand {
  id: string;
  command: string;
  timestamp: Date;
  status: "pending" | "executing" | "completed" | "failed";
  response?: string;
  audioLevel?: number;
  confidence?: number;
}

interface VoiceControlProps {
  agentId: string | null;
  isConnected: boolean;
}

export function VoiceControl({ agentId, isConnected }: VoiceControlProps) {
  const { socket } = useSocket();
  const [isListening, setIsListening] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [voiceCommands, setVoiceCommands] = useState([] as VoiceCommand[]);
  const [recognition, setRecognition] = useState(null as SpeechRecognition | null);
  const [audioContext, setAudioContext] = useState(null as AudioContext | null);
  const [mediaRecorder, setMediaRecorder] = useState(null as MediaRecorder | null);
  const [recordedChunks, setRecordedChunks] = useState([] as Blob[]);
  const [voiceSettings, setVoiceSettings] = useState({
    language: "en-US",
    continuous: true,
    interimResults: true,
    maxAlternatives: 1,
    threshold: 0.7,
  });
  const [selectedMode, setSelectedMode] = useState("speech" as "speech" | "audio");
  
  const audioLevelRef = useRef(0 as number);
  const animationRef = useRef(undefined as number | undefined);

  // Predefined voice commands for the agent
  const predefinedCommands = [
    { command: "take screenshot", description: "Capture current screen" },
    { command: "start camera", description: "Begin camera streaming" },
    { command: "stop camera", description: "End camera streaming" },
    { command: "start streaming", description: "Begin screen streaming" },
    { command: "stop streaming", description: "End screen streaming" },
    { command: "system info", description: "Get system information" },
    { command: "list processes", description: "Show running processes" },
    { command: "current directory", description: "Show current location" },
    { command: "network status", description: "Check network connectivity" },
    { command: "disk space", description: "Check available storage" },
  ];

  // Initialize speech recognition
  useEffect(() => {
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = voiceSettings.continuous;
      recognition.interimResults = voiceSettings.interimResults;
      recognition.lang = voiceSettings.language;
      recognition.maxAlternatives = voiceSettings.maxAlternatives;

      recognition.onstart = () => {
        setIsListening(true);
        toast.success("Voice recognition started");
      };

      recognition.onend = () => {
        setIsListening(false);
        if (audioContext) {
          audioContext.close();
          setAudioContext(null);
        }
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        toast.error(`Voice recognition error: ${event.error}`);
        setIsListening(false);
      };

      recognition.onresult = (event) => {
        const results = Array.from(event.results);
        const lastResult = results[results.length - 1];
        
        if (lastResult.isFinal) {
          const transcript = lastResult[0].transcript.trim();
          const confidence = lastResult[0].confidence;
          
          if (confidence >= voiceSettings.threshold) {
            executeVoiceCommand(transcript, confidence);
          } else {
            toast.warning(`Voice command unclear (${Math.round(confidence * 100)}% confidence)`);
          }
        }
      };

      setRecognition(recognition);
    } else {
      toast.error("Speech recognition not supported in this browser");
    }

    return () => {
      if (recognition) {
        recognition.stop();
      }
    };
  }, [voiceSettings]);

  // Initialize audio context for level monitoring
  const initializeAudioContext = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      const microphone = context.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      microphone.connect(analyser);
      
      const dataArray = new Uint8Array(analyser.frequencyBinCount);
      
      const updateAudioLevel = () => {
        if (isListening) {
          analyser.getByteFrequencyData(dataArray);
          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          const level = (average / 255) * 100;
          audioLevelRef.current = level;
          setAudioLevel(level);
          animationRef.current = requestAnimationFrame(updateAudioLevel);
        }
      };
      
      setAudioContext(context);
      updateAudioLevel();
    } catch (error) {
      console.error("Failed to initialize audio context:", error);
      toast.error("Failed to access microphone");
    }
  };

  // Start/stop voice recognition
  const toggleVoiceRecognition = async () => {
    if (!recognition) {
      toast.error("Speech recognition not available");
      return;
    }

    if (!agentId) {
      toast.error("Please select an agent first");
      return;
    }

    if (isListening) {
      recognition.stop();
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    } else {
      await initializeAudioContext();
      recognition.start();
    }
  };

  // Start/stop audio recording for live audio transmission
  const toggleAudioRecording = async () => {
    if (!agentId) {
      toast.error("Please select an agent first");
      return;
    }

    if (isRecording) {
      if (mediaRecorder) {
        mediaRecorder.stop();
      }
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            sampleRate: 44100,
          }
        });
        
        const recorder = new MediaRecorder(stream, {
          mimeType: "audio/webm;codecs=opus",
        });
        
        const chunks: Blob[] = [];
        
        recorder.ondataavailable = (event) => {
          if (event.data.size > 0) {
            chunks.push(event.data);
          }
        };
        
        recorder.onstop = () => {
          const audioBlob = new Blob(chunks, { type: "audio/webm" });
          sendLiveAudio(audioBlob);
          setRecordedChunks([]);
          setIsRecording(false);
        };
        
        recorder.start(1000); // Capture data every second
        setMediaRecorder(recorder);
        setIsRecording(true);
        toast.success("Audio recording started");
      } catch (error) {
        console.error("Failed to start recording:", error);
        toast.error("Failed to start audio recording");
      }
    }
  };

  // Execute voice command
  const executeVoiceCommand = (command: string, confidence: number) => {
    const commandId = Date.now().toString();
    const newCommand: VoiceCommand = {
      id: commandId,
      command,
      timestamp: new Date(),
      status: "pending",
      confidence,
      audioLevel: audioLevelRef.current,
    };

    setVoiceCommands(prev => [newCommand, ...prev.slice(0, 49)]); // Keep last 50 commands

    // Send to agent
    if (agentId && socket) {
      socket.emit('execute_command', { agent_id: agentId, command });
      setVoiceCommands(prev => prev.map(cmd => cmd.id === commandId ? { ...cmd, status: 'executing' } : cmd));
      toast.success(`Voice command: "${command}" sent`);
    }
  };

  // Send live audio to agent
  const sendLiveAudio = async (audioBlob: Blob) => {
    if (!agentId) return;

    try {
      const reader = new FileReader();
      reader.onload = () => {
        const base64Audio = reader.result as string;
        if (socket && agentId) {
          socket.emit('audio_frame', { agent_id: agentId, frame: base64Audio });
          toast.success("Live audio sent to agent");
        }
      };
      reader.readAsDataURL(audioBlob);
    } catch (error) {
      console.error("Failed to send audio:", error);
      toast.error("Failed to send audio to agent");
    }
  };

  // Execute predefined command
  const executePredefinedCommand = (command: string) => {
    executeVoiceCommand(command, 1.0);
  };

  // Clear command history
  const clearHistory = () => {
    setVoiceCommands([]);
    toast.success("Command history cleared");
  };

  // Get status icon for command
  const getStatusIcon = (status: VoiceCommand["status"]) => {
    switch (status) {
      case "pending":
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case "executing":
        return <Zap className="h-4 w-4 text-blue-500 animate-pulse" />;
      case "completed":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "failed":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Voice Control Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mic className="h-5 w-5" />
            Voice Control Panel
          </CardTitle>
          <CardDescription>
            Control agents using speech recognition and live audio streaming
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Mode Selection */}
          <div className="flex items-center gap-4">
            <Select value={selectedMode} onValueChange={(value: "speech" | "audio") => setSelectedMode(value)}>
              <SelectTrigger className="w-48">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="speech">Speech Recognition</SelectItem>
                <SelectItem value="audio">Live Audio Stream</SelectItem>
              </SelectContent>
            </Select>
            
            <Badge variant={isConnected ? "default" : "secondary"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
            
            {agentId && (
              <Badge variant="outline">
                Agent: {agentId.slice(0, 8)}
              </Badge>
            )}
          </div>

          {/* Control Buttons */}
          <div className="flex items-center gap-4">
            {selectedMode === "speech" ? (
              React.createElement(Button, {
                onClick: toggleVoiceRecognition,
                variant: isListening ? "destructive" : "default",
                disabled: !agentId || !isConnected,
                className: "flex items-center gap-2"
              },
                isListening ? React.createElement(MicOff, { className: "h-4 w-4" }) : React.createElement(Mic, { className: "h-4 w-4" }),
                isListening ? "Stop Listening" : "Start Listening"
              )
            ) : (
              React.createElement(Button, {
                onClick: toggleAudioRecording,
                variant: isRecording ? "destructive" : "default",
                disabled: !agentId || !isConnected,
                className: "flex items-center gap-2"
              },
                isRecording ? React.createElement(Square, { className: "h-4 w-4" }) : React.createElement(Play, { className: "h-4 w-4" }),
                isRecording ? "Stop Recording" : "Start Recording"
              )
            )}

            {React.createElement(Button, {
              onClick: clearHistory,
              variant: "outline",
              size: "sm",
              className: "flex items-center gap-2"
            },
              React.createElement(Trash2, { className: "h-4 w-4" }),
              "Clear History"
            )}
          </div>

          {/* Audio Level Indicator */}
          {(isListening || isRecording) && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Audio Level</span>
                <span className="text-sm font-mono">{Math.round(audioLevel)}%</span>
              </div>
              <Progress value={audioLevel} className="h-2" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Quick Commands */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Voice Commands</CardTitle>
          <CardDescription>
            Click to execute common commands or use voice recognition
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {predefinedCommands.map((cmd, index) => (
              React.createElement(Button, {
                key: index,
                variant: "outline",
                onClick: () => executePredefinedCommand(cmd.command),
                disabled: !agentId || !isConnected,
                className: "justify-start h-auto p-3"
              },
                React.createElement("div", { className: "text-left" },
                  React.createElement("div", { className: "font-medium" }, cmd.command),
                  React.createElement("div", { className: "text-xs text-muted-foreground" }, cmd.description)
                )
              )
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Command History */}
      <Card>
        <CardHeader>
          <CardTitle>Command History</CardTitle>
          <CardDescription>
            Recent voice commands and their execution status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            {voiceCommands.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No voice commands yet. Start by clicking "Start Listening" or use Quick Commands above.
              </div>
            ) : (
              <div className="space-y-3">
                {voiceCommands.map((command) => (
                  <div
                    key={command.id}
                    className="flex items-start gap-3 p-3 rounded-lg border"
                  >
                    <div className="flex-shrink-0 mt-1">
                      {getStatusIcon(command.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="font-medium truncate">{command.command}</p>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          {command.confidence && (
                            <Badge variant="secondary" className="text-xs">
                              {Math.round(command.confidence * 100)}%
                            </Badge>
                          )}
                          <span>{command.timestamp.toLocaleTimeString()}</span>
                        </div>
                      </div>
                      {command.response && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {command.response}
                        </p>
                      )}
                      {command.audioLevel !== undefined && (
                        <div className="flex items-center gap-2 mt-2">
                          <Volume2 className="h-3 w-3" />
                          <Progress value={command.audioLevel} className="h-1 flex-1" />
                          <span className="text-xs text-muted-foreground">
                            {Math.round(command.audioLevel)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Voice Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Voice Recognition Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Language</label>
              <Select
                value={voiceSettings.language}
                onValueChange={(value) => setVoiceSettings(prev => ({ ...prev, language: value }))}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en-US">English (US)</SelectItem>
                  <SelectItem value="en-GB">English (UK)</SelectItem>
                  <SelectItem value="es-ES">Spanish</SelectItem>
                  <SelectItem value="fr-FR">French</SelectItem>
                  <SelectItem value="de-DE">German</SelectItem>
                  <SelectItem value="ja-JP">Japanese</SelectItem>
                  <SelectItem value="zh-CN">Chinese</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Confidence Threshold</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={voiceSettings.threshold}
                  onChange={(e) => setVoiceSettings(prev => ({ 
                    ...prev, 
                    threshold: parseFloat(e.target.value) 
                  }))}
                  className="flex-1"
                />
                <span className="text-sm font-mono w-12">
                  {Math.round(voiceSettings.threshold * 100)}%
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}