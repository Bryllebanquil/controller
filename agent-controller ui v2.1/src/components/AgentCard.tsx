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
  Network,
  Shield,
  User
} from 'lucide-react';
import { cn } from './ui/utils';
import { localizationService } from '../utils/localization';
import { useLanguage } from './LanguageSelector';
import { toast } from 'sonner';
import { apiClient } from '../services/api';
import { useSocket } from './SocketProvider';

interface Agent {
  id: string;
  name: string;
  alias?: string;
  rawName?: string;
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
  is_admin?: boolean;
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
  const { language } = useLanguage(); // Listen for language changes
  const { extensionStatus, checkExtensionStatus } = useSocket();

  const handleSelect = () => {
    onSelect();
    toast.info(`Selected agent: ${agent.name}`, {
      description: `${agent.platform} agent - ${isOnline ? 'Online' : 'Offline'}${agent.is_admin ? ' (Admin privileges)' : ''}`
    });
  };

  const handleMoreActions = async () => {
    try {
      const current = agent.alias || agent.rawName || agent.name || '';
      const next = window.prompt('Enter alias for this agent', current) || '';
      const alias = next.trim();
      const res = await apiClient.setAgentAlias(agent.id, alias);
      if (res.success) {
        toast.success(`Alias set for ${agent.id}`, { description: alias });
      } else {
        toast.error(res.error || 'Failed to set alias');
      }
    } catch (e: any) {
      toast.error(e?.message || 'Failed to set alias');
    }
  };

  const handleCapabilityClick = (capability: string) => {
    toast.info(`${agent.name} capability: ${capability}`, {
      description: `This agent supports ${capability} functionality.`
    });
  };

  const handlePerformanceClick = (metric: string, value: number) => {
    toast.info(`${agent.name} ${metric}: ${value}${metric === 'network' ? ' MB/s' : '%'}`, {
      description: `Current ${metric} usage for this agent.`
    });
  };
  const handleExtensionClick = () => {
    checkExtensionStatus(agent.id);
    toast.info(`Checking extension status for ${agent.name}`);
  };
  
  // Get localized text for badges (will re-render when language changes)
  const adminBadgeText = localizationService.getBadgeText(true);
  const userBadgeText = localizationService.getBadgeText(false);
  const adminAriaLabel = localizationService.getAriaLabel(true, agent.name);
  const userAriaLabel = localizationService.getAriaLabel(false, agent.name);
  
