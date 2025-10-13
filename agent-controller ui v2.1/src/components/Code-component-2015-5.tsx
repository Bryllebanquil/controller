import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Alert, AlertDescription, AlertTitle } from './ui/alert';
import { Separator } from './ui/separator';
import { 
  Monitor, 
  Activity, 
  Zap, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Upload, 
  Download,
  Cpu,
  MemoryStick,
  Network,
  TrendingUp,
  Settings,
  RefreshCw,
  ArrowUp,
  ArrowDown,
  Gauge
} from 'lucide-react';

interface WebRTCStats {
  connection_state: string;
  ice_connection_state: string;
  ice_gathering_state: string;
  signaling_state: string;
}

interface BandwidthStats {
  available_bandwidth: number;
  current_bitrate: number;
  packets_lost: number;
  rtt: number;
  jitter: number;
}

interface QualityData {
  quality_score: number;
  bandwidth_stats: BandwidthStats;
  quality_issues: string[];
  timestamp: string;
}

interface ProductionReadiness {
  current_implementation: string;
  target_implementation: string;
  migration_phase: string;
  current_usage: {
    agents: number;
    viewers: number;
    total_connections: number;
  };
  scalability_assessment: {
    aiortc_limit_reached: boolean;
    production_ready: boolean;
    recommended_action: string;
  };
  performance_metrics: {
    average_latency: number;
    average_bitrate: number;
    latency_target_met: boolean;
    bitrate_target_met: boolean;
  };
  recommendations: string[];
}

interface MigrationPlan {
  current_state: {
    implementation: string;
    max_viewers: number;
    technology: string;
  };
  target_state: {
    implementation: string;
    max_viewers: number;
    technology: string;
  };
  migration_phases: Array<{
    phase: number;
    name: string;
    description: string;
    duration: string;
    tasks: string[];
  }>;
  technical_requirements: string[];
  estimated_effort: string;
  risk_assessment: string;
}

interface WebRTCMonitoringProps {
  selectedAgent?: string | null;
}

