import * as React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Shield,
  Monitor,
  Terminal,
  Files,
  Activity,
  Camera,
  Volume2,
  Wifi,
  Lock,
  Zap,
  Users,
  Code,
  Globe,
  Download,
  Upload,
  Play,
  Pause,
  RotateCcw,
  Settings,
  Search,
  Filter,
  Keyboard,
  Info,
  ExternalLink,
  Github,
  Mail,
  BookOpen,
  Lightbulb,
  CheckCircle
} from 'lucide-react';

interface Feature {
  icon: any;
  title: string;
  description: string;
  category: 'core' | 'monitoring' | 'management' | 'security';
  capabilities: string[];
}

const features: Feature[] = [
  {
    icon: Monitor,
    title: 'Real-time Streaming',
    description: 'Live screen, camera, and audio streaming with WebRTC technology',
    category: 'core',
    capabilities: ['Screen capture', 'Camera feed', 'Audio monitoring', 'Low latency', 'Multi-stream']
  },
  {
    icon: Terminal,
    title: 'Remote Command Execution',
    description: 'Execute commands and scripts on remote agents with real-time output',
    category: 'core',
    capabilities: ['PowerShell/CMD', 'Bash/Shell', 'Python scripts', 'Batch operations', 'Output streaming']
  },
  {
    icon: Files,
    title: 'File Management',
    description: 'Browse, upload, download, and manage files across all connected agents',
    category: 'management',
    capabilities: ['File browser', 'Bulk operations', 'Drag & drop', 'Remote editing', 'Permission management']
  },
  {
    icon: Activity,
    title: 'System Monitoring',
    description: 'Monitor CPU, memory, network, and system performance in real-time',
    category: 'monitoring',
    capabilities: ['Performance metrics', 'Process monitoring', 'Network statistics', 'Historical data', 'Alerts']
  },
  {
    icon: Shield,
    title: 'Advanced Security',
    description: 'End-to-end encryption, authentication, and secure communication protocols',
    category: 'security',
    capabilities: ['AES encryption', 'Certificate validation', 'Two-factor auth', 'Session management', 'Audit logs']
  },
  {
    icon: Users,
    title: 'Multi-Agent Management',
    description: 'Manage multiple agents simultaneously with centralized control',
    category: 'management',
    capabilities: ['Bulk operations', 'Group management', 'Status monitoring', 'Auto-discovery', 'Load balancing']
  }
];

const shortcuts = [
  { key: 'Ctrl + 1-6', action: 'Switch between tabs (Overview, Agents, etc.)' },
  { key: 'Ctrl + F', action: 'Focus search bar' },
  { key: 'Ctrl + A', action: 'Select first available agent' },
  { key: 'Escape', action: 'Deselect current agent' },
  { key: 'Ctrl + R', action: 'Refresh agent list' },
  { key: 'Ctrl + S', action: 'Open settings' },
  { key: 'Ctrl + ?', action: 'Show keyboard shortcuts' },
  { key: 'F11', action: 'Toggle fullscreen' }
];

const usageSteps = [
  {
    step: 1,
    title: 'Install Agent',
    description: 'Deploy the Neural Control Hub agent on target systems',
    details: 'Download and run the agent installer on Windows, Linux, or macOS systems you want to control.'
  },
  {
    step: 2,
    title: 'Connect Agents',
    description: 'Agents automatically connect to the control hub',
    details: 'Once installed, agents will appear in the Agents tab with their status, platform, and capabilities.'
  },
  {
    step: 3,
    title: 'Select & Control',
    description: 'Click on an agent to start remote operations',
    details: 'Use the sidebar to switch between different control modes: streaming, commands, files, and monitoring.'
  },
  {
    step: 4,
    title: 'Monitor & Manage',
    description: 'Use the overview dashboard for system-wide monitoring',
    details: 'View real-time statistics, activity feeds, and perform bulk operations across multiple agents.'
  }
];

