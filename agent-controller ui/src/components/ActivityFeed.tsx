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

const mockActivities: ActivityEvent[] = [
  {
    id: 'act-001',
    type: 'connection',
    action: 'Agent Connected',
    details: 'Successfully established connection',
    agentId: 'agent-001',
    agentName: 'Windows-Desktop-01',
    timestamp: new Date(Date.now() - 30000),
    status: 'success'
  },
  {
    id: 'act-002',
    type: 'stream',
    action: 'Screen Stream Started',
    details: 'High quality stream initiated',
    agentId: 'agent-001',
    agentName: 'Windows-Desktop-01',
    timestamp: new Date(Date.now() - 120000),
    status: 'info'
  },
  {
    id: 'act-003',
    type: 'command',
    action: 'Command Executed',
    details: 'systeminfo command completed successfully',
    agentId: 'agent-002',
    agentName: 'Linux-Server-01',
    timestamp: new Date(Date.now() - 180000),
    status: 'success'
  },
  {
    id: 'act-004',
    type: 'connection',
    action: 'Agent Disconnected',
    details: 'Connection lost unexpectedly',
    agentId: 'agent-003',
    agentName: 'MacBook-Pro-01',
    timestamp: new Date(Date.now() - 300000),
    status: 'warning'
  },
  {
    id: 'act-005',
    type: 'security',
    action: 'Authentication Failed',
    details: 'Invalid credentials from 192.168.1.250',
    agentId: '',
    agentName: 'System',
    timestamp: new Date(Date.now() - 450000),
    status: 'error'
  },
  {
    id: 'act-006',
    type: 'file',
    action: 'File Transfer',
    details: 'Downloaded system logs (2.4 MB)',
    agentId: 'agent-002',
    agentName: 'Linux-Server-01',
    timestamp: new Date(Date.now() - 600000),
    status: 'success'
  }
];

export function ActivityFeed() {
  const [activities, setActivities] = useState<ActivityEvent[]>(mockActivities);
  const [filter, setFilter] = useState<'all' | ActivityEvent['type']>('all');
  const [isLive, setIsLive] = useState(true);

  // Simulate real-time activities
  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      if (Math.random() > 0.6) { // 40% chance every 5 seconds
        const activityTypes: ActivityEvent['type'][] = ['connection', 'command', 'stream', 'file', 'system'];
        const actions = {
          connection: ['Agent Connected', 'Agent Disconnected', 'Connection Timeout'],
          command: ['Command Executed', 'Command Failed', 'Batch Script Run'],
          stream: ['Stream Started', 'Stream Stopped', 'Quality Changed'],
          file: ['File Downloaded', 'File Uploaded', 'Directory Listed'],
          system: ['System Restart', 'Service Started', 'Update Installed']
        };
        
        const type = activityTypes[Math.floor(Math.random() * activityTypes.length)];
        const typeActions = actions[type];
        const action = typeActions[Math.floor(Math.random() * typeActions.length)];
        
        const newActivity: ActivityEvent = {
          id: `act-${Date.now()}`,
          type,
          action,
          details: 'Simulated activity for demonstration',
          agentId: `agent-${String(Math.floor(Math.random() * 3) + 1).padStart(3, '0')}`,
          agentName: ['Windows-Desktop-01', 'Linux-Server-01', 'MacBook-Pro-01'][Math.floor(Math.random() * 3)],
          timestamp: new Date(),
          status: ['success', 'info', 'warning'][Math.floor(Math.random() * 3)] as any
        };
        
        setActivities(prev => [newActivity, ...prev.slice(0, 49)]); // Keep last 50 activities
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [isLive]);

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
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsLive(!isLive)}
          >
            {isLive ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
          </Button>
        </div>
        
        {/* Filter buttons */}
        <div className="flex flex-wrap gap-1">
          {filterOptions.map(({ key, label, count }) => (
            <Button
              key={key}
              variant={filter === key ? 'default' : 'ghost'}
              size="sm"
              className="h-7 text-xs"
              onClick={() => setFilter(key as any)}
            >
              {label}
              {count > 0 && (
                <Badge className="ml-1 h-4 w-4 p-0 text-xs">{count}</Badge>
              )}
            </Button>
          ))}
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