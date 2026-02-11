import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { 
  Cpu, 
  HardDrive, 
  Monitor, 
  MemoryStick, 
  Network, 
  Activity,
  Zap,
  Usb,
  Settings,
  HardDrive as StorageIcon,
  Video,
  Headphones,
  Keyboard,
  Mouse,
  Wifi,
  Bluetooth,
  CircuitBoard
} from 'lucide-react';
import { useMemo, useState, useEffect } from 'react';
import { useSocket } from './SocketProvider';
import { Button } from './ui/button';
import { cn } from './ui/utils';
import { toast } from 'sonner';

interface HardwareInventoryProps {
  agentId: string | null;
}

interface HardwareInfo {
  cpu?: {
    name: string;
    cores: number;
    threads: number;
    frequency: number;
    architecture: string;
    vendor: string;
  };
  memory?: {
    total: number;
    available: number;
    used: number;
    type: string;
    speed: number;
  };
  storage?: Array<{
    name: string;
    size: number;
    type: string;
    interface: string;
    health: string;
  }>;
  gpu?: Array<{
    name: string;
    memory: number;
    driver: string;
    vendor: string;
  }>;
  network?: Array<{
    name: string;
    mac: string;
    ip: string;
    type: string;
  }>;
  peripherals?: Array<{
    name: string;
    type: string;
    vendor: string;
    connected: boolean;
  }>;
  motherboard?: {
    manufacturer: string;
    model: string;
    bios: string;
  };
}

