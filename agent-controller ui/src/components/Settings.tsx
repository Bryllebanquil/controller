import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { useTheme } from './ThemeProvider';
import { useSocket } from './SocketProvider-new';
import { 
  Settings as SettingsIcon,
  Monitor,
  Sun,
  Moon,
  Bell,
  Shield,
  Network,
  Database,
  Key,
  Download,
  Upload,
  Trash2,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info,
  LogOut
} from 'lucide-react';

interface SettingsData {
  general: {
    autoConnect: boolean;
    startMinimized: boolean;
    enableTray: boolean;
    language: string;
    updateFrequency: string;
  };
  notifications: {
    agentConnect: boolean;
    agentDisconnect: boolean;
    commandComplete: boolean;
    errors: boolean;
    sound: boolean;
    desktop: boolean;
  };
  security: {
    encryption: boolean;
    twoFactor: boolean;
    sessionTimeout: string;
    maxFailedAttempts: number;
    requireAuth: boolean;
  };
  network: {
    port: number;
    maxConnections: number;
    timeout: number;
    compression: boolean;
    bufferSize: string;
  };
  advanced: {
    debugMode: boolean;
    logLevel: string;
    maxLogSize: string;
    autoBackup: boolean;
    backupFrequency: string;
  };
}

export function Settings() {
  const { theme, setTheme } = useTheme();
  const { logout } = useSocket();
  const [settings, setSettings] = useState<SettingsData>({
    general: {
      autoConnect: true,
      startMinimized: false,
      enableTray: true,
      language: 'en',
      updateFrequency: '1h'
    },
    notifications: {
      agentConnect: true,
      agentDisconnect: true,
      commandComplete: false,
      errors: true,
      sound: true,
      desktop: true
    },
    security: {
      encryption: true,
      twoFactor: false,
      sessionTimeout: '30m',
      maxFailedAttempts: 3,
      requireAuth: true
    },
    network: {
      port: 8080,
      maxConnections: 100,
      timeout: 30,
      compression: true,
      bufferSize: '1MB'
    },
    advanced: {
      debugMode: false,
      logLevel: 'info',
      maxLogSize: '100MB',
      autoBackup: true,
      backupFrequency: '24h'
    }
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [saved, setSaved] = useState(false);

  const updateSetting = (category: keyof SettingsData, key: string, value: any) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value
      }
    }));
    setHasChanges(true);
    setSaved(false);
  };

  const saveSettings = () => {
    // Simulate saving
    setTimeout(() => {
      setHasChanges(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 500);
  };

  const resetSettings = () => {
    // Reset to defaults (simplified)
    setHasChanges(true);
  };

  const exportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'neural-control-hub-settings.json';
    link.click();
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold">Settings</h2>
          <p className="text-muted-foreground">Manage your Neural Control Hub configuration</p>
        </div>
        <div className="flex items-center space-x-2">
          {saved && (
            <Alert className="w-auto">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>Settings saved successfully</AlertDescription>
            </Alert>
          )}
          <Button 
            onClick={saveSettings} 
            disabled={!hasChanges}
            className="flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>Save Changes</span>
          </Button>
          <Button 
            onClick={handleLogout}
            variant="outline"
            className="flex items-center space-x-2 text-red-600 hover:text-red-700 hover:bg-red-50"
          >
            <LogOut className="h-4 w-4" />
            <span>Logout</span>
          </Button>
        </div>
      </div>

      {/* Theme Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sun className="h-5 w-5" />
            <span>Appearance</span>
          </CardTitle>
          <CardDescription>Customize the appearance of the application</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Theme</Label>
            <div className="flex space-x-2">
              <Button
                variant={theme === 'light' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTheme('light')}
                className="flex items-center space-x-2"
              >
                <Sun className="h-4 w-4" />
                <span>Light</span>
              </Button>
              <Button
                variant={theme === 'dark' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTheme('dark')}
                className="flex items-center space-x-2"
              >
                <Moon className="h-4 w-4" />
                <span>Dark</span>
              </Button>
              <Button
                variant={theme === 'system' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTheme('system')}
                className="flex items-center space-x-2"
              >
                <Monitor className="h-4 w-4" />
                <span>System</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* General Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <SettingsIcon className="h-5 w-5" />
            <span>General</span>
          </CardTitle>
          <CardDescription>Basic application settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="auto-connect">Auto-connect to agents</Label>
              <Switch
                id="auto-connect"
                checked={settings.general.autoConnect}
                onCheckedChange={(checked) => updateSetting('general', 'autoConnect', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="start-minimized">Start minimized</Label>
              <Switch
                id="start-minimized"
                checked={settings.general.startMinimized}
                onCheckedChange={(checked) => updateSetting('general', 'startMinimized', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="enable-tray">Enable system tray</Label>
              <Switch
                id="enable-tray"
                checked={settings.general.enableTray}
                onCheckedChange={(checked) => updateSetting('general', 'enableTray', checked)}
              />
            </div>
          </div>
          
          <Separator />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Language</Label>
              <Select value={settings.general.language} onValueChange={(value) => updateSetting('general', 'language', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">English</SelectItem>
                  <SelectItem value="es">Spanish</SelectItem>
                  <SelectItem value="fr">French</SelectItem>
                  <SelectItem value="de">German</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Update frequency</Label>
              <Select value={settings.general.updateFrequency} onValueChange={(value) => updateSetting('general', 'updateFrequency', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="5m">5 minutes</SelectItem>
                  <SelectItem value="15m">15 minutes</SelectItem>
                  <SelectItem value="1h">1 hour</SelectItem>
                  <SelectItem value="6h">6 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Bell className="h-5 w-5" />
            <span>Notifications</span>
          </CardTitle>
          <CardDescription>Control when and how you receive notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="agent-connect">Agent connections</Label>
              <Switch
                id="agent-connect"
                checked={settings.notifications.agentConnect}
                onCheckedChange={(checked) => updateSetting('notifications', 'agentConnect', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="agent-disconnect">Agent disconnections</Label>
              <Switch
                id="agent-disconnect"
                checked={settings.notifications.agentDisconnect}
                onCheckedChange={(checked) => updateSetting('notifications', 'agentDisconnect', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="command-complete">Command completion</Label>
              <Switch
                id="command-complete"
                checked={settings.notifications.commandComplete}
                onCheckedChange={(checked) => updateSetting('notifications', 'commandComplete', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="errors">Error notifications</Label>
              <Switch
                id="errors"
                checked={settings.notifications.errors}
                onCheckedChange={(checked) => updateSetting('notifications', 'errors', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="sound">Sound notifications</Label>
              <Switch
                id="sound"
                checked={settings.notifications.sound}
                onCheckedChange={(checked) => updateSetting('notifications', 'sound', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="desktop">Desktop notifications</Label>
              <Switch
                id="desktop"
                checked={settings.notifications.desktop}
                onCheckedChange={(checked) => updateSetting('notifications', 'desktop', checked)}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Shield className="h-5 w-5" />
            <span>Security</span>
          </CardTitle>
          <CardDescription>Manage security and authentication settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Security settings affect all connected agents. Changes require restart.
            </AlertDescription>
          </Alert>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="encryption">Enable encryption</Label>
              <Switch
                id="encryption"
                checked={settings.security.encryption}
                onCheckedChange={(checked) => updateSetting('security', 'encryption', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="two-factor">Two-factor authentication</Label>
              <Switch
                id="two-factor"
                checked={settings.security.twoFactor}
                onCheckedChange={(checked) => updateSetting('security', 'twoFactor', checked)}
              />
            </div>
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="require-auth">Require authentication</Label>
              <Switch
                id="require-auth"
                checked={settings.security.requireAuth}
                onCheckedChange={(checked) => updateSetting('security', 'requireAuth', checked)}
              />
            </div>
          </div>
          
          <Separator />
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Session timeout</Label>
              <Select value={settings.security.sessionTimeout} onValueChange={(value) => updateSetting('security', 'sessionTimeout', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15m">15 minutes</SelectItem>
                  <SelectItem value="30m">30 minutes</SelectItem>
                  <SelectItem value="1h">1 hour</SelectItem>
                  <SelectItem value="4h">4 hours</SelectItem>
                  <SelectItem value="24h">24 hours</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-attempts">Max failed attempts</Label>
              <Input
                id="max-attempts"
                type="number"
                value={settings.security.maxFailedAttempts}
                onChange={(e) => updateSetting('security', 'maxFailedAttempts', parseInt(e.target.value))}
                min="1"
                max="10"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Network */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="h-5 w-5" />
            <span>Network</span>
          </CardTitle>
          <CardDescription>Configure network and connection settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="port">Server port</Label>
              <Input
                id="port"
                type="number"
                value={settings.network.port}
                onChange={(e) => updateSetting('network', 'port', parseInt(e.target.value))}
                min="1024"
                max="65535"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="max-connections">Max connections</Label>
              <Input
                id="max-connections"
                type="number"
                value={settings.network.maxConnections}
                onChange={(e) => updateSetting('network', 'maxConnections', parseInt(e.target.value))}
                min="1"
                max="1000"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="timeout">Connection timeout (s)</Label>
              <Input
                id="timeout"
                type="number"
                value={settings.network.timeout}
                onChange={(e) => updateSetting('network', 'timeout', parseInt(e.target.value))}
                min="5"
                max="300"
              />
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between space-x-2">
              <Label htmlFor="compression">Enable compression</Label>
              <Switch
                id="compression"
                checked={settings.network.compression}
                onCheckedChange={(checked) => updateSetting('network', 'compression', checked)}
              />
            </div>
            <div className="space-y-2">
              <Label>Buffer size</Label>
              <Select value={settings.network.bufferSize} onValueChange={(value) => updateSetting('network', 'bufferSize', value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="512KB">512 KB</SelectItem>
                  <SelectItem value="1MB">1 MB</SelectItem>
                  <SelectItem value="2MB">2 MB</SelectItem>
                  <SelectItem value="4MB">4 MB</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Data Management</CardTitle>
          <CardDescription>Import, export, and manage your settings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <Button onClick={exportSettings} variant="outline" className="flex items-center space-x-2">
              <Download className="h-4 w-4" />
              <span>Export Settings</span>
            </Button>
            <Button variant="outline" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Import Settings</span>
            </Button>
            <Button onClick={resetSettings} variant="outline" className="flex items-center space-x-2">
              <RefreshCw className="h-4 w-4" />
              <span>Reset to Defaults</span>
            </Button>
            <Button variant="destructive" className="flex items-center space-x-2">
              <Trash2 className="h-4 w-4" />
              <span>Clear All Data</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}