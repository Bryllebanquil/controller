import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { useSocket } from './SocketProvider';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Switch } from './ui/switch';
import { 
  Terminal, 
  Send, 
  History, 
  Play, 
  Square, 
  Copy,
  Download,
  Trash2,
  PowerOff,
  RefreshCw
} from 'lucide-react';

interface CommandPanelProps {
  agentId: string | null;
}

const quickCommands = [
  { label: 'System Info', command: 'systeminfo', icon: RefreshCw },
  { label: 'List Processes', command: 'tasklist', icon: Terminal },
  { label: 'Network Config', command: 'ipconfig /all', icon: RefreshCw },
  { label: 'Directory Listing', command: 'dir', icon: Terminal },
  { label: 'Environment Variables', command: 'set', icon: Terminal },
  { label: 'System Restart', command: 'shutdown /r /t 0', icon: PowerOff, variant: 'destructive' },
];

const commandHistory = [
  { id: 1, command: 'systeminfo', output: 'Host Name: WIN-DESKTOP-01\nOS Name: Microsoft Windows 11...', timestamp: new Date(), success: true },
  { id: 2, command: 'dir C:\\', output: 'Volume in drive C has no label.\nDirectory of C:\\\n\n...', timestamp: new Date(), success: true },
  { id: 3, command: 'ipconfig', output: 'Windows IP Configuration\n\nEthernet adapter...', timestamp: new Date(), success: true },
  { id: 4, command: 'invalid-command', output: 'Command not recognized', timestamp: new Date(), success: false },
];

