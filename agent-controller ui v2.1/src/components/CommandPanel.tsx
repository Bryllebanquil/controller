import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { useSocket } from './SocketProvider';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
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

  const executeCommand = async (cmd?: string) => {
    const commandToExecute = cmd || command;
    if (!commandToExecute.trim() || !agentId) return;

    setIsExecuting(true);
    
    // Add the command to output immediately (like a real terminal)
    const commandLine = `$ ${commandToExecute}`;
    setOutput(prev => prev + (prev ? '\n' : '') + commandLine + '\n');
    
    try {
      sendCommand(agentId, commandToExecute);
      const entry = {
        id: Date.now(),
        command: commandToExecute,
        output: '',
        timestamp: new Date(),
        success: true
      };
      setHistory(prev => [entry, ...prev]);
      
      // Don't reset isExecuting here - let the command result handler do it
      // This ensures we show "Executing..." until we get the actual result
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
    // Update output window as new lines come in
    console.log('🔍 CommandPanel: commandOutput changed, length:', commandOutput.length);
    console.log('🔍 CommandPanel: commandOutput array:', commandOutput);
    
    if (commandOutput.length > 0) {
      // Get the latest output line
      const latestOutput = commandOutput[commandOutput.length - 1];
      console.log('🔍 CommandPanel: latest output:', latestOutput);
      
      if (latestOutput && latestOutput.trim()) {
        // Add the latest output to the display
        setOutput(prev => {
          const newOutput = prev + (prev.endsWith('\n') ? '' : '\n') + latestOutput + '\n';
          console.log('🔍 CommandPanel: setting new output:', newOutput);
          return newOutput;
        });
      }
      
      // Reset executing state when we receive command output
      setIsExecuting(false);
    }
  }, [commandOutput]);

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

      <Tabs defaultValue="execute" className="space-y-4">
        <TabsList>
          <TabsTrigger value="execute">Execute</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="execute" className="space-y-4">
          {/* Command Input */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-sm">Command Execution</CardTitle>
                {agentId && (
                  <Badge variant="outline">{agentId.substring(0, 8)}</Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Enter command..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={!agentId || isExecuting}
                  className="font-mono"
                />
                <Button 
                  onClick={() => executeCommand()}
                  disabled={!agentId || !command.trim() || isExecuting}
                  size="sm"
                >
                  {isExecuting ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </div>

              {!agentId && (
                <div className="text-center text-muted-foreground text-sm py-4">
                  Select an agent to execute commands
                </div>
              )}
            </CardContent>
          </Card>

          {/* Command Output */}
          {agentId && (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm">Output</CardTitle>
                  <div className="flex items-center space-x-2">
                    <Button variant="ghost" size="sm" onClick={copyOutput} disabled={!output}>
                      <Copy className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" onClick={clearOutput} disabled={!output}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                    <Button variant="ghost" size="sm" disabled={!output}>
                      <Download className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="bg-black text-green-400 p-4 rounded font-mono text-xs min-h-[200px] max-h-[400px] overflow-auto whitespace-pre-wrap">
                  {output || 'No output yet. Execute a command to see results.'}
                  {isExecuting && (
                    <div className="text-yellow-400 animate-pulse">
                      Executing command... <span className="animate-pulse">▋</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
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