export function About() {
  const coreFeatures = features.filter(f => f.category === 'core');
  const managementFeatures = features.filter(f => f.category === 'management');
  const monitoringFeatures = features.filter(f => f.category === 'monitoring');
  const securityFeatures = features.filter(f => f.category === 'security');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center space-y-4">
        <div className="flex items-center justify-center space-x-3">
          <Shield className="h-12 w-12 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Neural Control Hub</h1>
            <p className="text-lg text-muted-foreground">Advanced Remote Administration System</p>
          </div>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <Badge variant="default">v2.1.0</Badge>
          <Badge variant="secondary">Production Ready</Badge>
          <Badge variant="outline">Multi-Platform</Badge>
        </div>
      </div>

      {/* Quick Start */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Play className="h-5 w-5" />
            <span>Quick Start Guide</span>
          </CardTitle>
          <CardDescription>Get started with Neural Control Hub in 4 simple steps</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {usageSteps.map((step) => (
              <div key={step.step} className="space-y-3">
                <div className="flex items-center space-x-2">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground font-semibold">
                    {step.step}
                  </div>
                  <h3 className="font-semibold">{step.title}</h3>
                </div>
                <p className="text-sm text-muted-foreground">{step.description}</p>
                <p className="text-xs text-muted-foreground">{step.details}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Core Features */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Core Features</span>
          </CardTitle>
          <CardDescription>Powerful remote administration capabilities</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {coreFeatures.map((feature) => (
              <div key={feature.title} className="space-y-3">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 rounded-lg">
                    <feature.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
                <div className="flex flex-wrap gap-1">
                  {feature.capabilities.map((cap) => (
                    <Badge key={cap} variant="secondary" className="text-xs">
                      {cap}
                    </Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* All Features by Category */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Settings className="h-5 w-5" />
              <span>Management</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {managementFeatures.map((feature) => (
              <div key={feature.title} className="space-y-2">
                <div className="flex items-center space-x-2">
                  <feature.icon className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">{feature.title}</span>
                </div>
                <p className="text-xs text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Monitoring */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Monitoring</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {monitoringFeatures.map((feature) => (
              <div key={feature.title} className="space-y-2">
                <div className="flex items-center space-x-2">
                  <feature.icon className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">{feature.title}</span>
                </div>
                <p className="text-xs text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Security */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Shield className="h-5 w-5" />
              <span>Security</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {securityFeatures.map((feature) => (
              <div key={feature.title} className="space-y-2">
                <div className="flex items-center space-x-2">
                  <feature.icon className="h-4 w-4 text-primary" />
                  <span className="font-medium text-sm">{feature.title}</span>
                </div>
                <p className="text-xs text-muted-foreground">{feature.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {/* Keyboard Shortcuts */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Keyboard className="h-5 w-5" />
            <span>Keyboard Shortcuts</span>
          </CardTitle>
          <CardDescription>Speed up your workflow with these keyboard shortcuts</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {shortcuts.map((shortcut) => (
              <div key={shortcut.key} className="flex items-center justify-between space-x-4">
                <span className="text-sm">{shortcut.action}</span>
                <Badge variant="outline" className="font-mono text-xs">
                  {shortcut.key}
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* How to Use */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <BookOpen className="h-5 w-5" />
            <span>How to Use Neural Control Hub</span>
          </CardTitle>
          <CardDescription>Detailed usage instructions for each feature</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overview Tab */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span>Overview Tab</span>
            </h3>
            <ul className="space-y-1 text-sm text-muted-foreground ml-6">
              <li>• View system-wide statistics and connected agent count</li>
              <li>• Monitor real-time activity feed with agent events</li>
              <li>• Access quick actions for bulk operations</li>
              <li>• Check system performance metrics</li>
            </ul>
          </div>

          {/* Agents Tab */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center space-x-2">
              <Users className="h-4 w-4" />
              <span>Agents Tab</span>
            </h3>
            <ul className="space-y-1 text-sm text-muted-foreground ml-6">
              <li>• View all connected agents with their status and platform</li>
              <li>• Click on an agent card to select it for operations</li>
              <li>• Use search and filters to find specific agents</li>
              <li>• Sort agents by name, status, platform, or performance</li>
            </ul>
          </div>

          {/* Streaming Tab */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center space-x-2">
              <Monitor className="h-4 w-4" />
              <span>Streaming Tab</span>
            </h3>
            <ul className="space-y-1 text-sm text-muted-foreground ml-6">
              <li>• View live screen capture from selected agent</li>
              <li>• Monitor camera feed if available on the agent</li>
              <li>• Control streaming quality and frame rate</li>
              <li>• Take screenshots and record sessions</li>
            </ul>
          </div>

          {/* Commands Tab */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center space-x-2">
              <Terminal className="h-4 w-4" />
              <span>Commands Tab</span>
            </h3>
            <ul className="space-y-1 text-sm text-muted-foreground ml-6">
              <li>• Execute commands on the selected agent</li>
              <li>• Choose between PowerShell, CMD, or Bash</li>
              <li>• View real-time command output</li>
              <li>• Save frequently used commands for quick access</li>
            </ul>
          </div>

          {/* Files Tab */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center space-x-2">
              <Files className="h-4 w-4" />
              <span>Files Tab</span>
            </h3>
            <ul className="space-y-1 text-sm text-muted-foreground ml-6">
              <li>• Browse remote file system like a local folder</li>
              <li>• Upload files by dragging and dropping</li>
              <li>• Download files and folders as zip archives</li>
              <li>• Edit text files directly in the browser</li>
            </ul>
          </div>

          {/* Monitoring Tab */}
          <div className="space-y-3">
            <h3 className="font-semibold flex items-center space-x-2">
              <Activity className="h-4 w-4" />
              <span>Monitoring Tab</span>
            </h3>
            <ul className="space-y-1 text-sm text-muted-foreground ml-6">
              <li>• Monitor real-time system performance metrics</li>
              <li>• View CPU, memory, and network usage charts</li>
              <li>• Track running processes and services</li>
              <li>• Set up alerts for performance thresholds</li>
            </ul>
          </div>
        </CardContent>
      </Card>

      {/* Tips and Best Practices */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Lightbulb className="h-5 w-5" />
            <span>Tips & Best Practices</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Performance</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Limit concurrent streams for better performance</li>
                <li>• Use filters to manage large numbers of agents</li>
                <li>• Enable compression for slower networks</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Security</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Always use encryption in production</li>
                <li>• Enable two-factor authentication</li>
                <li>• Regularly update agent software</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Workflow</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Use keyboard shortcuts for faster navigation</li>
                <li>• Save frequently used commands</li>
                <li>• Organize agents with meaningful names</li>
              </ul>
            </div>
            <div className="space-y-2">
              <h4 className="font-semibold text-sm">Troubleshooting</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Check network status for connection issues</li>
                <li>• Review activity feed for error messages</li>
                <li>• Enable debug mode for detailed logs</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Requirements */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Monitor className="h-5 w-5" />
            <span>System Requirements</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold">Control Hub (Server)</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Modern web browser (Chrome 80+, Firefox 75+, Safari 13+)</li>
                <li>• 4GB RAM minimum, 8GB recommended</li>
                <li>• Network access to target systems</li>
                <li>• WebRTC support for streaming features</li>
              </ul>
            </div>
            <div className="space-y-3">
              <h4 className="font-semibold">Agent (Target Systems)</h4>
              <ul className="space-y-1 text-sm text-muted-foreground">
                <li>• Windows 10+, Linux (Ubuntu 18.04+), macOS 10.15+</li>
                <li>• 1GB RAM minimum, 2GB recommended</li>
                <li>• Network connectivity to control hub</li>
                <li>• Administrative privileges for full functionality</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Support */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Info className="h-5 w-5" />
            <span>Support & Resources</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" className="flex items-center space-x-2">
              <BookOpen className="h-4 w-4" />
              <span>Documentation</span>
              <ExternalLink className="h-3 w-3" />
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Github className="h-4 w-4" />
              <span>Source Code</span>
              <ExternalLink className="h-3 w-3" />
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Mail className="h-4 w-4" />
              <span>Contact Support</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}