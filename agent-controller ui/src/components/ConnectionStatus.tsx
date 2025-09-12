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

interface ConnectionData {
  status: 'excellent' | 'good' | 'poor' | 'offline';
  latency: number;
  bandwidth: number;
  uptime: number;
  packetsLost: number;
  lastUpdate: Date;
}

export function ConnectionStatus() {
  const [connection, setConnection] = useState<ConnectionData>({
    status: 'excellent',
    latency: 12,
    bandwidth: 2.4,
    uptime: 99.8,
    packetsLost: 0.1,
    lastUpdate: new Date()
  });

  // Simulate connection fluctuations
  useEffect(() => {
    const interval = setInterval(() => {
      setConnection(prev => {
        const newLatency = Math.max(5, prev.latency + (Math.random() - 0.5) * 10);
        const newBandwidth = Math.max(0.5, prev.bandwidth + (Math.random() - 0.5) * 0.5);
        const newPacketsLost = Math.max(0, prev.packetsLost + (Math.random() - 0.5) * 0.2);
        
        let newStatus: ConnectionData['status'] = 'excellent';
        if (newLatency > 50 || newPacketsLost > 2) {
          newStatus = 'poor';
        } else if (newLatency > 25 || newPacketsLost > 1) {
          newStatus = 'good';
        }

        return {
          ...prev,
          status: newStatus,
          latency: Math.round(newLatency),
          bandwidth: Math.round(newBandwidth * 10) / 10,
          packetsLost: Math.round(newPacketsLost * 10) / 10,
          lastUpdate: new Date()
        };
      });
    }, 3000);

    return () => clearInterval(interval);
  }, []);

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
    <Card className="p-3">
      <CardContent className="p-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={cn("p-1 rounded-full", getStatusColor())}>
              <SignalIcon className="h-4 w-4" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-sm font-medium">Network Status</span>
                <Badge 
                  variant={connection.status === 'excellent' ? 'default' : 
                          connection.status === 'good' ? 'secondary' : 'destructive'}
                  className="text-xs capitalize"
                >
                  {connection.status}
                </Badge>
              </div>
              <div className="text-xs text-muted-foreground">
                Last updated: {connection.lastUpdate.toLocaleTimeString()}
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <div className="flex items-center space-x-1">
                <Globe className="h-3 w-3 text-muted-foreground" />
                <span>{connection.latency}ms</span>
              </div>
              <div className="flex items-center space-x-1">
                <Server className="h-3 w-3 text-muted-foreground" />
                <span>{connection.bandwidth} MB/s</span>
              </div>
              <div className="text-muted-foreground">
                Uptime: {connection.uptime}%
              </div>
              <div className="text-muted-foreground">
                Loss: {connection.packetsLost}%
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}