export function WebRTCMonitoring({ selectedAgent }: WebRTCMonitoringProps) {
  const [stats, setStats] = useState<WebRTCStats | null>(null);
  const [qualityData, setQualityData] = useState<QualityData | null>(null);
  const [productionReadiness, setProductionReadiness] = useState<ProductionReadiness | null>(null);
  const [migrationPlan, setMigrationPlan] = useState<MigrationPlan | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [selectedQuality, setSelectedQuality] = useState<'low' | 'medium' | 'high' | 'auto'>('auto');

  // Mock data for demonstration - DISABLED for real-time operation
  useEffect(() => {
    // Mock data disabled - will use real Socket.IO data
    return;
    const mockStats: WebRTCStats = {
      connection_state: 'connected',
      ice_connection_state: 'connected',
      ice_gathering_state: 'complete',
      signaling_state: 'stable'
    };

    const mockQualityData: QualityData = {
      quality_score: 87,
      bandwidth_stats: {
        available_bandwidth: 2500000,
        current_bitrate: 1800000,
        packets_lost: 2,
        rtt: 24,
        jitter: 8.5
      },
      quality_issues: ['Minor jitter detected'],
      timestamp: new Date().toISOString()
    };

    const mockProductionReadiness: ProductionReadiness = {
      current_implementation: 'aiortc_sfu',
      target_implementation: 'mediasoup',
      migration_phase: 'planning',
      current_usage: {
        agents: 12,
        viewers: 35,
        total_connections: 47
      },
      scalability_assessment: {
        aiortc_limit_reached: false,
        production_ready: true,
        recommended_action: 'continue_with_aiortc'
      },
      performance_metrics: {
        average_latency: 28,
        average_bitrate: 1650000,
        latency_target_met: true,
        bitrate_target_met: true
      },
      recommendations: [
        'Monitor viewer count approaching aiortc limits',
        'Plan mediasoup migration for scale beyond 50 viewers'
      ]
    };

    const mockMigrationPlan: MigrationPlan = {
      current_state: {
        implementation: 'aiortc_sfu',
        max_viewers: 50,
        technology: 'Python + aiortc'
      },
      target_state: {
        implementation: 'mediasoup_sfu',
        max_viewers: 1000,
        technology: 'Node.js + mediasoup'
      },
      migration_phases: [
        {
          phase: 1,
          name: 'Parallel Implementation',
          description: 'Implement mediasoup alongside existing aiortc',
          duration: '2-3 weeks',
          tasks: [
            'Set up Node.js mediasoup server',
            'Implement mediasoup SFU logic',
            'Create migration endpoints',
            'Test with subset of viewers'
          ]
        },
        {
          phase: 2,
          name: 'Gradual Migration',
          description: 'Migrate viewers from aiortc to mediasoup',
          duration: '1-2 weeks',
          tasks: [
            'Implement viewer routing logic',
            'Add load balancing between aiortc and mediasoup',
            'Monitor performance during migration',
            'Handle fallback scenarios'
          ]
        },
        {
          phase: 3,
          name: 'Full Migration',
          description: 'Complete migration to mediasoup',
          duration: '1 week',
          tasks: [
            'Migrate all remaining viewers',
            'Decommission aiortc implementation',
            'Performance validation',
            'Documentation updates'
          ]
        }
      ],
      technical_requirements: [
        'Node.js 18+ runtime',
        'mediasoup library installation',
        'Redis for session management',
        'Load balancer configuration',
        'Monitoring and alerting setup'
      ],
      estimated_effort: '4-6 weeks',
      risk_assessment: 'Medium - requires careful testing and rollback plan'
    };

    setStats(mockStats);
    setQualityData(mockQualityData);
    setProductionReadiness(mockProductionReadiness);
    setMigrationPlan(mockMigrationPlan);
  }, [selectedAgent]);

  const getConnectionStateColor = (state: string) => {
    switch (state) {
      case 'connected': return 'text-green-500';
      case 'connecting': return 'text-yellow-500';
      case 'disconnected': return 'text-red-500';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-500';
    }
  };

  const getQualityScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const formatBitrate = (bitrate: number) => {
    if (bitrate >= 1000000) {
      return `${(bitrate / 1000000).toFixed(1)} Mbps`;
    }
    return `${(bitrate / 1000).toFixed(0)} kbps`;
  };

  const handleQualityChange = (quality: 'low' | 'medium' | 'high' | 'auto') => {
    setSelectedQuality(quality);
    // In real app, emit Socket.IO event: socket.emit('webrtc_set_quality', { agent_id: selectedAgent, quality });
    console.log(`Setting WebRTC quality to ${quality} for agent ${selectedAgent}`);
  };

  const toggleAdaptiveBitrate = () => {
    // In real app, emit Socket.IO event: socket.emit('webrtc_adaptive_bitrate_control', { agent_id: selectedAgent });
    console.log(`Triggering adaptive bitrate control for agent ${selectedAgent}`);
  };

  const toggleFrameDropping = () => {
    // In real app, emit Socket.IO event: socket.emit('webrtc_implement_frame_dropping', { agent_id: selectedAgent });
    console.log(`Implementing frame dropping for agent ${selectedAgent}`);
  };

  if (!selectedAgent) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            WebRTC Production Monitoring
          </CardTitle>
          <CardDescription>
            Select an agent to view WebRTC streaming performance and production scale monitoring
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No agent selected for WebRTC monitoring
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Monitor className="h-5 w-5" />
                WebRTC Production Monitoring
              </CardTitle>
              <CardDescription>
                Agent {selectedAgent} - Advanced WebRTC streaming performance and scalability analysis
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsMonitoring(!isMonitoring)}
              >
                <RefreshCw className={`h-4 w-4 ${isMonitoring ? 'animate-spin' : ''}`} />
                {isMonitoring ? 'Stop' : 'Start'} Monitoring
              </Button>
              <Badge variant={stats?.connection_state === 'connected' ? 'default' : 'destructive'}>
                {stats?.connection_state}
              </Badge>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="quality" className="space-y-4">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="quality">Quality Metrics</TabsTrigger>
              <TabsTrigger value="controls">Stream Controls</TabsTrigger>
              <TabsTrigger value="production">Production Scale</TabsTrigger>
              <TabsTrigger value="migration">Migration Plan</TabsTrigger>
            </TabsList>

            <TabsContent value="quality" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Gauge className="h-4 w-4" />
                      Quality Score
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className={`text-2xl font-bold ${getQualityScoreColor(qualityData?.quality_score || 0)}`}>
                      {qualityData?.quality_score}/100
                    </div>
                    <Progress value={qualityData?.quality_score} className="mt-2" />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Upload className="h-4 w-4" />
                      Bitrate
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {formatBitrate(qualityData?.bandwidth_stats.current_bitrate || 0)}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Available: {formatBitrate(qualityData?.bandwidth_stats.available_bandwidth || 0)}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Latency
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {qualityData?.bandwidth_stats.rtt}ms
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Jitter: {qualityData?.bandwidth_stats.jitter}ms
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Packet Loss
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      {qualityData?.bandwidth_stats.packets_lost}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Packets lost
                    </div>
                  </CardContent>
                </Card>
              </div>

              {qualityData?.quality_issues && qualityData.quality_issues.length > 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Quality Issues Detected</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside space-y-1">
                      {qualityData.quality_issues.map((issue, index) => (
                        <li key={index}>{issue}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Connection States</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Connection State:</span>
                        <Badge className={getConnectionStateColor(stats?.connection_state || '')}>
                          {stats?.connection_state}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">ICE Connection:</span>
                        <Badge className={getConnectionStateColor(stats?.ice_connection_state || '')}>
                          {stats?.ice_connection_state}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">ICE Gathering:</span>
                        <Badge variant="outline">
                          {stats?.ice_gathering_state}
                        </Badge>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Signaling State:</span>
                        <Badge variant="outline">
                          {stats?.signaling_state}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="controls" className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Stream Quality Controls
                  </CardTitle>
                  <CardDescription>
                    Advanced WebRTC streaming optimization and quality management
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Quality Level</label>
                      <div className="flex gap-2">
                        {(['low', 'medium', 'high', 'auto'] as const).map((quality) => (
                          <Button
                            key={quality}
                            variant={selectedQuality === quality ? 'default' : 'outline'}
                            size="sm"
                            onClick={() => handleQualityChange(quality)}
                          >
                            {quality.charAt(0).toUpperCase() + quality.slice(1)}
                          </Button>
                        ))}
                      </div>
                      <p className="text-xs text-muted-foreground mt-1">
                        Auto mode uses adaptive bitrate control based on network conditions
                      </p>
                    </div>

                    <Separator />

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">Adaptive Bitrate Control</CardTitle>
                          <CardDescription className="text-sm">
                            Automatically adjust streaming quality based on network conditions
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button onClick={toggleAdaptiveBitrate} className="w-full">
                            <TrendingUp className="h-4 w-4 mr-2" />
                            Trigger Adaptation
                          </Button>
                        </CardContent>
                      </Card>

                      <Card>
                        <CardHeader className="pb-3">
                          <CardTitle className="text-base">Frame Dropping</CardTitle>
                          <CardDescription className="text-sm">
                            Implement intelligent frame dropping under high system load
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Button onClick={toggleFrameDropping} className="w-full">
                            <ArrowDown className="h-4 w-4 mr-2" />
                            Enable Frame Drop
                          </Button>
                        </CardContent>
                      </Card>
                    </div>

                    <Card className="bg-muted/50">
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base">Quality Thresholds</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <div className="font-medium">Min Bitrate</div>
                            <div className="text-muted-foreground">100 kbps</div>
                          </div>
                          <div>
                            <div className="font-medium">Max Latency</div>
                            <div className="text-muted-foreground">1000ms</div>
                          </div>
                          <div>
                            <div className="font-medium">Min FPS</div>
                            <div className="text-muted-foreground">15 fps</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="production" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Network className="h-5 w-5" />
                      Current Usage
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between">
                        <span>Active Agents:</span>
                        <span className="font-medium">{productionReadiness?.current_usage.agents}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Connected Viewers:</span>
                        <span className="font-medium">{productionReadiness?.current_usage.viewers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Total Connections:</span>
                        <span className="font-medium">{productionReadiness?.current_usage.total_connections}</span>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm">Viewer Capacity:</span>
                        <span className="text-sm text-muted-foreground">35/50 (70%)</span>
                      </div>
                      <Progress value={70} className="h-2" />
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <CheckCircle className="h-5 w-5" />
                      Performance Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span>Average Latency:</span>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{productionReadiness?.performance_metrics.average_latency}ms</span>
                          {productionReadiness?.performance_metrics.latency_target_met ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          )}
                        </div>
                      </div>
                      <div className="flex justify-between items-center">
                        <span>Average Bitrate:</span>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">
                            {formatBitrate(productionReadiness?.performance_metrics.average_bitrate || 0)}
                          </span>
                          {productionReadiness?.performance_metrics.bitrate_target_met ? (
                            <CheckCircle className="h-4 w-4 text-green-500" />
                          ) : (
                            <AlertTriangle className="h-4 w-4 text-yellow-500" />
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Implementation Status</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div>
                        <div className="font-medium text-sm">Current Implementation</div>
                        <Badge variant="outline" className="mt-1">
                          {productionReadiness?.current_implementation}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-1">
                          Python + aiortc (Max 50 viewers)
                        </div>
                      </div>
                      <div>
                        <div className="font-medium text-sm">Production Ready</div>
                        <Badge variant={productionReadiness?.scalability_assessment.production_ready ? 'default' : 'destructive'} className="mt-1">
                          {productionReadiness?.scalability_assessment.production_ready ? 'Yes' : 'No'}
                        </Badge>
                      </div>
                    </div>
                    <div className="space-y-3">
                      <div>
                        <div className="font-medium text-sm">Target Implementation</div>
                        <Badge variant="secondary" className="mt-1">
                          {productionReadiness?.target_implementation}
                        </Badge>
                        <div className="text-xs text-muted-foreground mt-1">
                          Node.js + mediasoup (Max 1000 viewers)
                        </div>
                      </div>
                      <div>
                        <div className="font-medium text-sm">Migration Phase</div>
                        <Badge variant="outline" className="mt-1">
                          {productionReadiness?.migration_phase}
                        </Badge>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {productionReadiness?.recommendations && productionReadiness.recommendations.length > 0 && (
                <Alert>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle>Production Recommendations</AlertTitle>
                  <AlertDescription>
                    <ul className="list-disc list-inside space-y-1 mt-2">
                      {productionReadiness.recommendations.map((rec, index) => (
                        <li key={index}>{rec}</li>
                      ))}
                    </ul>
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>

            <TabsContent value="migration" className="space-y-4">
              {migrationPlan && (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Current State</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Implementation:</span>
                            <Badge variant="outline">{migrationPlan.current_state.implementation}</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span>Max Viewers:</span>
                            <span className="font-medium">{migrationPlan.current_state.max_viewers}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Technology:</span>
                            <span className="text-sm text-muted-foreground">{migrationPlan.current_state.technology}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Target State</CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          <div className="flex justify-between">
                            <span>Implementation:</span>
                            <Badge variant="default">{migrationPlan.target_state.implementation}</Badge>
                          </div>
                          <div className="flex justify-between">
                            <span>Max Viewers:</span>
                            <span className="font-medium flex items-center gap-1">
                              {migrationPlan.target_state.max_viewers}
                              <ArrowUp className="h-3 w-3 text-green-500" />
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Technology:</span>
                            <span className="text-sm text-muted-foreground">{migrationPlan.target_state.technology}</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  <Card>
                    <CardHeader>
                      <CardTitle>Migration Phases</CardTitle>
                      <CardDescription>
                        Estimated effort: {migrationPlan.estimated_effort} • Risk: {migrationPlan.risk_assessment}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {migrationPlan.migration_phases.map((phase) => (
                          <Card key={phase.phase}>
                            <CardHeader className="pb-3">
                              <div className="flex items-center justify-between">
                                <CardTitle className="text-base">
                                  Phase {phase.phase}: {phase.name}
                                </CardTitle>
                                <Badge variant="outline">{phase.duration}</Badge>
                              </div>
                              <CardDescription>{phase.description}</CardDescription>
                            </CardHeader>
                            <CardContent>
                              <div className="space-y-2">
                                {phase.tasks.map((task, index) => (
                                  <div key={index} className="flex items-center gap-2 text-sm">
                                    <div className="w-1.5 h-1.5 bg-muted-foreground rounded-full" />
                                    {task}
                                  </div>
                                ))}
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle>Technical Requirements</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          {migrationPlan.technical_requirements.map((req, index) => (
                            <div key={index} className="flex items-center gap-2 text-sm">
                              <CheckCircle className="w-4 h-4 text-green-500" />
                              {req}
                            </div>
                          ))}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}