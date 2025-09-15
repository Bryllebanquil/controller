import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { 
  Monitor, 
  Mic, 
  Camera, 
  Files, 
  Terminal, 
  MoreVertical,
  Wifi,
  WifiOff,
  Cpu,
  HardDrive,
  Network
} from 'lucide-react';
import { cn } from './ui/utils';

interface Agent {
  id: string;
  name: string;
  status: 'online' | 'offline';
  platform: string;
  ip: string;
  lastSeen: Date;
  capabilities: string[];
  performance: {
    cpu: number;
    memory: number;
    network: number;
  };
}

interface AgentCardProps {
  agent: Agent;
  isSelected: boolean;
  onSelect: () => void;
}

const capabilityIcons = {
  screen: Monitor,
  audio: Mic,
  camera: Camera,
  files: Files,
  commands: Terminal,
};

export function AgentCard({ agent, isSelected, onSelect }: AgentCardProps) {
  const isOnline = agent.status === 'online';
  
  return (
    <Card 
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isSelected && "ring-2 ring-primary",
        !isOnline && "opacity-75"
      )}
      onClick={onSelect}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isOnline ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-500" />
            )}
            <CardTitle className="text-sm">{agent.name}</CardTitle>
          </div>
          <Button variant="ghost" size="sm">
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{agent.platform}</span>
          <Badge variant={isOnline ? "default" : "secondary"}>
            {agent.status}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Capabilities */}
        <div>
          <div className="text-xs text-muted-foreground mb-2">Capabilities</div>
          <div className="flex flex-wrap gap-1">
            {agent.capabilities.map((capability) => {
              const Icon = capabilityIcons[capability as keyof typeof capabilityIcons];
              return Icon ? (
                <div key={capability} className="flex items-center space-x-1 bg-muted px-2 py-1 rounded text-xs">
                  <Icon className="h-3 w-3" />
                  <span>{capability}</span>
                </div>
              ) : null;
            })}
          </div>
        </div>

        {/* Performance Metrics */}
        {isOnline && (
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">Performance</div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-1">
                  <Cpu className="h-3 w-3" />
                  <span>CPU</span>
                </div>
                <span>{agent.performance.cpu}%</span>
              </div>
              <Progress value={agent.performance.cpu} className="h-1" />
              
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-1">
                  <HardDrive className="h-3 w-3" />
                  <span>Memory</span>
                </div>
                <span>{agent.performance.memory}%</span>
              </div>
              <Progress value={agent.performance.memory} className="h-1" />
              
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-1">
                  <Network className="h-3 w-3" />
                  <span>Network</span>
                </div>
                <span>{agent.performance.network} MB/s</span>
              </div>
            </div>
          </div>
        )}

        {/* Connection Info */}
        <div className="pt-2 border-t">
          <div className="text-xs text-muted-foreground">
            IP: {agent.ip}
          </div>
          <div className="text-xs text-muted-foreground">
            Last seen: {agent.lastSeen.toLocaleTimeString()}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}