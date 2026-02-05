import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSocket } from './SocketProvider';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Camera, Download, RefreshCw, Image as ImageIcon, AlertCircle, TestTube } from 'lucide-react';
import { toast } from 'sonner';
import { Progress } from './ui/progress';
import { ScreenshotTest } from './ScreenshotTest';

interface ScreenshotTabProps {
  agentId: string | null;
}

export function ScreenshotTab({ agentId }: ScreenshotTabProps) {
  const { sendCommand, socket } = useSocket();
  const [screenshot, setScreenshot] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastCaptured, setLastCaptured] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const [progress, setProgress] = useState(0);
  const [accuracy, setAccuracy] = useState<number | null>(null);
  const [accuracyHistory, setAccuracyHistory] = useState<{ timestamp: string; accuracy: number; durationMs: number; size: number; success: boolean; attempts: number; error?: string }[]>([]);
  const [operationLogs, setOperationLogs] = useState<{ timestamp: string; type: string; accuracy?: number; durationMs?: number; size?: number; message?: string }[]>([]);
  const maxRetries = 3;
  const screenshotTimeout = 20000; // 20-second timeout
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);
  const isLoadingRef = useRef(false);
  const captureStartRef = useRef<number | null>(null);
  const expectedDurationRef = useRef<number>(screenshotTimeout);
  const durationSamplesRef = useRef<number[]>([]);
  const sizeSamplesRef = useRef<number[]>([]);
  const minSizeRef = useRef<number>(100);
  const isDev = Boolean((import.meta as any)?.env?.DEV);
  const debugEnabled = isDev && (typeof window !== 'undefined') && localStorage.getItem('screenshot_debug') === 'true';

  const appendLog = useCallback((entry: { timestamp: string; type: string; accuracy?: number; durationMs?: number; size?: number; message?: string }) => {
    setOperationLogs(prev => [...prev.slice(-49), entry]);
  }, []);

  const updateExpectedDuration = useCallback((durationMs: number) => {
    durationSamplesRef.current = [...durationSamplesRef.current.slice(-4), durationMs];
    const avg = durationSamplesRef.current.reduce((sum, value) => sum + value, 0) / durationSamplesRef.current.length;
    expectedDurationRef.current = Math.min(Math.max(avg, 1000), screenshotTimeout);
  }, [screenshotTimeout]);

  const updateSizeBaseline = useCallback((size: number) => {
    sizeSamplesRef.current = [...sizeSamplesRef.current.slice(-4), size];
    const avg = sizeSamplesRef.current.reduce((sum, value) => sum + value, 0) / sizeSamplesRef.current.length;
    minSizeRef.current = Math.max(100, Math.round(avg * 0.2));
  }, []);

  const computeAccuracy = useCallback((params: { success: boolean; durationMs: number; size: number; attempts: number; error?: string }) => {
    const { success, durationMs, size, attempts, error } = params;
    let score = 100;
    if (!success) score -= 40;
    if (durationMs > expectedDurationRef.current) {
      const over = durationMs - expectedDurationRef.current;
      const ratio = Math.min(1, over / expectedDurationRef.current);
      score -= Math.round(20 * ratio);
    } else if (durationMs > expectedDurationRef.current * 0.75) {
      score -= 6;
    }
    if (size < minSizeRef.current) {
      score -= 25;
    } else if (size < minSizeRef.current * 2) {
      score -= 10;
    }
    if (attempts > 1) {
      score -= Math.min(15, (attempts - 1) * 5);
    }
    if (error) {
      score -= Math.min(10, Math.ceil(error.length / 50) * 5);
    }
    return Math.max(0, Math.min(100, score));
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    isLoadingRef.current = isLoading;
  }, [isLoading]);

  useEffect(() => {
    if (!isLoading) {
      setProgress(0);
      return;
    }

    const interval = setInterval(() => {
      setProgress(prev => {
        const start = captureStartRef.current ?? Date.now();
        const elapsed = Date.now() - start;
        const expected = Math.max(screenshotTimeout, 1000);
        const ratio = Math.min(0.99, elapsed / expected);
        const nextProgress = Math.max(prev, Math.round(ratio * 100));
        const liveAccuracy = Math.max(0, Math.min(100, 100 - Math.round(ratio * 30)));
        setAccuracy(liveAccuracy);
        return nextProgress;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isLoading]);

  useEffect(() => {
    if (!socket) return;

    const handleScreenshotResponse = (data: any) => {
      if (data.agent_id === agentId) {
        if (debugEnabled) {
          debugger;
        }
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }
        
        if (isMountedRef.current) {
          const durationMs = typeof data.duration_ms === 'number' ? data.duration_ms : (captureStartRef.current ? Date.now() - captureStartRef.current : 0);
          const size = typeof data.image === 'string' ? data.image.length : (typeof data.image_size === 'number' ? data.image_size : 0);
          const attempts = typeof data.attempts === 'number' ? data.attempts : 1;
          if (data.success && data.image) {
            if (size < minSizeRef.current) {
              setIsLoading(false);
              setProgress(0);
              setError('Screenshot data too small, capture may have failed');
              const derivedAccuracy = computeAccuracy({ success: false, durationMs, size, attempts, error: 'Screenshot data too small' });
              setAccuracy(derivedAccuracy);
              setAccuracyHistory(prev => [...prev.slice(-49), { timestamp: new Date().toISOString(), accuracy: derivedAccuracy, durationMs, size, success: false, attempts, error: 'Screenshot data too small' }]);
              appendLog({ timestamp: new Date().toISOString(), type: 'error', accuracy: derivedAccuracy, durationMs, size, message: 'Screenshot data too small' });
              toast.error('Screenshot data invalid');
              return;
            }
            
            setScreenshot(`data:image/png;base64,${data.image}`);
            setLastCaptured(new Date());
            setIsLoading(false);
            setError(null);
            setRetryCount(0);
            setProgress(100); // Complete progress
            updateExpectedDuration(durationMs);
            updateSizeBaseline(size);
            const accuracyScore = typeof data.accuracy === 'number' ? data.accuracy : computeAccuracy({ success: true, durationMs, size, attempts });
            setAccuracy(accuracyScore);
            setAccuracyHistory(prev => [...prev.slice(-49), { timestamp: new Date().toISOString(), accuracy: accuracyScore, durationMs, size, success: true, attempts }]);
            appendLog({ timestamp: new Date().toISOString(), type: 'success', accuracy: accuracyScore, durationMs, size, message: 'Screenshot captured' });
            toast.success('Screenshot captured successfully');
          } else {
            setIsLoading(false);
            setProgress(0);
            const errorMsg = data.error || 'Unknown error';
            setError(errorMsg);
            const derivedAccuracy = typeof data.accuracy === 'number' ? data.accuracy : computeAccuracy({ success: false, durationMs, size, attempts, error: errorMsg });
            setAccuracy(derivedAccuracy);
            setAccuracyHistory(prev => [...prev.slice(-49), { timestamp: new Date().toISOString(), accuracy: derivedAccuracy, durationMs, size, success: false, attempts, error: errorMsg }]);
            appendLog({ timestamp: new Date().toISOString(), type: 'error', accuracy: derivedAccuracy, durationMs, size, message: errorMsg });
            toast.error(`Screenshot capture failed: ${errorMsg}`);
          }
        }
      }
    };

    socket.on('screenshot_response', handleScreenshotResponse);

    return () => {
      socket.off('screenshot_response', handleScreenshotResponse);
    };
  }, [socket, agentId]);

  const handleCapture = useCallback(async () => {
    if (!agentId || !socket) {
      toast.error('No agent selected or socket not connected');
      return;
    }

    setError(null);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    captureStartRef.current = Date.now();
    setIsLoading(true);
    setAccuracy(100);
    appendLog({ timestamp: new Date().toISOString(), type: 'start', message: 'Screenshot capture started' });
    if (debugEnabled) {
      debugger;
    }
    
    try {
      socket.emit('get_screenshot', { agent_id: agentId });
      
      timeoutRef.current = setTimeout(() => {
        if (isMountedRef.current && isLoadingRef.current) {
          setIsLoading(false);
          setProgress(100);
          setError('Screenshot request timed out, please retry');
          const durationMs = captureStartRef.current ? Date.now() - captureStartRef.current : screenshotTimeout;
          const derivedAccuracy = computeAccuracy({ success: false, durationMs, size: 0, attempts: retryCount + 1, error: 'Timeout' });
          setAccuracy(derivedAccuracy);
          setAccuracyHistory(prev => [...prev.slice(-49), { timestamp: new Date().toISOString(), accuracy: derivedAccuracy, durationMs, size: 0, success: false, attempts: retryCount + 1, error: 'Timeout' }]);
          appendLog({ timestamp: new Date().toISOString(), type: 'timeout', accuracy: derivedAccuracy, durationMs, message: 'Screenshot request timed out' });
          if (debugEnabled) {
            debugger;
          }
          toast.error('Screenshot request timed out, please retry');
        }
      }, screenshotTimeout);
      
    } catch (err) {
       if (isMountedRef.current) {
          setIsLoading(false);
          setProgress(0);
          const errorMsg = err instanceof Error ? err.message : 'Failed to send screenshot request';
          setError(errorMsg);
          const durationMs = captureStartRef.current ? Date.now() - captureStartRef.current : 0;
          const derivedAccuracy = computeAccuracy({ success: false, durationMs, size: 0, attempts: retryCount + 1, error: errorMsg });
          setAccuracy(derivedAccuracy);
          setAccuracyHistory(prev => [...prev.slice(-49), { timestamp: new Date().toISOString(), accuracy: derivedAccuracy, durationMs, size: 0, success: false, attempts: retryCount + 1, error: errorMsg }]);
          appendLog({ timestamp: new Date().toISOString(), type: 'error', accuracy: derivedAccuracy, durationMs, message: errorMsg });
          if (debugEnabled) {
            debugger;
          }
          toast.error(`Screenshot request failed: ${errorMsg}`);
        }
     }
   }, [agentId, socket, isLoading, screenshotTimeout, retryCount, computeAccuracy, appendLog, debugEnabled, updateExpectedDuration, updateSizeBaseline]);

  const handleRetry = useCallback(() => {
    setError(null);
    setRetryCount(prev => prev + 1);
    appendLog({ timestamp: new Date().toISOString(), type: 'retry', message: 'Retry requested' });
    handleCapture();
  }, [handleCapture, appendLog]);

  const handleDownload = useCallback(() => {
    if (!screenshot) return;
    
    try {
      const a = document.createElement('a');
      a.href = screenshot;
      a.download = `screenshot-${agentId}-${new Date().getTime()}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      appendLog({ timestamp: new Date().toISOString(), type: 'download', message: 'Screenshot downloaded' });
      toast.success('Screenshot downloaded');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Download failed';
      appendLog({ timestamp: new Date().toISOString(), type: 'error', message: errorMsg });
      toast.error('Screenshot download failed');
      console.error('Screenshot download error:', err);
    }
  }, [screenshot, agentId, appendLog]);

  if (!agentId) {
    return (
      <Card className="h-[400px]">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            <Camera className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Select an agent to capture screenshots</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  const averageAccuracy = useMemo(() => {
    if (!accuracyHistory.length) return null;
    const sum = accuracyHistory.reduce((total, entry) => total + entry.accuracy, 0);
    return Math.round((sum / accuracyHistory.length) * 10) / 10;
  }, [accuracyHistory]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Remote Screen Capture</h3>
          <p className="text-sm text-muted-foreground">
              Capture high-quality single frame images from agent screen
            </p>
        </div>
        <div className="flex space-x-2">
          <Button 
            onClick={handleCapture} 
            disabled={isLoading}
            className={error ? "border-destructive" : ""}
          >
            {isLoading ? (
              <>
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                Capturing...
              </>
            ) : (
              <>
                <Camera className="h-4 w-4 mr-2" />
                Capture Screen
              </>
            )}
          </Button>
          
          {screenshot && (
            <Button variant="outline" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
          )}
        </div>
      </div>

      {isLoading && (
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span>Capturing screen...</span>
            <span>{Math.round(progress)}%</span>
          </div>
          <Progress value={progress} className="h-2" />
          <p className="text-xs text-muted-foreground">
            {progress < 30 && "Connecting to agent..."}
            {progress >= 30 && progress < 70 && "Capturing screen..."}
            {progress >= 70 && progress < 90 && "Processing image..."}
            {progress >= 90 && "Waiting for response..."}
          </p>
          {accuracy !== null && (
            <div className="text-xs text-muted-foreground flex items-center justify-between">
              <span>Accuracy</span>
              <span>{Math.round(accuracy)}%</span>
            </div>
          )}
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-destructive">Capture Failed</p>
                  <p className="text-xs text-muted-foreground">{error}</p>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleRetry}
                  disabled={isLoading || retryCount >= maxRetries}
                >
                  {retryCount >= maxRetries ? "Retry limit reached" : `Retry (${retryCount}/${maxRetries})`}
                </Button>
              </div>
          </CardContent>
        </Card>
      )}

      <Card className="overflow-hidden">
        <CardContent className="p-0 min-h-[400px] flex items-center justify-center bg-black/5 relative">
          {screenshot ? (
            <div className="relative w-full h-full flex flex-col">
               <img 
                 src={screenshot} 
                 alt="Remote screen" 
                 className="w-full h-auto object-contain max-h-[70vh]" 
                 onError={() => {
                   toast.error('Screenshot image failed to load');
                   setScreenshot(null);
                   setError('Screenshot image format error or corrupted');
                   appendLog({ timestamp: new Date().toISOString(), type: 'error', message: 'Screenshot image failed to load' });
                   if (debugEnabled) {
                     debugger;
                   }
                 }}
               />
               <div className="absolute bottom-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded backdrop-blur-sm">
                 Captured: {lastCaptured?.toLocaleTimeString()}
               </div>
            </div>
          ) : (
            <div className="text-center text-muted-foreground p-10">
              <ImageIcon className="h-16 w-16 mx-auto mb-4 opacity-20" />
              <p>No screenshot captured yet</p>
              <p className="text-xs mt-2">Click "Capture Screen" to get current display</p>
            </div>
          )}
        </CardContent>
      </Card>
      
      <div className="text-xs text-muted-foreground space-y-1">
        <p>• Screen capture uses main monitor. If screen is locked or asleep, capture may be black or fail.</p>
        <p>• Screenshot will timeout after {Math.round(screenshotTimeout/1000)} seconds, can retry up to {maxRetries} times.</p>
        {averageAccuracy !== null && <p>• Average accuracy: {averageAccuracy}%</p>}
        {isLoading && <p className="text-yellow-600">• Waiting for agent response, please wait...</p>}
      </div>

      <ScreenshotTest agentId={agentId} />
    </div>
  );
}
