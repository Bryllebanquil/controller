import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Zap,
  Power,
  RefreshCw,
  Download,
  Upload,
  Shield,
  Terminal,
  Monitor,
  Camera,
  Volume2,
  Settings,
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';
import { cn } from './ui/utils';
import { toast } from 'sonner';
import apiClient from '../services/api';

interface QuickAction {
  id: string;
  label: string;
  description: string;
  icon: any;
  category: 'power' | 'monitoring' | 'files' | 'security';
  variant: 'default' | 'destructive' | 'secondary';
  requiresAgent: boolean;
  dangerous?: boolean;
}

const quickActions: QuickAction[] = [
  {
    id: 'shutdown-all',
    label: 'Shutdown All',
    description: 'Shutdown all connected agents',
    icon: Power,
    category: 'power',
    variant: 'destructive',
    requiresAgent: false,
    dangerous: true
  },
  {
    id: 'restart-all',
    label: 'Restart All',
    description: 'Restart all connected agents',
    icon: RefreshCw,
    category: 'power',
    variant: 'destructive',
    requiresAgent: false,
    dangerous: true
  },
  {
    id: 'start-all-streams',
    label: 'Start All Streams',
    description: 'Begin screen streaming on all agents',
    icon: Monitor,
    category: 'monitoring',
    variant: 'default',
    requiresAgent: true
  },
  {
    id: 'start-all-audio',
    label: 'Start Audio Capture',
    description: 'Begin audio monitoring on all agents',
    icon: Volume2,
    category: 'monitoring',
    variant: 'default',
    requiresAgent: true
  },
  {
    id: 'collect-system-info',
    label: 'Collect System Info',
    description: 'Gather system information from all agents',
    icon: Terminal,
    category: 'monitoring',
    variant: 'secondary',
    requiresAgent: true
  },
  {
    id: 'download-logs',
    label: 'Download Logs',
    description: 'Download system logs from all agents',
    icon: Download,
    category: 'files',
    variant: 'secondary',
    requiresAgent: true
  },
  {
    id: 'security-scan',
    label: 'Security Scan',
    description: 'Run security assessment on all agents',
    icon: Shield,
    category: 'security',
    variant: 'default',
    requiresAgent: true
  },
  {
    id: 'update-agents',
    label: 'Update Agents',
    description: 'Push agent updates to all connected systems',
    icon: Upload,
    category: 'security',
    variant: 'secondary',
    requiresAgent: true
  }
];

interface QuickActionsProps {
  agentCount: number;
  selectedAgent: string | null;
}

export function QuickActions({ agentCount, selectedAgent }: QuickActionsProps) {
  const [executingAction, setExecutingAction] = useState<string | null>(null);
  const [confirmAction, setConfirmAction] = useState<QuickAction | null>(null);

  const executeAction = async (action: QuickAction) => {
    if (action.dangerous) {
      setConfirmAction(action);
      return;
    }

    setExecutingAction(action.id);
    try {
      console.log(`🔍 QuickActions: Executing action: ${action.id}`);
      const response = await apiClient.executeBulkAction(action.id, []);
      
      console.log(`🔍 QuickActions: Response:`, response);
      
      if (!response.success || response.error) {
        throw new Error(response.error || 'Action failed');
      }
      
      const totalAgents = response.data?.total_agents || 0;
      toast.success(`${action.label} sent to ${totalAgents} agent(s)`);
    } catch (e: any) {
      console.error('🔍 QuickActions: Error:', e);
      toast.error(e.message || 'Failed to execute action');
    } finally {
      setExecutingAction(null);
    }
  };

  const confirmAndExecute = async (action: QuickAction) => {
    setConfirmAction(null);
    setExecutingAction(action.id);
    try {
      console.log(`🔍 QuickActions: Executing confirmed action: ${action.id}`);
      const response = await apiClient.executeBulkAction(action.id, []);
      
      console.log(`🔍 QuickActions: Response:`, response);
      
      if (!response.success || response.error) {
        throw new Error(response.error || 'Action failed');
      }
      
      const totalAgents = response.data?.total_agents || 0;
      toast.success(`${action.label} sent to ${totalAgents} agent(s)`);
    } catch (e: any) {
      console.error('🔍 QuickActions: Error:', e);
      toast.error(e.message || 'Failed to execute action');
    } finally {
      setExecutingAction(null);
    }
  };

  const categoryIcons = {
    power: Power,
    monitoring: Monitor,
    files: Download,
    security: Shield
  };

  const categorizedActions = quickActions.reduce((acc, action) => {
    if (!acc[action.category]) {
      acc[action.category] = [];
    }
    acc[action.category].push(action);
    return acc;
  }, {} as Record<string, QuickAction[]>);

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4" />
              <CardTitle className="text-sm">Quick Actions</CardTitle>
            </div>
            <Badge variant="outline">{agentCount} agents</Badge>
          </div>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {Object.entries(categorizedActions).map(([category, actions]) => {
            const CategoryIcon = categoryIcons[category as keyof typeof categoryIcons];
            
            return (
              <div key={category}>
                <div className="flex items-center space-x-2 mb-2">
                  <CategoryIcon className="h-3 w-3 text-muted-foreground" />
                  <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
                    {category}
                  </span>
                </div>
                
                <div className="grid grid-cols-1 gap-2">
                  {actions.map((action) => {
                    const Icon = action.icon;
                    const isExecuting = executingAction === action.id;
                    const isDisabled = (action.requiresAgent && agentCount === 0) || isExecuting;
                    
                    return (
                      <Button
                        key={action.id}
                        variant={action.variant}
                        size="sm"
                        className={cn(
                          "h-auto p-3 justify-start text-left",
                          action.dangerous && "border-destructive/20"
                        )}
                        onClick={() => executeAction(action)}
                        disabled={isDisabled}
                      >
                        <div className="flex items-start space-x-3 w-full">
                          {isExecuting ? (
                            <RefreshCw className="h-4 w-4 mt-0.5 animate-spin flex-shrink-0" />
                          ) : (
                            <Icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          )}
                          <div className="text-left min-w-0 flex-1">
                            <div className="text-xs font-medium truncate">{action.label}</div>
                            <div className="text-xs text-muted-foreground line-clamp-2">{action.description}</div>
                          </div>
                        </div>
                      </Button>
                    );
                  })}
                </div>
              </div>
            );
          })}
          
          {agentCount === 0 && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="text-xs">
                No agents connected. Most actions require active agent connections.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Confirmation Dialog */}
      <Dialog open={!!confirmAction} onOpenChange={() => setConfirmAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              <span>Confirm Dangerous Action</span>
            </DialogTitle>
            <DialogDescription>
              This action requires confirmation as it may affect system operations.
            </DialogDescription>
          </DialogHeader>
          
          {confirmAction && (
            <div className="space-y-4">
              <Alert variant="destructive">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  You are about to execute "{confirmAction.label}" on {agentCount} agent(s). 
                  This action cannot be undone and may cause system disruptions.
                </AlertDescription>
              </Alert>
              
              <div className="p-4 bg-muted rounded-lg">
                <div className="flex items-center space-x-2 mb-2">
                  <confirmAction.icon className="h-4 w-4" />
                  <span className="font-medium">{confirmAction.label}</span>
                </div>
                <p className="text-sm text-muted-foreground">{confirmAction.description}</p>
              </div>
              
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setConfirmAction(null)}>
                  Cancel
                </Button>
                <Button 
                  variant="destructive" 
                  onClick={() => confirmAndExecute(confirmAction)}
                >
                  Execute Action
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}