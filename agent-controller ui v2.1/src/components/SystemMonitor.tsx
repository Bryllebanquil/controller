import * as React from "react";
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

// Default metrics; will be updated from backend if available
const systemMetrics = {
  cpu: { usage: 0, temperature: 0, cores: 0, frequency: 0 },
  memory: { used: 0, total: 0, available: 0 },
  storage: { used: 0, total: 0, available: 0 },
  network: { upload: 0, download: 0, latency: 0 }
};

import { useEffect, useState } from 'react';

export function SystemMonitor() {
  const [metrics, setMetrics] = useState(systemMetrics);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      try {
        const res = await fetch('/api/system/info');
        const data = await res.json();
        if (!res.ok) return;
        const perf = data?.performance || {};
        if (isMounted) {
          setMetrics({
            cpu: { 
              usage: perf.cpu_percent || 0, 
              temperature: 0, // Temperature not available in psutil
              cores: perf.cpu_cores || 0, 
              frequency: perf.cpu_frequency_ghz || 0 
            },
            memory: { 
              used: perf.memory_percent || 0, 
              total: perf.memory_total_gb || 0, 
              available: perf.memory_available_gb || 0 
            },
            storage: { 
              used: perf.disk_percent || 0, 
              total: perf.disk_total_gb || 0, 
              available: perf.disk_free_gb || 0 
            },
            network: { 
              upload: perf.network_upload_mb || 0, 
              download: perf.network_download_mb || 0, 
              latency: 0 // Latency not available in psutil
            },
          });
        }
      } catch {}
    };
    load();
    const id = setInterval(load, 10000);
    return () => { isMounted = false; clearInterval(id); };
  }, []);

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
                <Badge variant="secondary">{metrics.cpu.usage}%</Badge>
                <Badge variant="outline">{metrics.cpu.frequency} GHz</Badge>
              </div>
            </div>
            <Progress value={metrics.cpu.usage} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{metrics.cpu.cores} cores</span>
              <span>{metrics.cpu.temperature}°C</span>
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
                <Badge variant="secondary">{metrics.memory.used}%</Badge>
                <Badge variant="outline">{metrics.memory.total} GB</Badge>
              </div>
            </div>
            <Progress value={metrics.memory.used} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Used: {(metrics.memory.total * metrics.memory.used / 100).toFixed(1)} GB</span>
              <span>Available: {metrics.memory.available} GB</span>
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
                <Badge variant="secondary">{metrics.storage.used}%</Badge>
                <Badge variant="outline">{metrics.storage.total} GB</Badge>
              </div>
            </div>
            <Progress value={metrics.storage.used} className="h-2" />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Used: {(metrics.storage.total * metrics.storage.used / 100).toFixed(0)} GB</span>
              <span>Free: {metrics.storage.available} GB</span>
            </div>
          </div>

          {/* Network */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Network className="h-4 w-4 text-orange-500" />
                <span className="text-sm">Network</span>
              </div>
              <Badge variant="secondary">{metrics.network.latency}ms</Badge>
            </div>
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Upload:</span>
                <span>{metrics.network.upload} MB/s</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Download:</span>
                <span>{metrics.network.download} MB/s</span>
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
                <p className="text-xs text-muted-foreground">{metrics.cpu.temperature}°C</p>
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
                <p className="text-xs text-muted-foreground">N/A</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}