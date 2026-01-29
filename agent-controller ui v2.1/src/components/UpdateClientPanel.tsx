import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { ScrollArea } from "./ui/scroll-area";
import { toast } from "sonner";
import { useSocket } from "./SocketProvider";
import { useTheme } from "./ThemeProvider";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";

type MonacoEditorProps = {
  height: string;
  defaultLanguage: string;
  theme: string;
  value: string;
  onChange: (v?: string) => void;
  options?: Record<string, any>;
};

function MonacoEditor({ height, defaultLanguage, theme, value, onChange, options }: MonacoEditorProps) {
  const [Editor, setEditor] = useState<any>(null);
  useEffect(() => {
    let mounted = true;
    const allowsEval = (() => {
      try {
        // If CSP blocks eval/new Function, this will throw
        // We avoid loading Monaco in that case
        // eslint-disable-next-line no-new-func
        const f = new Function("return 1");
        return typeof f === "function" && f() === 1;
      } catch {
        return false;
      }
    })();
    if (!allowsEval) {
      setEditor(null);
      return () => { mounted = false; };
    }
    const MOD: any = /* @vite-ignore */ "@monaco-editor/react";
    import(MOD).then((mod) => {
      if (mounted) setEditor(mod.default);
    }).catch(() => {
      setEditor(null);
    });
    return () => { mounted = false; };
  }, []);
  if (Editor) {
    return (
      <Editor
        height={height}
        defaultLanguage={defaultLanguage}
        theme={theme}
        value={value}
        onChange={(v?: string) => onChange(v)}
        options={options}
      />
    );
  }
  return (
    <textarea
      style={{ height, width: "100%" }}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full h-full p-2 border rounded font-mono text-sm bg-background text-foreground"
    />
  );
}

