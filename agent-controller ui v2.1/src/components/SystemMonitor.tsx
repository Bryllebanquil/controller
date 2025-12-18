import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { Activity, Cpu, HardDrive, Network, MemoryStick } from 'lucide-react';
import { useMemo } from 'react';
import { useSocket } from './SocketProvider';

export function SystemMonitor() {
  const { agents, selectedAgent, agentMetrics } = useSocket();

  const metrics = useMemo(() => {
    const current = agents.find(a => a.id === selectedAgent);
    const live = selectedAgent ? agentMetrics[selectedAgent] : undefined;
    return {
      cpu: { usage: live?.cpu ?? current?.performance.cpu ?? 0 },
      memory: { used: live?.memory ?? current?.performance.memory ?? 0 },
      network: { throughput: live?.network ?? current?.performance.network ?? 0 },
    };
  }, [agents, selectedAgent, agentMetrics]);

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center">
            <Activity className="h-4 w-4 mr-2" />
            Agent Performance
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* CPU */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Cpu className="h-4 w-4 text-blue-500" />
                <span className="text-sm">CPU</span>
              </div>
              <div className="flex items-center space-x-2">
                <Badge variant="secondary">{metrics.cpu.usage}%</Badge>
              </div>
            </div>
            <Progress value={metrics.cpu.usage} className="h-2" />
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
              </div>
            </div>
            <Progress value={metrics.memory.used} className="h-2" />
          </div>

          {/* Network (agent throughput) */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Network className="h-4 w-4 text-orange-500" />
                <span className="text-sm">Network</span>
              </div>
              <Badge variant="secondary">{metrics.network.throughput} MB/s</Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}