import React from 'react';
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Alert, AlertDescription } from './ui/alert';
import { Progress } from './ui/progress';
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
  Clock,
  XCircle,
  Loader2,
  Info
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

interface ActionStatus {
  id: string;
  status: 'idle' | 'executing' | 'success' | 'error' | 'warning';
  message: string;
  timestamp: number;
  progress?: number;
  details?: any;
}

interface QuickActionsProps {
  agentCount: number;
  selectedAgent: string | null;
}

export function QuickActions({ agentCount, selectedAgent }: QuickActionsProps) {
  const [executingAction, setExecutingAction] = useState(null as string | null);
  const [confirmAction, setConfirmAction] = useState(null as QuickAction | null);
  const [actionStatuses, setActionStatuses] = useState({} as Record<string, ActionStatus>);
  const [showStatusDialog, setShowStatusDialog] = useState(false);
  const [currentStatus, setCurrentStatus] = useState(null as ActionStatus | null);

  const updateActionStatus = (actionId: string, status: ActionStatus['status'], message: string, details?: any) => {
    const newStatus: ActionStatus = {
      id: actionId,
      status,
      message,
      timestamp: Date.now(),
      details
    };
    
    setActionStatuses(prev => ({
      ...prev,
      [actionId]: newStatus
    }));
    
    // Show detailed status dialog for important updates
    if (status === 'error' || status === 'warning' || (status === 'success' && details?.total_agents > 0)) {
      setCurrentStatus(newStatus);
      setShowStatusDialog(true);
    }
  };

  const executeAction = async (action: QuickAction) => {
    if (action.dangerous) {
      setConfirmAction(action);
      return;
    }

    // Check if agents are available for actions that require them
    if (action.requiresAgent && agentCount === 0) {
      updateActionStatus(action.id, 'error', 'No agents available for this action');
      toast.error('No agents available for this action');
      return;
    }

    setExecutingAction(action.id);
    updateActionStatus(action.id, 'executing', `Executing ${action.label}...`, { progress: 0 });

    try {
      console.log(`🔍 QuickActions: Executing action: ${action.id}`);
      
      // Show progress
      updateActionStatus(action.id, 'executing', `Sending ${action.label} to agents...`, { progress: 50 });
      
      const response = await apiClient.executeBulkAction(action.id, []);
      
      console.log(`🔍 QuickActions: Response:`, response);
      
      if (!response.success || response.error) {
        throw new Error(response.error || 'Action failed');
      }
      
      const totalAgents = response.data?.total_agents || 0;
      const successful = response.data?.successful || 0;
      const failed = response.data?.failed || 0;
      
      if (totalAgents === 0) {
        updateActionStatus(action.id, 'warning', 'No agents available to execute this action');
        toast.warning('No agents available to execute this action');
      } else if (failed > 0) {
        updateActionStatus(action.id, 'warning', `${action.label} completed with issues`, {
          total_agents: totalAgents,
          successful,
          failed,
          results: response.data?.results
        });
        toast.warning(`${action.label} completed: ${successful}/${totalAgents} successful`);
      } else {
        updateActionStatus(action.id, 'success', `${action.label} completed successfully`, {
          total_agents: totalAgents,
          successful,
          failed: 0
        });
        toast.success(`${action.label} sent to ${totalAgents} agent(s)`);
      }
      
    } catch (e: any) {
      console.error('🔍 QuickActions: Error:', e);
      const errorMessage = e.message || 'Failed to execute action';
      updateActionStatus(action.id, 'error', errorMessage, { error: e });
      toast.error(errorMessage);
    } finally {
      setExecutingAction(null);
    }
  };

  const confirmAndExecute = async (action: QuickAction) => {
    setConfirmAction(null);
    setExecutingAction(action.id);
    updateActionStatus(action.id, 'executing', `Executing ${action.label}...`, { progress: 0 });

    try {
      console.log(`🔍 QuickActions: Executing confirmed action: ${action.id}`);
      
      // Show progress
      updateActionStatus(action.id, 'executing', `Sending ${action.label} to agents...`, { progress: 50 });
      
      const response = await apiClient.executeBulkAction(action.id, []);
      
      console.log(`🔍 QuickActions: Response:`, response);
      
      if (!response.success || response.error) {
        throw new Error(response.error || 'Action failed');
      }
      
      const totalAgents = response.data?.total_agents || 0;
      const successful = response.data?.successful || 0;
      const failed = response.data?.failed || 0;
      
      if (totalAgents === 0) {
        updateActionStatus(action.id, 'warning', 'No agents available to execute this action');
        toast.warning('No agents available to execute this action');
      } else if (failed > 0) {
        updateActionStatus(action.id, 'warning', `${action.label} completed with issues`, {
          total_agents: totalAgents,
          successful,
          failed,
          results: response.data?.results
        });
        toast.warning(`${action.label} completed: ${successful}/${totalAgents} successful`);
      } else {
        updateActionStatus(action.id, 'success', `${action.label} completed successfully`, {
          total_agents: totalAgents,
          successful,
          failed: 0
        });
        toast.success(`${action.label} sent to ${totalAgents} agent(s)`);
      }
      
    } catch (e: any) {
      console.error('🔍 QuickActions: Error:', e);
      const errorMessage = e.message || 'Failed to execute action';
      updateActionStatus(action.id, 'error', errorMessage, { error: e });
      toast.error(errorMessage);
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
                    const actionStatus = actionStatuses[action.id];
                    
                    const getStatusIcon = () => {
                      if (isExecuting) return <Loader2 className="h-3 w-3 animate-spin" />;
                      if (actionStatus) {
                        switch (actionStatus.status) {
                          case 'success': return <CheckCircle className="h-3 w-3 text-green-500" />;
                          case 'error': return <XCircle className="h-3 w-3 text-red-500" />;
                          case 'warning': return <AlertTriangle className="h-3 w-3 text-yellow-500" />;
                          default: return null;
                        }
                      }
                      return null;
                    };
                    
                    return (
                      React.createElement(Button, {
                        key: action.id,
                        variant: action.variant,
                        size: "sm",
                        className: cn(
                          "h-auto p-3 justify-start text-left",
                          action.dangerous && "border-destructive/20"
                        ),
                        onClick: () => executeAction(action),
                        disabled: isDisabled
                      },
                        React.createElement("div", { className: "flex items-start space-x-3 w-full" },
                          React.createElement("div", { className: "flex items-center space-x-2 flex-shrink-0" },
                            isExecuting ? (
                              React.createElement(RefreshCw, { className: "h-4 w-4 animate-spin" })
                            ) : (
                              React.createElement(Icon, { className: "h-4 w-4" })
                            ),
                            getStatusIcon()
                          ),
                          React.createElement("div", { className: "text-left min-w-0 flex-1" },
                            React.createElement("div", { className: "flex items-center justify-between" },
                              React.createElement("div", { className: "text-xs font-medium truncate" }, action.label),
                              actionStatus && (
                                React.createElement("div", { className: "text-xs text-muted-foreground ml-2" },
                                  new Date(actionStatus.timestamp).toLocaleTimeString()
                                )
                              )
                            ),
                            React.createElement("div", { className: "text-xs text-muted-foreground line-clamp-2" },
                              actionStatus ? actionStatus.message : action.description
                            ),
                            actionStatus?.details?.progress !== undefined && (
                              React.createElement(Progress, {
                                value: actionStatus.details.progress,
                                className: "h-1 mt-1"
                              })
                            )
                          )
                        )
                      )
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
      {React.createElement(Dialog, { open: !!confirmAction, onOpenChange: () => setConfirmAction(null) },
        React.createElement(DialogContent, null,
          React.createElement(DialogHeader, null,
            React.createElement(DialogTitle, { className: "flex items-center space-x-2" },
              React.createElement(AlertTriangle, { className: "h-5 w-5 text-destructive" }),
              React.createElement("span", null, "Confirm Dangerous Action")
            ),
            React.createElement(DialogDescription, null,
              "This action requires confirmation as it may affect system operations."
            )
          ),
          
          confirmAction && (
            React.createElement("div", { className: "space-y-4" },
              React.createElement(Alert, { variant: "destructive" },
                React.createElement(AlertTriangle, { className: "h-4 w-4" }),
                React.createElement(AlertDescription, null,
                  `You are about to execute "${confirmAction.label}" on ${agentCount} agent(s). `,
                  "This action cannot be undone and may cause system disruptions."
                )
              ),
              
              React.createElement("div", { className: "p-4 bg-muted rounded-lg" },
                React.createElement("div", { className: "flex items-center space-x-2 mb-2" },
                  React.createElement(confirmAction.icon, { className: "h-4 w-4" }),
                  React.createElement("span", { className: "font-medium" }, confirmAction.label)
                ),
                React.createElement("p", { className: "text-sm text-muted-foreground" }, confirmAction.description)
              ),
              
              React.createElement("div", { className: "flex justify-end space-x-2" },
                React.createElement(Button, {
                  variant: "outline",
                  onClick: () => setConfirmAction(null)
                }, "Cancel"),
                React.createElement(Button, {
                  variant: "destructive",
                  onClick: () => confirmAndExecute(confirmAction)
                }, "Execute Action")
              )
            )
          )
        )
      )}

      {/* Status Dialog */}
      {React.createElement(Dialog, { open: showStatusDialog, onOpenChange: setShowStatusDialog },
        React.createElement(DialogContent, null,
          React.createElement(DialogHeader, null,
            React.createElement(DialogTitle, { className: "flex items-center space-x-2" },
              currentStatus?.status === 'success' && React.createElement(CheckCircle, { className: "h-5 w-5 text-green-500" }),
              currentStatus?.status === 'error' && React.createElement(XCircle, { className: "h-5 w-5 text-red-500" }),
              currentStatus?.status === 'warning' && React.createElement(AlertTriangle, { className: "h-5 w-5 text-yellow-500" }),
              currentStatus?.status === 'executing' && React.createElement(Loader2, { className: "h-5 w-5 animate-spin" }),
              React.createElement("span", null, "Action Status")
            ),
            React.createElement(DialogDescription, null,
              "Detailed information about the action execution"
            )
          ),
          
          currentStatus && (
            React.createElement("div", { className: "space-y-4" },
              React.createElement("div", { className: "p-4 bg-muted rounded-lg" },
                React.createElement("div", { className: "flex items-center justify-between mb-2" },
                  React.createElement("span", { className: "font-medium" }, currentStatus.message),
                  React.createElement("span", { className: "text-xs text-muted-foreground" },
                    new Date(currentStatus.timestamp).toLocaleString()
                  )
                ),
                
                currentStatus.details && (
                  React.createElement("div", { className: "space-y-2" },
                    currentStatus.details.total_agents !== undefined && (
                      React.createElement("div", { className: "text-sm" },
                        React.createElement("strong", null, "Total Agents: "),
                        currentStatus.details.total_agents
                      )
                    ),
                    currentStatus.details.successful !== undefined && (
                      React.createElement("div", { className: "text-sm" },
                        React.createElement("strong", null, "Successful: "),
                        currentStatus.details.successful
                      )
                    ),
                    currentStatus.details.failed !== undefined && (
                      React.createElement("div", { className: "text-sm" },
                        React.createElement("strong", null, "Failed: "),
                        currentStatus.details.failed
                      )
                    ),
                    
                    currentStatus.details.results && (
                      React.createElement("div", { className: "mt-3" },
                        React.createElement("div", { className: "text-sm font-medium mb-2" }, "Agent Results:"),
                        React.createElement("div", { className: "max-h-32 overflow-y-auto space-y-1" },
                          currentStatus.details.results.map((result: any, index: number) => (
                            React.createElement("div", {
                              key: index,
                              className: "text-xs p-2 bg-background rounded border"
                            },
                              React.createElement("div", { className: "font-medium" }, `Agent: ${result.agent_id}`),
                              React.createElement("div", {
                                className: `text-xs ${
                                  result.status === 'sent' ? 'text-green-600' : 'text-red-600'
                                }`
                              }, `Status: ${result.status}`),
                              result.error && (
                                React.createElement("div", { className: "text-xs text-red-600 mt-1" },
                                  `Error: ${result.error}`
                                )
                              )
                            )
                          ))
                        )
                      )
                    ),
                    
                    currentStatus.details.error && (
                      React.createElement("div", { className: "mt-3 p-3 bg-red-50 border border-red-200 rounded" },
                        React.createElement("div", { className: "text-sm font-medium text-red-800" }, "Error Details:"),
                        React.createElement("div", { className: "text-xs text-red-600 mt-1" },
                          currentStatus.details.error.message || String(currentStatus.details.error)
                        )
                      )
                    )
                  )
                )
              ),
              
              React.createElement("div", { className: "flex justify-end" },
                React.createElement(Button, {
                  onClick: () => setShowStatusDialog(false)
                }, "Close")
              )
            )
          )
        )
      )}
    </>
  );
}