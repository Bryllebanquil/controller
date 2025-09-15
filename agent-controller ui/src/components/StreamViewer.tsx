import { useState } from 'react';
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
  Mic
} from 'lucide-react';
import { cn } from './ui/utils';

interface StreamViewerProps {
  agentId: string | null;
  type: 'screen' | 'camera' | 'audio';
  title: string;
}

export function StreamViewer({ agentId, type, title }: StreamViewerProps) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [quality, setQuality] = useState('high');
  const [isFullscreen, setIsFullscreen] = useState(false);

  const getStreamIcon = () => {
    switch (type) {
      case 'screen': return Monitor;
      case 'camera': return Camera;
      case 'audio': return Mic;
      default: return Monitor;
    }
  };

  const StreamIcon = getStreamIcon();

  const handleStartStop = () => {
    setIsStreaming(!isStreaming);
  };

  const handleQualityChange = (newQuality: string) => {
    setQuality(newQuality);
  };

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
            
            <Button variant="ghost" size="sm" onClick={() => setIsFullscreen(!isFullscreen)}>
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
            
            {type !== 'audio' && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => setIsMuted(!isMuted)}
                disabled={!isStreaming}
              >
                {isMuted ? <VolumeX className="h-3 w-3" /> : <Volume2 className="h-3 w-3" />}
              </Button>
            )}
          </div>
          
          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
            {isStreaming && (
              <>
                <Badge variant="secondary">30 FPS</Badge>
                <Badge variant="secondary">2.1 MB/s</Badge>
                <Badge variant="secondary">12ms</Badge>
              </>
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
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
              <div className="text-white text-center">
                <StreamIcon className="h-16 w-16 mx-auto mb-4 animate-pulse" />
                <p className="text-lg font-medium">Live Stream</p>
                <p className="text-sm opacity-80">Agent: {agentId.substring(0, 8)}</p>
                <div className="mt-4 flex justify-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          
          {isStreaming && (
            <div className="absolute top-2 left-2 flex items-center space-x-2">
              <div className="flex items-center space-x-1 bg-black/70 text-white px-2 py-1 rounded text-xs">
                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                <span>LIVE</span>
              </div>
              <div className="bg-black/70 text-white px-2 py-1 rounded text-xs">
                {quality.toUpperCase()}
              </div>
            </div>
          )}
        </div>
        
        {isStreaming && (
          <div className="mt-4 text-xs text-muted-foreground">
            <div className="flex justify-between items-center">
              <span>Connection Quality: Excellent</span>
              <span>Latency: 12ms</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}