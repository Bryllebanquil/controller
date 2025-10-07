import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { 
  Activity, 
  Cpu, 
  HardDrive, 
  Network, 
  Thermometer, 
  Zap,
  MemoryStick,
  Wifi
} from 'lucide-react';

// Mock system data
const systemMetrics = {
  cpu: {
    usage: 45,
    temperature: 65,
    cores: 8,
    frequency: 3.2
  },
  memory: {
    used: 62,
    total: 16,
    available: 6.1
  },
  storage: {
    used: 78,
    total: 500,
    available: 110
  },
  network: {
    upload: 2.4,
    download: 15.7,
    latency: 12
  }
};

export function SystemMonitor() {
  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center">
            <Activity className="h-4 w-4 mr-2" />
            System Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* CPU */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Cpu className="h-4 w-4 text-blue-500" />
                <span className="text-sm">CPU Usage</span>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary">{systemMetrics.cpu.usage}%</Badge>
                <Badge variant="outline">{systemMetrics.cpu.frequency} GHz</Badge>
              </div>
            </div>
            <Progress value={systemMetrics.cpu.usage} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{systemMetrics.cpu.cores} cores</span>
              <span>{systemMetrics.cpu.temperature}°C</span>
            </div>
          </div>

          {/* Memory */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MemoryStick className="h-4 w-4 text-green-500" />
                <span className="text-sm">Memory</span>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary">{systemMetrics.memory.used}%</Badge>
                <Badge variant="outline">{systemMetrics.memory.total} GB</Badge>
              </div>
            </div>
            <Progress value={systemMetrics.memory.used} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Used: {(systemMetrics.memory.total * systemMetrics.memory.used / 100).toFixed(1)} GB</span>
              <span>Available: {systemMetrics.memory.available} GB</span>
            </div>
          </div>

          {/* Storage */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <HardDrive className="h-4 w-4 text-purple-500" />
                <span className="text-sm">Storage</span>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary">{systemMetrics.storage.used}%</Badge>
                <Badge variant="outline">{systemMetrics.storage.total} GB</Badge>
              </div>
            </div>
            <Progress value={systemMetrics.storage.used} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Used: {(systemMetrics.storage.total * systemMetrics.storage.used / 100).toFixed(0)} GB</span>
              <span>Free: {systemMetrics.storage.available} GB</span>
            </div>
          </div>

          {/* Network */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Network className="h-4 w-4 text-orange-500" />
                <span className="text-sm">Network</span>
              </div>
              <Badge variant="secondary">{systemMetrics.network.latency}ms</Badge>
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Upload:</span>
                <span>{systemMetrics.network.upload} MB/s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Download:</span>
                <span>{systemMetrics.network.download} MB/s</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Thermometer className="h-4 w-4 text-red-500" />
              <div>
                <p className="text-sm font-medium">Temperature</p>
                <p className="text-xs text-muted-foreground">{systemMetrics.cpu.temperature}°C</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4 text-yellow-500" />
              <div>
                <p className="text-sm font-medium">Power</p>
                <p className="text-xs text-muted-foreground">85W</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}