export function CommandPanel({ agentId }: CommandPanelProps) {
  const { sendCommand, commandOutput } = useSocket();
  const [command, setCommand] = useState('');
  const [output, setOutput] = useState('');
  const [isExecuting, setIsExecuting] = useState(false);
  const [history, setHistory] = useState(commandHistory);
  const [showAgentTag, setShowAgentTag] = useState(true);
  const [currentCommandId, setCurrentCommandId] = useState<number | null>(null);
  const endTimerRef = useRef<number | null>(null);
  const outputRef = useRef<HTMLPreElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [innerTab, setInnerTab] = useState<string>(() => {
    try { return localStorage.getItem('nch:tab:cmd') || 'execute'; } catch { return 'execute'; }
  });

  const applyChunk = (prev: string, chunk: string) => {
    const normalized = chunk.replace(/\r\n/g, '\n');
    if (!normalized.includes('\r')) return prev + normalized;
    const parts = normalized.split('\r');
    let acc = prev + parts[0];
    for (let i = 1; i < parts.length; i++) {
      const lastNewline = acc.lastIndexOf('\n');
      acc = (lastNewline >= 0 ? acc.slice(0, lastNewline + 1) : '') + parts[i];
    }
    return acc;
  };

  const executeCommand = async (cmd?: string) => {
    const commandToExecute = cmd || command;
    if (!commandToExecute.trim() || !agentId) return;

    setIsExecuting(true);
    setOutput('');

    try {
      sendCommand(agentId, commandToExecute);
      const entry = {
        id: Date.now(),
        command: commandToExecute,
        output: '',
        timestamp: new Date(),
        success: true
      };
      setCurrentCommandId(entry.id);
      setHistory(prev => [entry, ...prev]);
      
    } catch (error) {
      console.error('Error executing command:', error);
      setOutput(prev => prev + `Error: ${error}\n`);
      setIsExecuting(false);
    }
    
    if (!cmd) setCommand('');
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      executeCommand();
    }
  };

  const copyOutput = () => {
    navigator.clipboard.writeText(output);
  };

  const clearOutput = () => {
    setOutput('');
  };

  useEffect(() => {
    if (commandOutput.length > 0) {
      const latestOutput = commandOutput[commandOutput.length - 1];
      const processed = showAgentTag ? latestOutput : latestOutput.replace(/^\[[^\]]+\]\s*/, '');
      setOutput(prev => applyChunk(prev, processed));
      if (currentCommandId !== null) {
        setHistory(prev =>
          prev.map(e => e.id === currentCommandId ? { ...e, output: applyChunk(e.output, processed) } : e)
        );
      }
      if (endTimerRef.current) {
        window.clearTimeout(endTimerRef.current);
      }
      endTimerRef.current = window.setTimeout(() => {
        setIsExecuting(false);
      }, 800);
    }
  }, [commandOutput, showAgentTag, currentCommandId]);

  useEffect(() => {
    const viewport = outputRef.current?.parentElement;
    if (!viewport) return;
    const onScroll = () => {
      const nearBottom = viewport.scrollTop + viewport.clientHeight >= viewport.scrollHeight - 8;
      setAutoScroll(nearBottom);
    };
    viewport.addEventListener('scroll', onScroll, { passive: true } as any);
    return () => {
      viewport.removeEventListener('scroll', onScroll);
    };
  }, []);

  useEffect(() => {
    if (!autoScroll) return;
    const viewport = outputRef.current?.parentElement;
    if (viewport) {
      viewport.scrollTop = viewport.scrollHeight;
    }
  }, [output, autoScroll]);
  useEffect(() => {
    try { localStorage.setItem('nch:tab:cmd', innerTab); } catch {}
  }, [innerTab]);

  return (
    <div className="space-y-6">
      {/* Quick Commands */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm flex items-center">
            <Terminal className="h-4 w-4 mr-2" />
            Quick Commands
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {quickCommands.map((cmd, index) => {
              const Icon = cmd.icon;
              return (
                <Button
                  key={index}
                  variant={cmd.variant as any || "outline"}
                  size="sm"
                  className="justify-start h-auto p-3"
                  onClick={() => executeCommand(cmd.command)}
                  disabled={!agentId || isExecuting}
                >
                  <Icon className="h-3 w-3 mr-2" />
                  <div className="text-left">
                    <div className="text-xs font-medium">{cmd.label}</div>
                    <div className="text-xs text-muted-foreground truncate">{cmd.command}</div>
                  </div>
                </Button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      <Tabs value={innerTab} onValueChange={setInnerTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="execute">Terminal</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="execute" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm flex items-center">
                  <Terminal className="h-4 w-4 mr-2" />
                  PowerShell Terminal
                </CardTitle>
                <div className="flex items-center gap-3">
                  {agentId && (
                    <Badge variant="outline">{agentId.substring(0, 8)}</Badge>
                  )}
                  <div className="flex items-center gap-2">
                    <span className="text-xs">Show Agent Tag</span>
                    <Switch checked={showAgentTag} onCheckedChange={setShowAgentTag} />
                  </div>
                  {isExecuting && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <RefreshCw className="h-3 w-3 animate-spin" />
                      Executing…
                    </div>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              <ScrollArea className="min-h-[220px] sm:min-h-[280px] max-h-[60vh] sm:max-h-[520px] rounded">
                <pre
                  className="bg-[#012456] text-[#e5e5e5] p-4 rounded font-mono text-sm overflow-x-auto break-normal"
                  style={{ whiteSpace: 'pre', fontFamily: 'Consolas, \"Courier New\", monospace', tabSize: 8 as any }}
                  ref={outputRef}
                >
                  {output}
                </pre>
              </ScrollArea>
              <div className="flex items-center gap-2 bg-[#012456] p-2 rounded flex-wrap sm:flex-nowrap">
                <span className="font-mono text-sm text-[#e5e5e5] w-full sm:w-auto">{'PS C:\\>'}</span>
                <Input
                  placeholder="Type a command and press Enter"
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={!agentId || isExecuting}
                  className="font-mono text-sm bg-transparent border-none text-[#e5e5e5] focus-visible:ring-0 focus-visible:outline-none flex-1 min-w-0"
                />
                <Button 
                  onClick={() => executeCommand()}
                  disabled={!agentId || !command.trim() || isExecuting}
                  size="sm"
                  variant="secondary"
                  className="bg-[#0a2a6b] text-[#e5e5e5] hover:bg-[#0d337f]"
                >
                  {isExecuting ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
                <Button variant="ghost" size="sm" onClick={copyOutput} disabled={!output} className="sm:ml-0">
                  <Copy className="h-4 w-4 text-[#e5e5e5]" />
                </Button>
                <Button variant="ghost" size="sm" onClick={clearOutput} disabled={!output}>
                  <Trash2 className="h-4 w-4 text-[#e5e5e5]" />
                </Button>
                <Button variant="ghost" size="sm" disabled={!output}>
                  <Download className="h-4 w-4 text-[#e5e5e5]" />
                </Button>
              </div>
              {!agentId && (
                <div className="text-center text-muted-foreground text-sm py-2">
                  Select an agent to execute commands
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Command History</CardTitle>
                <Button variant="ghost" size="sm">
                  <Trash2 className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {history.map((entry) => (
                    <div key={entry.id} className="border rounded p-3 space-y-2">
                      <div className="flex items-center justify-between">
                        <code className="text-sm bg-muted px-2 py-1 rounded">{entry.command}</code>
                        <div className="flex items-center space-x-2">
                          <Badge variant={entry.success ? "default" : "destructive"}>
                            {entry.success ? "Success" : "Failed"}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {entry.timestamp.toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                      <div className="text-xs text-muted-foreground bg-muted p-2 rounded font-mono">
                        {entry.output.substring(0, 100)}
                        {entry.output.length > 100 && '...'}
                      </div>
                      <div className="flex justify-end space-x-1">
                        <Button variant="ghost" size="sm" onClick={() => setCommand(entry.command)}>
                          <Play className="h-3 w-3 mr-1" />
                          Run Again
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => navigator.clipboard.writeText(entry.output)}>
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
