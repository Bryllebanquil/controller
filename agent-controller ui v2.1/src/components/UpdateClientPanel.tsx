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
import apiClient from "../services/api";

type MonacoEditorProps = {
  height: string;
  defaultLanguage: string;
  theme: string;
  value: string;
  onChange: (v?: string) => void;
  options?: Record<string, any>;
};

function MonacoEditor({ height, defaultLanguage, theme, value, onChange }: MonacoEditorProps) {
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
  const { agents, selectedAgent, setSelectedAgent, previewFile, uploadFile, socket, sendCommand, connected, getLastFilePath } = useSocket();
  const { theme } = useTheme();
  const [agentId, setAgentId] = useState<string | null>(selectedAgent);
  const [filePath, setFilePath] = useState<string>("client.py");
  const [code, setCode] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [tab, setTab] = useState<string>(() => {
    try { return localStorage.getItem('nch:tab:update_client') || 'editor'; } catch { return 'editor'; }
  });
  const [debugRunning, setDebugRunning] = useState<boolean>(false);
  const [debugOutput, setDebugOutput] = useState<string[]>([]);
  const [latest, setLatest] = useState<{ version?: string; sha256?: string; last_push?: string; download_url?: string; size?: number } | null>(null);
  const [userEdited, setUserEdited] = useState<boolean>(false);
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
    if (!agentId) return;
    if (filePath && filePath.trim() && filePath.trim() !== 'client.py') return;
    try {
      const last = getLastFilePath(agentId) || '/';
      const sep = last.includes('\\') || /^[a-zA-Z]:/.test(last) ? '\\' : '/';
      const next = last.endsWith(sep) ? `${last}client.py` : `${last}${sep}client.py`;
      setFilePath(next);
    } catch {}
  }, [agentId]);
  useEffect(() => {
    try { localStorage.setItem('nch:tab:update_client', tab); } catch {}
  }, [tab]);

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
        setUserEdited(false);
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

  useEffect(() => {
    let mounted = true;
    (async () => {
      const res = await apiClient.getUpdaterLatest();
      if (res?.success && res.data) {
        if (!mounted) return;
        const d: any = res.data;
        setLatest({ version: d.version, sha256: d.sha256, last_push: d.last_push, download_url: d.download_url, size: d.size });
      }
    })();
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    try {
      if (userEdited) return;
      const cached = localStorage.getItem('updater_code') || '';
      const cachedSha = localStorage.getItem('updater_sha256') || localStorage.getItem('updater_md5') || '';
      if (cached && !code) {
        setCode(cached);
      }
      if (cached && latest?.sha256 && cachedSha === (latest.sha256 || '') && !code) {
        setCode(cached);
      }
    } catch {}
  }, [latest, userEdited]);

  useEffect(() => {
    (async () => {
      if (!latest) return;
      if (userEdited) return;
      if (code && code.trim().length > 0) return;
      const url = latest.download_url || '';
      if (!url) return;
      try {
        const r = await fetch(url);
        const t = await r.text();
        if (t && t.trim()) {
          setUserEdited(false);
          setCode(t);
          try {
            localStorage.setItem('updater_code', t);
            if (latest.sha256) {
              localStorage.setItem('updater_sha256', latest.sha256);
            } else if ((latest as any)?.md5) {
              localStorage.setItem('updater_md5', (latest as any).md5);
            }
          } catch {}
        }
      } catch {}
    })();
  }, [latest, code, userEdited]);

  useEffect(() => {
    const onChunk = (event: any) => {
      const data = event?.detail;
      if (!data) return;
      const req = previewRequestRef.current;
      if (!req) return;
      const id = String(data?.download_id || "");
      if (!id.startsWith("preview_")) return;
      const aid = String(data?.agent_id || "");
      if (req.agentId && aid && aid !== req.agentId) return;
      if (typeof data?.error === "string" && data.error) {
        setLoading(false);
        toast.error(data.error);
      }
    };
    window.addEventListener("file_download_chunk", onChunk);
    return () => {
      window.removeEventListener("file_download_chunk", onChunk);
    };
  }, []);

  useEffect(() => {
    const onOpen = (e: any) => {
      const d = e?.detail || {};
      const aid = typeof d?.agentId === 'string' ? d.agentId : agentId;
      const path = typeof d?.path === 'string' ? d.path : filePath;
      if (aid) {
        setAgentId(aid);
        setSelectedAgent(aid);
      }
      if (path) setFilePath(path);
      setTimeout(() => handleLoadCode(), 50);
    };
    window.addEventListener('open_in_updater', onOpen);
    return () => {
      window.removeEventListener('open_in_updater', onOpen);
    };
  }, [agentId, filePath]);

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
    setTimeout(async () => {
      if (!code.trim()) {
        try {
          const url = latest?.download_url || "";
          if (url) {
            const r = await fetch(url);
            const t = await r.text();
            if (t && t.trim()) {
              setCode(t);
              toast.info("Loaded controller copy of client.py");
              return;
            }
          }
        } catch {}
        toast.error("Preview not received. Try full path like C:/Users/YourName/Desktop/client.py");
      }
    }, 2000);
  };

  const handleFind = async () => {
    if (!agentId || !connected) {
      toast.error("No agent connected");
      return;
    }
    setTab("debugger");
    setDebugRunning(true);
    setDebugOutput([]);
    const cmd = `powershell -NoProfile -Command "(Get-ChildItem -Path C:\\ -Filter client.py -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName)"`;
    sendCommand(agentId, cmd);
    const startedAt = Date.now();
    const timer = setInterval(() => {
      const out = debugOutput.join("\\n");
      const m = out.match(/([A-Za-z]:\\\\[^\\n]*client\\.py)/i);
      if (m && m[1]) {
        clearInterval(timer);
        setDebugRunning(false);
        setFilePath(m[1]);
        setTab("editor");
        setTimeout(() => handleLoadCode(), 200);
      } else if (Date.now() - startedAt > 8000) {
        clearInterval(timer);
        setDebugRunning(false);
        toast.error("Auto locate failed");
      }
    }, 500);
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

  const handlePublishUpdater = async () => {
    if (!code.trim()) {
      toast.error("No code to publish");
      return;
    }
    const res = await apiClient.pushUpdater(code);
    if (res?.success && res.data) {
      const d: any = res.data;
      setLatest({ version: d.version, sha256: d.sha256, last_push: d.last_push });
      try {
        localStorage.setItem('updater_code', code);
        if (d.sha256) {
          localStorage.setItem('updater_sha256', d.sha256);
        } else if (d.md5) {
          localStorage.setItem('updater_md5', d.md5);
        }
      } catch {}
      toast.success("Updater state updated");
    } else {
      toast.error(res?.error || "Failed to publish updater");
    }
  };
  // Removed "Update Agent" and "Push All" actions per request

  return (
    <div className="h-[calc(100vh-3rem)] flex flex-col border rounded-md overflow-hidden bg-background shadow-sm">
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
               <Button size="sm" variant="ghost" className="h-8 px-2 text-xs" onClick={handleFind} disabled={!agentId || loading}>
                 Find
               </Button>
           </div>
           
           <Badge variant={connected ? "default" : "secondary"} className="text-[10px] h-5">{connected ? "Connected" : "Offline"}</Badge>
        </div>

        <div className="flex flex-wrap items-center gap-2">
           <Button size="sm" variant="outline" className="h-8 text-xs w-full sm:w-auto" onClick={handleDebug} disabled={!agentId || debugRunning}>
              {debugRunning ? "Running..." : "Debug"}
           </Button>
           <Button size="sm" className="h-8 text-xs w-full sm:w-auto" onClick={handleUpdateSelected} disabled={loading || !agentId || !code.trim()}>
              Push to {selectedAgentName}
           </Button>
           <Button size="sm" variant="secondary" className="h-8 text-xs w-full sm:w-auto" onClick={handlePublishUpdater} disabled={!code.trim()}>
              Publish Updater
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
                <div className="relative h-[500px] overflow-auto">
                   <MonacoEditor
                     height="500px"
                     defaultLanguage="python"
                     theme={monacoTheme}
                     value={code}
                     onChange={(v?: string) => { setUserEdited(true); setCode(v || ""); }}
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
                <div className="border-t px-4 py-2 text-xs flex items-center gap-4">
                  <span className="opacity-70">Last Push:</span>
                  <span className="font-mono">{latest?.last_push || "—"}</span>
                  <span className="opacity-70">Version:</span>
                  <span className="font-mono">{latest?.version || "—"}</span>
                  <span className="opacity-70">SHA256:</span>
                  <span className="font-mono">{latest?.sha256 || "—"}</span>
                  <span className="ml-auto flex items-center gap-2" />
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