  return (
    <Card 
      className={cn(
        "cursor-pointer transition-all hover:shadow-md",
        isSelected && "ring-2 ring-primary",
        !isOnline && "opacity-75"
      )}
      onClick={handleSelect}
      role="article"
      aria-label={`${agent.name} - ${agent.is_admin === true ? adminAriaLabel : agent.is_admin === false ? userAriaLabel : 'Unknown privilege level'} - ${agent.status}`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2" aria-label={`Connection status: ${agent.status}`}>
            {isOnline ? (
              <Wifi className="h-4 w-4 text-green-600" aria-hidden="true" />
            ) : (
              <WifiOff className="h-4 w-4 text-red-600" aria-hidden="true" />
            )}
            <div className="flex items-center space-x-2">
              <CardTitle className="text-sm">
                {agent.alias ? `${agent.rawName || agent.name} (${agent.alias})` : (agent.rawName || agent.name)}
              </CardTitle>
              {agent.is_admin === true && (
                <Badge 
                  variant="default" 
                  className="bg-black text-white border-black hover:bg-black/90 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer dark:bg-white dark:text-black dark:border-white dark:hover:bg-white/90" 
                  title={`${adminAriaLabel} - This agent has elevated system access`}
                  role="status"
                  aria-live="polite"
                  tabIndex={0}
                  onClick={(e) => { 
                    e.stopPropagation(); 
                    toast.info(`${agent.name} privileges: Administrator`, {
                      description: 'This agent has elevated system access and can perform administrative operations.'
                    });
                  }}
                >
                  <Shield className="h-3 w-3" aria-hidden="true" />
                  <span className="sr-only">{localizationService.t('admin_aria_label')}:</span>
                  {adminBadgeText}
                </Badge>
              )}
              {agent.is_admin === false && (
                <Badge 
                  variant="default" 
                  className="bg-black text-white border-black hover:bg-black/90 focus:outline-none focus:ring-2 focus:ring-blue-500 cursor-pointer dark:bg-white dark:text-black dark:border-white dark:hover:bg-white/90" 
                  title={`${userAriaLabel} - This agent has normal system access`}
                  role="status"
                  aria-live="polite"
                  tabIndex={0}
                  onClick={(e) => { 
                    e.stopPropagation(); 
                    toast.info(`${agent.name} privileges: Standard User`, {
                      description: 'This agent has normal system access and operates with standard user permissions.'
                    });
                  }}
                >
                  <User className="h-3 w-3" aria-hidden="true" />
                  <span className="sr-only">{localizationService.t('user_aria_label')}:</span>
                  {userBadgeText}
                </Badge>
              )}
              {agent.is_admin === undefined && (
                <span className="sr-only" role="status">Privilege level unknown</span>
              )}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); handleMoreActions(); }}>
            <MoreVertical className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{agent.platform}</span>
          <Badge 
            variant={isOnline ? "default" : "secondary"}
            className="cursor-pointer hover:opacity-80 transition-opacity"
            onClick={(e) => { 
              e.stopPropagation(); 
              toast.info(`${agent.name} status: ${agent.status}`, {
                description: isOnline 
                  ? 'Agent is currently connected and responsive.' 
                  : 'Agent is offline or not responding to network requests.'
              });
            }}
            title="Click to view status details"
          >
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
                <div 
                  key={capability} 
                  className="flex items-center space-x-1 bg-muted px-2 py-1 rounded text-xs cursor-pointer hover:bg-muted/80 transition-colors"
                  onClick={(e) => { e.stopPropagation(); handleCapabilityClick(capability); }}
                  title={`Click to learn more about ${capability} capability`}
                >
                  <Icon className="h-3 w-3" />
                  <span>{capability}</span>
                </div>
              ) : null;
            })}
          </div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground mb-2">Extension</div>
          <div className="flex flex-wrap gap-1">
            <div
              className="flex items-center space-x-1 bg-muted px-2 py-1 rounded text-xs cursor-pointer hover:bg-muted/80 transition-colors"
              onClick={(e) => { e.stopPropagation(); handleExtensionClick(); }}
              title="Click to refresh extension status"
            >
              <Shield className="h-3 w-3" />
              <span>
                {extensionStatus[agent.id]?.installed
                  ? 'Installed'
                  : extensionStatus[agent.id]
                  ? 'Not Installed'
                  : 'Check'}
              </span>
            </div>
            {extensionStatus[agent.id] && (
              <div
                className="flex items-center space-x-1 bg-muted px-2 py-1 rounded text-xs"
                title="Policy applied"
              >
                <span>Policy: {extensionStatus[agent.id].policy_applied ? 'Yes' : 'No'}</span>
              </div>
            )}
          </div>
        </div>

        {/* Performance Metrics */}
        {isOnline && (
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">Performance</div>
            
            <div className="space-y-2">
              <div 
                className="flex items-center justify-between text-xs cursor-pointer hover:bg-muted/50 p-1 rounded transition-colors"
                onClick={(e) => { e.stopPropagation(); handlePerformanceClick('CPU', agent.performance.cpu); }}
                title="Click to view CPU details"
              >
                <div className="flex items-center space-x-1">
                  <Cpu className="h-3 w-3" />
                  <span>CPU</span>
                </div>
                <span>{agent.performance.cpu}%</span>
              </div>
              <Progress value={agent.performance.cpu} className="h-1" />
              
              <div 
                className="flex items-center justify-between text-xs cursor-pointer hover:bg-muted/50 p-1 rounded transition-colors"
                onClick={(e) => { e.stopPropagation(); handlePerformanceClick('Memory', agent.performance.memory); }}
                title="Click to view Memory details"
              >
                <div className="flex items-center space-x-1">
                  <HardDrive className="h-3 w-3" />
                  <span>Memory</span>
                </div>
                <span>{agent.performance.memory}%</span>
              </div>
              <Progress value={agent.performance.memory} className="h-1" />
              
              <div 
                className="flex items-center justify-between text-xs cursor-pointer hover:bg-muted/50 p-1 rounded transition-colors"
                onClick={(e) => { e.stopPropagation(); handlePerformanceClick('Network', agent.performance.network); }}
                title="Click to view Network details"
              >
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