export function HardwareInventory({ agentId }: HardwareInventoryProps) {
  const { sendCommand, socket } = useSocket();
  const [hardwareInfo, setHardwareInfo] = useState<HardwareInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchHardwareInfo = useMemo(() => async () => {
    if (!agentId) return;
    
    setIsLoading(true);
    try {
      sendCommand(agentId, 'Get-ComputerInfo');
      
      // Set up one-time listener for hardware info response
      let completed = false;
      const handleHardwareInfo = (data: any) => {
        try {
          const incomingAgentId = typeof data?.agentId === 'string' ? data.agentId : (typeof data?.agent_id === 'string' ? data.agent_id : '');
          if (incomingAgentId === agentId && data?.type === 'hardware_info') {
            completed = true;
            setHardwareInfo(data.hardware || null);
            setLastUpdate(new Date());
            setIsLoading(false);
            socket?.off('agent_response', handleHardwareInfo);
            toast.success('Hardware inventory updated');
          }
        } catch {}
      };
      
      socket?.on('agent_response', handleHardwareInfo);
      
      // Timeout after 10 seconds
      setTimeout(() => {
        socket?.off('agent_response', handleHardwareInfo);
        if (!completed) {
          setIsLoading(false);
          toast.error('Failed to fetch hardware information');
        }
      }, 10000);
      
    } catch (error) {
      console.error('Error fetching hardware info:', error);
      setIsLoading(false);
      toast.error('Error fetching hardware information');
    }
  }, [agentId, sendCommand, socket, isLoading]);

  

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatFrequency = (mhz: number): string => {
    if (mhz >= 1000) {
      return `${(mhz / 1000).toFixed(2)} GHz`;
    }
    return `${mhz} MHz`;
  };

  if (!agentId) {
    return (
      <Card className="h-[400px]">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Select an agent to view hardware inventory</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className="h-[400px]">
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-sm">Loading hardware information...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Hardware Inventory</h3>
          <p className="text-sm text-muted-foreground">
            {lastUpdate ? `Last updated: ${lastUpdate.toLocaleTimeString()}` : 'No data available'}
          </p>
        </div>
        <Button 
          onClick={fetchHardwareInfo} 
          disabled={isLoading}
          size="sm"
          variant="outline"
        >
          <Activity className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* CPU Information */}
      {hardwareInfo?.cpu && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <Cpu className="h-4 w-4 mr-2" />
              Processor
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Name:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.cpu.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Cores/Threads:</span>
                <span className="text-sm text-muted-foreground">
                  {hardwareInfo.cpu.cores} cores / {hardwareInfo.cpu.threads} threads
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Frequency:</span>
                <span className="text-sm text-muted-foreground">
                  {formatFrequency(hardwareInfo.cpu.frequency)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Architecture:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.cpu.architecture}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Vendor:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.cpu.vendor}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Memory Information */}
      {hardwareInfo?.memory && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <MemoryStick className="h-4 w-4 mr-2" />
              Memory (RAM)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Total:</span>
                <span className="text-sm text-muted-foreground">{formatBytes(hardwareInfo.memory.total)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Available:</span>
                <span className="text-sm text-muted-foreground">{formatBytes(hardwareInfo.memory.available)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Used:</span>
                <span className="text-sm text-muted-foreground">{formatBytes(hardwareInfo.memory.used)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Type:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.memory.type}</span>
              </div>
              {hardwareInfo.memory.speed > 0 && (
                <div className="flex justify-between">
                  <span className="text-sm font-medium">Speed:</span>
                  <span className="text-sm text-muted-foreground">{formatFrequency(hardwareInfo.memory.speed)}</span>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* GPU Information */}
      {hardwareInfo?.gpu && hardwareInfo.gpu.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <Video className="h-4 w-4 mr-2" />
              Graphics Cards ({hardwareInfo.gpu.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {hardwareInfo.gpu.map((gpu, index) => (
                <div key={index} className="border rounded-lg p-3 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Name:</span>
                    <span className="text-sm text-muted-foreground">{gpu.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Memory:</span>
                    <span className="text-sm text-muted-foreground">{formatBytes(gpu.memory)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Driver:</span>
                    <span className="text-sm text-muted-foreground">{gpu.driver}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Vendor:</span>
                    <span className="text-sm text-muted-foreground">{gpu.vendor}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Storage Information */}
      {hardwareInfo?.storage && hardwareInfo.storage.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <StorageIcon className="h-4 w-4 mr-2" />
              Storage Devices ({hardwareInfo.storage.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {hardwareInfo.storage.map((storage, index) => (
                <div key={index} className="border rounded-lg p-3 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Name:</span>
                    <span className="text-sm text-muted-foreground">{storage.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Size:</span>
                    <span className="text-sm text-muted-foreground">{formatBytes(storage.size)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Type:</span>
                    <span className="text-sm text-muted-foreground">{storage.type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Interface:</span>
                    <span className="text-sm text-muted-foreground">{storage.interface}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Health:</span>
                    <Badge 
                      variant={storage.health === 'Good' ? 'default' : 'destructive'}
                      className="text-xs"
                    >
                      {storage.health}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Network Information */}
      {hardwareInfo?.network && hardwareInfo.network.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <Network className="h-4 w-4 mr-2" />
              Network Interfaces ({hardwareInfo.network.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {hardwareInfo.network.map((net, index) => (
                <div key={index} className="border rounded-lg p-3 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Name:</span>
                    <span className="text-sm text-muted-foreground">{net.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">MAC:</span>
                    <span className="text-sm text-muted-foreground font-mono">{net.mac}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">IP:</span>
                    <span className="text-sm text-muted-foreground">{net.ip}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Type:</span>
                    <Badge variant="secondary" className="text-xs">{net.type}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Peripherals */}
      {hardwareInfo?.peripherals && hardwareInfo.peripherals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
              <Usb className="h-4 w-4 mr-2" />
              Peripherals ({hardwareInfo.peripherals.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {hardwareInfo.peripherals.map((peripheral, index) => (
                <div key={index} className="border rounded-lg p-3 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Name:</span>
                    <span className="text-sm text-muted-foreground">{peripheral.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Type:</span>
                    <Badge variant="secondary" className="text-xs">{peripheral.type}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Vendor:</span>
                    <span className="text-sm text-muted-foreground">{peripheral.vendor}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm font-medium">Status:</span>
                    <Badge 
                      variant={peripheral.connected ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {peripheral.connected ? 'Connected' : 'Disconnected'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Motherboard Information */}
      {hardwareInfo?.motherboard && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm flex items-center">
                <CircuitBoard className="h-4 w-4 mr-2" />
                Motherboard
              </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Manufacturer:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.motherboard.manufacturer}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Model:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.motherboard.model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">BIOS:</span>
                <span className="text-sm text-muted-foreground">{hardwareInfo.motherboard.bios}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Data Message */}
      {!hardwareInfo && !isLoading && (
        <Card className="h-[200px]">
          <CardContent className="flex items-center justify-center h-full">
            <div className="text-center text-muted-foreground">
              <Settings className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p className="text-sm">No hardware information available</p>
              <p className="text-xs mt-1">Click refresh to fetch data from agent</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