export function UpdateClientPanel() {
  const { agents, selectedAgent, setSelectedAgent, previewFile, uploadFile, socket, sendCommand, connected } = useSocket();
  const { theme } = useTheme();
  const [agentId, setAgentId] = useState<string | null>(selectedAgent);
  const [filePath, setFilePath] = useState<string>("client.py");
  const [code, setCode] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [tab, setTab] = useState<string>("editor");
  const [debugRunning, setDebugRunning] = useState<boolean>(false);
  const [debugOutput, setDebugOutput] = useState<string[]>([]);
  const [bulkUpdating, setBulkUpdating] = useState<boolean>(false);
  const previewRequestRef = useRef<{ agentId: string; filePath: string } | null>(null);
  
  const selectedAgentName = agents.find(a => a.id === agentId)?.name || "Agent";

  const monacoTheme = useMemo(() => {
    if (theme === "dark") return "vs-dark";
    if (theme === "light") return "vs-light";
    const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
    return prefersDark ? "vs-dark" : "vs-light";
  }, [theme]);

  useEffect(() => {
    if (!agentId && agents.length > 0) {
        const online = agents.find(a => a.status === "online");
        if (online) setAgentId(online.id);
    }
  }, [agents, agentId]);

  useEffect(() => {
    const handlePreviewReady = async (event: any) => {
      const data = event?.detail;
      if (!data) return;
      const req = previewRequestRef.current;
      if (!req) return;
      try {
        let text = '';
        const payload = typeof data?.chunk === 'string' ? data.chunk : null;
        if (payload) {
          const base = payload.includes(',') ? payload.split(',', 1)[1] : payload;
          const bin = atob(base);
          const bytes = new Uint8Array(bin.length);
          for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
          const decoder = new TextDecoder('utf-8');
          text = decoder.decode(bytes);
        } else if (data.blob && typeof data.blob.text === 'function') {
          text = await data.blob.text();
        } else if (data.url) {
          const res = await fetch(data.url);
          text = await res.text();
        }
        setCode(text);
        toast.success(`Loaded ${data.filename || req.filePath}`);
      } catch (e: any) {
        toast.error(e?.message || "Failed to load file content");
      }
    };
    window.addEventListener("file_preview_ready", handlePreviewReady);
    return () => {
      window.removeEventListener("file_preview_ready", handlePreviewReady);
    };
  }, []);

  useEffect(() => {
    if (!socket) return;
    const handler = (data: any) => {
      if (!data || typeof data !== "object") return;
      const aid = String(data.agent_id || "");
      if (agentId && aid === agentId) {
        const text = typeof data.formatted_text === "string" ? data.formatted_text : (typeof data.output === "string" ? data.output : "");
        if (text) {
          setDebugOutput(prev => [...prev.slice(-199), text]);
        }
      }
    };
    socket.on("command_result", handler);
    return () => {
      try { socket.off("command_result", handler); } catch {}
    };
  }, [socket, agentId]);

  const normalizeDestinationDir = (destinationPath: string, filename: string): string => {
    const raw = (destinationPath || "").trim();
    if (!raw) return "";
    const lower = raw.toLowerCase();
    const filenameLower = filename.toLowerCase();
    if (lower.endsWith(`/${filenameLower}`) || lower.endsWith(`\\${filenameLower}`)) {
      return raw.slice(0, raw.length - filename.length - 1);
    }
    return raw;
  };

  const sanitizeFilename = (path: string): string => {
    const raw = String(path || '').trim();
    const s = raw.replace(/^[/\\]+/, '');
    return s || 'client.py';
  };

  const handleLoadCode = () => {
    if (!agentId || !connected) {
      toast.error("No agent connected");
      return;
    }
    setLoading(true);
    previewRequestRef.current = { agentId, filePath };
    const fname = sanitizeFilename(filePath);
    previewFile?.(agentId, fname);
    setTimeout(() => setLoading(false), 800);
    setTimeout(() => {
      if (!code.trim()) {
        toast.error("Preview not received. Try full path like C:/Users/YourName/Desktop/client.py");
      }
    }, 2500);
  };

  const handleDebug = async () => {
    if (!agentId || !connected) {
      toast.error("No agent connected");
      return;
    }
    const dir = normalizeDestinationDir(filePath, "client_debug.py");
    const file = new File([code], "client_debug.py", { type: "text/x-python" });
    setDebugRunning(true);
    setDebugOutput([]);
    uploadFile(agentId, file, dir);
    const target = dir ? `${dir}${dir.endsWith("/") || dir.endsWith("\\") ? "" : "/"}client_debug.py` : "client_debug.py";
    setTimeout(() => {
      sendCommand(agentId, `python -m py_compile "${target}"`);
    }, 500);
    setTimeout(() => setDebugRunning(false), 2000);
    setTab("debugger");
  };

  const handleUpdateSelected = async () => {
    if (!agentId || !connected) {
      toast.error("No agent connected");
      return;
    }
    setLoading(true);
    const dir = normalizeDestinationDir(filePath, "client.py");
    const file = new File([code], "client.py", { type: "text/x-python" });
    uploadFile(agentId, file, dir);
    setLoading(false);
    toast.success(`Pushed update to agent`);
  };

  const handleUpdateAll = async () => {
    if (!connected) {
      toast.error("Not connected");
      return;
    }
    const onlineAgents = agents.filter(a => a.status === "online");
    if (onlineAgents.length === 0) {
      toast.error("No online agents");
      return;
    }
    setBulkUpdating(true);
    const dir = normalizeDestinationDir(filePath, "client.py");
    const file = new File([code], "client.py", { type: "text/x-python" });
    for (const a of onlineAgents) {
      uploadFile(a.id, file, dir);
      await new Promise(r => setTimeout(r, 200));
    }
    setBulkUpdating(false);
    toast.success(`Pushed updates to ${onlineAgents.length} agent(s)`);
  };

  return (
    <div className="h-[calc(100vh-6rem)] flex flex-col border rounded-md overflow-hidden bg-background shadow-sm">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-muted/20 shrink-0">
        <div className="flex items-center gap-4">
           <Select 
               value={agentId || ""} 
               onValueChange={(v) => {
                   setAgentId(v);
                   setSelectedAgent(v);
               }}
           >
             <SelectTrigger className="h-8 w-[200px] text-xs">
               <SelectValue placeholder="Select Agent" />
             </SelectTrigger>
             <SelectContent>
               {agents.map(a => (
                 <SelectItem key={a.id} value={a.id}>
                   {a.name} ({a.status})
                 </SelectItem>
               ))}
             </SelectContent>
           </Select>
           
           <div className="flex items-center gap-2">
               <Input 
                   className="h-8 w-[250px] text-xs font-mono" 
                   value={filePath} 
                   onChange={(e) => setFilePath(e.target.value)} 
                   placeholder="client.py" 
               />
               <Button size="sm" variant="ghost" className="h-8 px-2 text-xs" onClick={handleLoadCode} disabled={!agentId || loading}>
                 Load
               </Button>
           </div>
           
           <Badge variant={connected ? "default" : "secondary"} className="text-[10px] h-5">{connected ? "Connected" : "Offline"}</Badge>
        </div>

        <div className="flex items-center gap-2">
           <Button size="sm" variant="outline" className="h-8 text-xs" onClick={handleDebug} disabled={!agentId || debugRunning}>
              {debugRunning ? "Running..." : "Debug"}
           </Button>
           <Button size="sm" className="h-8 text-xs" onClick={handleUpdateSelected} disabled={loading || !agentId || !code.trim()}>
              Push to {selectedAgentName}
           </Button>
           <Button size="sm" variant="destructive" className="h-8 text-xs" onClick={handleUpdateAll} disabled={bulkUpdating || !code.trim()}>
              Push All
           </Button>
        </div>
      </div>

      {/* Editor Area */}
      <div className="flex-1 flex min-h-0 relative">
          <Tabs value={tab} onValueChange={setTab} className="flex-1 flex flex-col">
             <div className="border-b bg-muted/10 shrink-0">
                <TabsList className="h-8 w-auto bg-transparent p-0 justify-start">
                   <TabsTrigger value="editor" className="data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-8 px-4 text-xs">Code</TabsTrigger>
                   <TabsTrigger value="debugger" className="data-[state=active]:bg-background data-[state=active]:border-b-2 data-[state=active]:border-primary rounded-none h-8 px-4 text-xs">Output</TabsTrigger>
                </TabsList>
             </div>
             
             <TabsContent value="editor" className="flex-1 flex flex-col min-h-0 m-0 p-0 data-[state=active]:flex relative">
                <div className="flex-1 relative">
                   <MonacoEditor
                     height="100%"
                     defaultLanguage="python"
                     theme={monacoTheme}
                     value={code}
                     onChange={(v?: string) => setCode(v || "")}
                     options={{
                       fontSize: 14,
                       minimap: { enabled: true },
                       scrollBeyondLastLine: false,
                       automaticLayout: true,
                       wordWrap: "on",
                       padding: { top: 16 }
                     }}
                   />
                </div>
             </TabsContent>
             
             <TabsContent value="debugger" className="flex-1 flex flex-col min-h-0 m-0 p-0 data-[state=active]:flex">
                <ScrollArea className="flex-1 bg-black/90 text-green-400 font-mono text-xs p-4">
                   <pre>{debugOutput.join("\n") || "No output yet"}</pre>
                </ScrollArea>
             </TabsContent>
          </Tabs>
      </div>
    </div>
  );
}
