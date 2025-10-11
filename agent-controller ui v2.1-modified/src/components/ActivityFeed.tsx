import React from 'react';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';
import { 
  Activity,
  Monitor,
  Terminal,
  Files,
  Wifi,
  WifiOff,
  Shield,
  Camera,
  Mic,
  RefreshCw,
  Play,
  Square,
  Download,
  Upload,
  Clock
} from 'lucide-react';
import { cn } from './ui/utils';
import { useSocket } from './SocketProvider';

interface ActivityEvent {
  id: string;
  type: 'connection' | 'command' | 'stream' | 'file' | 'security' | 'system';
  action: string;
  details: string;
  agentId: string;
  agentName: string;
  timestamp: Date;
  status: 'success' | 'warning' | 'error' | 'info';
}

const activityIcons = {
  connection: Wifi,
  command: Terminal,
  stream: Monitor,
  file: Files,
  security: Shield,
  system: Activity
};

const statusColors = {
  success: 'text-green-600',
  warning: 'text-yellow-600', 
  error: 'text-red-600',
  info: 'text-blue-600'
};

const mockActivities: ActivityEvent[] = [];

export function ActivityFeed() {
  const [activities, setActivities] = useState(mockActivities as ActivityEvent[]);
  const [filter, setFilter] = useState('all' as 'all' | ActivityEvent['type']);
  const [isLive, setIsLive] = useState(true);
  const { socket } = useSocket();

  // Wire real-time activities
  useEffect(() => {
    if (!socket || !isLive) return;
    const handleStatusUpdate = (data: any) => {
      const newActivity: ActivityEvent = {
        id: `act-${Date.now()}`,
        type: 'system',
        action: data.type || 'Status Update',
        details: data.message || '',
        agentId: data.agent_id || '',
        agentName: data.agent_id || 'System',
        timestamp: new Date(),
        status: data.type === 'error' ? 'error' : 'info'
      };
      setActivities(prev => [newActivity, ...prev.slice(0, 49)]);
    };
    const handleActivity = (data: any) => {
      const newActivity: ActivityEvent = {
        id: `act-${Date.now()}`,
        type: (data.category || 'system') as ActivityEvent['type'],
        action: data.action || 'Activity',
        details: data.details || '',
        agentId: data.agent_id || '',
        agentName: data.agent_name || 'System',
        timestamp: new Date(),
        status: (data.status || 'info') as any
      };
      setActivities(prev => [newActivity, ...prev.slice(0, 49)]);
    };
    socket.on('status_update', handleStatusUpdate);
    socket.on('activity_update', handleActivity);
    return () => {
      socket.off('status_update', handleStatusUpdate);
      socket.off('activity_update', handleActivity);
    };
  }, [socket, isLive]);

  const filteredActivities = activities.filter(activity => 
    filter === 'all' || activity.type === filter
  );

  const getRelativeTime = (timestamp: Date) => {
    const now = new Date();
    const diff = now.getTime() - timestamp.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    
    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return timestamp.toLocaleDateString();
  };

  const filterOptions = [
    { key: 'all', label: 'All', count: activities.length },
    { key: 'connection', label: 'Connections', count: activities.filter(a => a.type === 'connection').length },
    { key: 'command', label: 'Commands', count: activities.filter(a => a.type === 'command').length },
    { key: 'stream', label: 'Streaming', count: activities.filter(a => a.type === 'stream').length },
    { key: 'file', label: 'Files', count: activities.filter(a => a.type === 'file').length },
    { key: 'security', label: 'Security', count: activities.filter(a => a.type === 'security').length }
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-4 w-4" />
            <CardTitle className="text-sm">Activity Feed</CardTitle>
            {isLive && (
              <div className="flex items-center space-x-1">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-xs text-muted-foreground">Live</span>
              </div>
            )}
          </div>
          {React.createElement(Button, {
            variant: "ghost",
            size: "sm",
            onClick: () => setIsLive(!isLive)
          }, isLive ? React.createElement(Square, { className: "h-3 w-3" }) : React.createElement(Play, { className: "h-3 w-3" }))}
        </div>
        
        {/* Filter buttons */}
        <div className="flex flex-wrap gap-1">
          {filterOptions.map(({ key, label, count }) => {
            return React.createElement(Button, {
              key: key,
              variant: filter === key ? 'default' : 'ghost',
              size: "sm",
              className: "h-7 text-xs",
              onClick: () => setFilter(key as any)
            }, label, count > 0 && React.createElement(Badge, {
              className: "ml-1 h-4 w-4 p-0 text-xs"
            }, count));
          })}
        </div>
      </CardHeader>
      
      <CardContent>
        <ScrollArea className="h-[300px]">
          <div className="space-y-3">
            {filteredActivities.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <Clock className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No activities yet</p>
              </div>
            ) : (
              filteredActivities.map((activity) => {
                const Icon = activityIcons[activity.type];
                
                return (
                  <div key={activity.id} className="flex items-start space-x-3 p-2 rounded-lg hover:bg-muted/50 transition-colors">
                    <div className={cn(
                      "mt-0.5 p-1 rounded-full bg-muted",
                      statusColors[activity.status]
                    )}>
                      <Icon className="h-3 w-3" />
                    </div>
                    
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{activity.action}</p>
                        <span className="text-xs text-muted-foreground">
                          {getRelativeTime(activity.timestamp)}
                        </span>
                      </div>
                      
                      <p className="text-xs text-muted-foreground">
                        {activity.details}
                      </p>
                      
                      {activity.agentId && (
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {activity.agentName}
                          </Badge>
                          <Badge 
                            variant={activity.status === 'success' ? 'default' : 
                                   activity.status === 'error' ? 'destructive' : 'secondary'}
                            className="text-xs capitalize"
                          >
                            {activity.status}
                          </Badge>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}