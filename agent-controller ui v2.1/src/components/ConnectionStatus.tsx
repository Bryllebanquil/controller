import { useState, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { 
  Wifi, 
  WifiOff, 
  Signal, 
  SignalHigh, 
  SignalLow, 
  SignalMedium,
  Globe,
  Server
} from 'lucide-react';
import { cn } from './ui/utils';
import { useSocket } from './SocketProvider';

interface ConnectionData {
  status: 'excellent' | 'good' | 'poor' | 'offline';
  latency: number;
  bandwidth: number;
  uptime: number;
  packetsLost: number;
  lastUpdate: Date;
}

export function ConnectionStatus() {
  const { connected } = useSocket();
  const [connection, setConnection] = useState<ConnectionData>({
    status: 'offline',
    latency: 0,
    bandwidth: 0,
    uptime: 0,
    packetsLost: 0,
    lastUpdate: new Date()
  });

  useEffect(() => {
    setConnection(prev => ({
      ...prev,
      status: connected ? 'excellent' : 'offline',
      lastUpdate: new Date()
    }));
  }, [connected]);

  const getSignalIcon = () => {
    switch (connection.status) {
      case 'excellent': return SignalHigh;
      case 'good': return SignalMedium;
      case 'poor': return SignalLow;
      case 'offline': return WifiOff;
      default: return Signal;
    }
  };

  const getStatusColor = () => {
    switch (connection.status) {
      case 'excellent': return 'text-green-500';
      case 'good': return 'text-yellow-500';
      case 'poor': return 'text-orange-500';
      case 'offline': return 'text-red-500';
      default: return 'text-muted-foreground';
    }
  };

  const SignalIcon = getSignalIcon();

  return (
    <Card className="p-2 sm:p-3 min-w-0 max-w-sm">
      <CardContent className="p-0">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-3">
          <div className="flex items-center space-x-2 sm:space-x-3 min-w-0">
            <div className={cn("p-1 rounded-full flex-shrink-0", getStatusColor())}>
              <SignalIcon className="h-3 w-3 sm:h-4 sm:w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center space-x-1 sm:space-x-2">
                <span className="text-xs sm:text-sm font-medium truncate">Network Status</span>
                <Badge 
                  variant={connection.status === 'excellent' ? 'default' : 
                          connection.status === 'good' ? 'secondary' : 'destructive'}
                  className="text-xs capitalize flex-shrink-0"
                >
                  {connection.status}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground truncate">
                Last updated: {connection.lastUpdate.toLocaleTimeString()}
              </div>
            </div>
          </div>

          <div className="w-full sm:w-auto flex-shrink-0">
            <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
              <div className="flex items-center space-x-1">
                <Globe className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                <span className="truncate">{connection.latency}ms</span>
              </div>
              <div className="flex items-center space-x-1">
                <Server className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                <span className="truncate">{connection.bandwidth} MB/s</span>
              </div>
              <div className="text-muted-foreground truncate">
                Uptime: {connection.uptime}%
              </div>
              <div className="text-muted-foreground truncate">
                Loss: {connection.packetsLost}%
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}