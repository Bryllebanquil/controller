import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useSocket } from './SocketProvider';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Progress } from './ui/progress';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { API_BASE_URL } from '../services/api';
import { 
  Files, 
  Folder, 
  File, 
  Download, 
  Upload, 
  Trash2, 
  RefreshCw,
  Search,
  ArrowLeft,
  Home,
  HardDrive,
  Image,
  FileText,
  Archive,
  Video,
  Music,
  X
} from 'lucide-react';
import { toast } from 'sonner';

interface FileManagerProps {
  agentId: string | null;
}

interface FileItem {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified: Date;
  path: string;
  extension?: string;
}

const mockFiles: FileItem[] = [];

const getFileIcon = (item: FileItem) => {
  if (item.type === 'directory') return Folder;
  
  switch (item.extension) {
    case 'png':
    case 'jpg':
    case 'jpeg':
    case 'gif':
      return Image;
    case 'txt':
    case 'json':
    case 'md':
      return FileText;
    case 'zip':
    case 'rar':
    case '7z':
      return Archive;
    case 'mp4':
    case 'avi':
    case 'mkv':
      return Video;
    case 'mp3':
    case 'wav':
    case 'flac':
      return Music;
    default:
      return File;
  }
};

const formatFileSize = (bytes?: number) => {
  if (bytes === undefined || bytes === null || Number.isNaN(Number(bytes))) return '-';
  if (bytes === 0) return '0 B';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
};

export function FileManager({ agentId }: FileManagerProps) {
  const { uploadFile, downloadFile, socket, setLastActivity, getLastFilePath, setLastFilePath, agents } = useSocket();
  const [currentPath, setCurrentPath] = useState('/');
  const [pathInput, setPathInput] = useState('/');
  const [files, setFiles] = useState(mockFiles);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null);
  const [transferFileName, setTransferFileName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [previewKind, setPreviewKind] = useState<'image' | 'video' | 'pdf' | 'ppt' | 'gif' | null>(null);
  const [previewItems, setPreviewItems] = useState<FileItem[]>([]);
  const [previewIndex, setPreviewIndex] = useState<number>(0);
  const [previewErrorCount, setPreviewErrorCount] = useState<number>(0);
  const currentPathRef = useRef<string>('/');
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const previewVideoRef = useRef<HTMLVideoElement | null>(null);
  const previewVideoStartupTimerRef = useRef<number | null>(null);
  const previewSessionRef = useRef<number>(0);
  const previewVideoReadyRef = useRef<boolean>(false);
  const [previewVideoMode, setPreviewVideoMode] = useState<'normal' | 'faststart'>('normal');
  const lastRefreshRef = useRef<number>(0);
  const [fitMode, setFitMode] = useState<'contain' | 'cover' | 'fill'>('contain');
  const [dirSizes, setDirSizes] = useState<Record<string, number>>({});
  const [zipInProgress, setZipInProgress] = useState<{ dest?: string; friendly?: string } | null>(null);
  const [sortBy, setSortBy] = useState<'name' | 'size' | 'modified'>(() => {
    try { return (localStorage.getItem('fm:sortBy') as any) || 'name'; } catch { return 'name'; }
  });
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>(() => {
    try { return (localStorage.getItem('fm:sortOrder') as any) || 'asc'; } catch { return 'asc'; }
  });
  const psEncode = (s: string) => {
    const buf = new Uint8Array(s.length * 2);
    for (let i = 0; i < s.length; i++) {
      const code = s.charCodeAt(i);
      buf[i * 2] = code & 0xff;
      buf[i * 2 + 1] = code >> 8;
    }
    let bin = '';
    for (let i = 0; i < buf.length; i++) {
      bin += String.fromCharCode(buf[i]);
    }
    return btoa(bin);
  };

  const filteredFiles = useMemo(() => {
    const term = searchTerm.toLowerCase();
    const arr = files.filter(file => file.name.toLowerCase().includes(term));
    arr.sort((a, b) => {
      if (a.type !== b.type) return a.type === 'directory' ? -1 : 1;
      let cmp = 0;
      if (sortBy === 'name') {
        cmp = a.name.localeCompare(b.name, undefined, { sensitivity: 'base' });
      } else if (sortBy === 'size') {
        const as = typeof a.size === 'number' ? a.size! : -1;
        const bs = typeof b.size === 'number' ? b.size! : -1;
        cmp = as - bs;
      } else {
        const am = a.modified ? a.modified.getTime() : 0;
        const bm = b.modified ? b.modified.getTime() : 0;
        cmp = am - bm;
      }
      return sortOrder === 'desc' ? -cmp : cmp;
    });
    return arr;
  }, [files, searchTerm, sortBy, sortOrder]);
  useEffect(() => {
    try {
      localStorage.setItem('fm:sortBy', sortBy);
      localStorage.setItem('fm:sortOrder', sortOrder);
    } catch {}
  }, [sortBy, sortOrder]);

  const handleFileSelect = (filePath: string) => {
    setSelectedFiles(prev => 
      prev.includes(filePath) 
        ? prev.filter(f => f !== filePath)
        : [...prev, filePath]
    );
  };

  const getParentPath = (path: string) => {
    const trimmed = (path || '').trim();
    if (!trimmed || trimmed === '/' || trimmed === '\\') return '/';
    const normalized = trimmed.replace(/[\\\/]+$/, '');
    const lastSlash = normalized.lastIndexOf('/');
    const lastBackslash = normalized.lastIndexOf('\\');
    const idx = Math.max(lastSlash, lastBackslash);
    if (idx <= 0) return '/';
    return normalized.slice(0, idx);
  };

  const handleNavigate = (path: string) => {
    const nextPath = path === '..' ? getParentPath(currentPath) : path;
    setCurrentPath(nextPath);
    setPathInput(nextPath);
    setSelectedFiles([]);
    if (agentId && socket) {
      const reqPath = nextPath || '/';
      try {
        setLastFilePath(agentId, reqPath);
      } catch {}
      socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${reqPath}` });
      try { setLastActivity('files', reqPath, agentId); } catch {}
    }
  };

  const handlePathKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== 'Enter') return;
    e.preventDefault();
    if (!agentId || !socket) return;
    const trimmed = pathInput.trim();
    if (!trimmed) {
      setPathInput(currentPathRef.current);
      return;
    }
    setIsLoading(true);
    socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${trimmed}` });
    try { setLastActivity('files', trimmed, agentId); } catch {}
  };

  const getExtension = (name: string) => {
    const idx = name.lastIndexOf('.');
    return idx >= 0 ? name.slice(idx + 1).toLowerCase() : '';
  };

  const getPreviewKind = (ext: string): 'image' | 'video' | 'pdf' | 'ppt' | null => {
    const image = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg', 'avif', 'heic', 'heif', 'tif', 'tiff', 'ico', 'jfif']);
    const video = new Set(['mp4', 'webm', 'mov', 'mkv', 'avi', 'm4v']);
    const office = new Set(['ppt', 'pptx']);
    if (ext === 'pdf') return 'pdf';
    if (image.has(ext)) return 'image';
    if (video.has(ext)) return 'video';
    if (office.has(ext)) return 'ppt';
    return null;
  };

  const previewableItems = useMemo(() => {
    return files
      .filter(f => f.type === 'file')
      .filter(f => getPreviewKind((f.extension || getExtension(f.name)).toLowerCase()) !== null)
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [files]);

  const selectedPreviewableIndex = useMemo(() => {
    if (selectedFiles.length !== 1) return -1;
    const selectedPath = selectedFiles[0];
    return previewableItems.findIndex(f => f.path === selectedPath);
  }, [selectedFiles, previewableItems]);

  const previewSourceType = useMemo(() => {
    if (!previewKind || previewKind !== 'video') return undefined;
    const item = previewItems[previewIndex];
    const name = (item?.name || '').toLowerCase();
    const ext = name.includes('.') ? name.split('.').pop()! : '';
    if (ext === 'mp4' || ext === 'm4v' || ext === 'mov') return 'video/mp4';
    if (ext === 'webm') return 'video/webm';
    return undefined;
  }, [previewKind, previewItems, previewIndex]);

  const makeStreamUrl = (path: string) => {
    if (!agentId) return '';
    return `${API_BASE_URL}/api/agents/${agentId}/files/stream?path=${encodeURIComponent(path)}`;
  };
  const makeStreamFastUrl = (path: string) => {
    if (!agentId) return '';
    return `${API_BASE_URL}/api/agents/${agentId}/files/stream_faststart?path=${encodeURIComponent(path)}`;
  };

  const openActual = (path: string, kind: string | null) => {
    if (!agentId) return;
    if (kind === 'ppt') {
      setSelectedFiles([path]);
      downloadFile(agentId!, path);
      return;
    }
    const ext = (getExtension(path) || '').toLowerCase();
    const useFast = kind === 'video' && (ext === 'mp4' || ext === 'm4v' || ext === 'mov');
    const url = useFast ? makeStreamFastUrl(path) : makeStreamUrl(path);
    try {
      const win = window.open(url, '_blank');
      if (!win) {
        window.location.href = url;
      }
    } catch {}
  };
  const makeThumbUrl = (path: string) => {
    if (!agentId) return '';
    return `${API_BASE_URL}/api/agents/${agentId}/files/thumbnail?path=${encodeURIComponent(path)}&size=64`;
  };

  const handlePlay = () => {
    if (selectedFiles.length !== 1) return;
    const idx = selectedPreviewableIndex;
    if (idx < 0) return;
    const item = previewableItems[idx];
    const kind = getPreviewKind((item.extension || getExtension(item.name)).toLowerCase());
    openActual(item.path, kind);
  };
  const handlePreview = () => {
    if (selectedFiles.length !== 1) return;
    const idx = selectedPreviewableIndex;
    if (idx < 0) return;
    setPreviewItems(previewableItems);
    setPreviewIndex(idx);
    setPreviewOpen(true);
  };

  const handleNextPreview = () => {
    const next = previewIndex + 1;
    if (next >= previewItems.length) return;
    setPreviewIndex(next);
  };

  const handlePrevPreview = () => {
    const prev = previewIndex - 1;
    if (prev < 0) return;
    setPreviewIndex(prev);
  };

  const handleDownload = () => {
    if (!agentId || selectedFiles.length === 0) return;
    // Determine if any selection is a directory
    const pathTypes = new Map<string, 'file' | 'directory'>();
    files.forEach(f => pathTypes.set(f.path, f.type));
    const hasDir = selectedFiles.some(p => pathTypes.get(p) === 'directory');
    if (hasDir || selectedFiles.length > 1) {
      handleDownloadZip();
      return;
    }
    setDownloadProgress(0);
    setUploadProgress(null);
    const only = selectedFiles[0];
    const leaf = (p: string) => {
      const s = p.replace(/[\\\/]+$/, '');
      const i = Math.max(s.lastIndexOf('\\'), s.lastIndexOf('/'));
      return i >= 0 ? s.slice(i + 1) : s;
    };
    setTransferFileName(leaf(only));
    downloadFile(agentId!, only);
    setSelectedFiles([]);
  };

  const handleDownloadZip = () => {
    if (!agentId || !socket) return;
    if (selectedFiles.length === 0) return;
    const items = selectedFiles.slice();
    const leaf = (p: string) => {
      const s = p.replace(/[\\\/]+$/, '');
      const i = Math.max(s.lastIndexOf('\\'), s.lastIndexOf('/'));
      return i >= 0 ? s.slice(i + 1) : s;
    };
    const friendly = items.length === 1 ? `${leaf(items[0])}.zip` : `files_${Date.now()}.zip`;
    const esc = (p: string) => p.replace(/'/g, "''");
    const ps = [
      "$ErrorActionPreference='SilentlyContinue'",
      `$items=@(${items.map(p => `'${esc(p)}'`).join(",")})`,
      `$dest=Join-Path $env:TEMP ('nch_zip_'+[DateTime]::Now.ToString('yyyyMMdd_HHmmss')+'.zip')`,
      "try { Compress-Archive -Path $items -DestinationPath $dest -Force -ErrorAction Stop; Write-Output ('NCH_ZIP:'+ $dest) } catch { Write-Output ('NCH_ERR:'+ $_.Exception.Message) }"
    ].join("; ");
    const cmd = `powershell -NoProfile -EncodedCommand ${psEncode(ps)}`;
    setDownloadProgress(0);
    setTransferFileName(friendly);
    socket.emit('execute_command', { agent_id: agentId, command: cmd });
    setZipInProgress({ friendly });
    setSelectedFiles([]);
  };

  const handleUpload = (e?: ChangeEvent<HTMLInputElement>) => {
    const files = e?.target?.files;
    if (!files || files.length === 0 || !agentId) return;
    setUploadProgress(0);
    setDownloadProgress(null);
    setTransferFileName(`${files.length} files`);
    
    Array.from(files).forEach(file => {
      uploadFile(agentId, file, currentPath || '/');
    });
    // Clear input to allow re-selecting the same file without needing a page refresh
    try { if (fileInputRef.current) fileInputRef.current.value = ''; } catch {}
  };

  const handleRefresh = () => {
    setIsLoading(true);
    setSelectedFiles([]);
    if (agentId && socket) {
      const reqPath = currentPath || '/';
      try { setLastFilePath(agentId, reqPath); } catch {}
      socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${reqPath}` });
      try { setLastActivity('files', reqPath, agentId); } catch {}
    }
    setTimeout(() => setIsLoading(false), 500);
  };

  // Delete selected files
  const handleDelete = () => {
    if (!agentId || selectedFiles.length === 0 || !socket) return;
    selectedFiles.forEach(path => {
      socket.emit('execute_command', { agent_id: agentId, command: `delete-file:${path}` });
    });
    // Clear selection immediately so Download(n) resets
    setSelectedFiles([]);
  };

  // Listen to operation results
  useEffect(() => {
    if (!socket) return;
    const handler = (data: any) => {
      if (!agentId || data.agent_id !== agentId) return;
      if (data.success) {
        toast.success(`${data.op} ok: ${data.path || data.dst || ''}`);
        setSelectedFiles([]);
        handleRefresh();
      } else {
        toast.error(`${data.op} failed: ${data.error || ''}`);
      }
    };
    socket.on('file_op_result', handler);
    return () => { socket.off('file_op_result', handler); };
  }, [socket, agentId, files]);

  // Compute real folder sizes on demand
  useEffect(() => {
    if (!socket || !agentId) return;
    const handler = (data: any) => {
      if (!agentId || data.agent_id !== agentId) return;
      const out: string = String(data.output || '');
      const lines = out.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
      if (!lines.some(l => l.startsWith('NCH_SIZE:') || l.startsWith('NCH_ZIP:') || l.startsWith('NCH_ERR:'))) return;
      try {
        for (const line of lines) {
          if (line.startsWith('NCH_SIZE:')) {
            const payload = line.slice('NCH_SIZE:'.length);
            const idx = payload.lastIndexOf(':');
            if (idx <= 0) continue;
            const p = payload.slice(0, idx);
            const szStr = payload.slice(idx + 1);
            const sz = Number(szStr);
            if (Number.isFinite(sz)) {
              setDirSizes(prev => ({ ...prev, [p]: sz }));
              setFiles(prev => prev.map(f => (f.type === 'directory' && f.path === p) ? { ...f, size: sz } : f));
            }
          } else if (line.startsWith('NCH_ZIP:')) {
            const dest = line.slice('NCH_ZIP:'.length).trim();
            if (!dest) continue;
            const friendly = zipInProgress?.friendly || dest.replace(/^.*[\\\/]/, '');
            setZipInProgress({ dest, friendly });
            setDownloadProgress(0);
            socket.emit('download_file', { agent_id: agentId, filename: dest, path: dest, download_id: `zip_${Date.now()}` });
          } else if (line.startsWith('NCH_ERR:')) {
            const msg = line.slice('NCH_ERR:'.length).trim();
            if (msg) toast.error(`ZIP error: ${msg}`);
            setDownloadProgress(null);
            setTransferFileName(null);
            setZipInProgress(null);
          }
        }
      } catch {}
    };
    socket.on('command_result', handler);
    return () => { socket.off('command_result', handler); };
  }, [socket, agentId, zipInProgress]);

  // Listen for file_list updates from agent and map to UI items
  useEffect(() => {
    if (!socket) return;
    const handler = (data: any) => {
      if (!agentId || data.agent_id !== agentId) return;
      if (data && data.success === false) {
        toast.error(data.error || 'Directory not found');
        setIsLoading(false);
        setPathInput(currentPathRef.current);
        return;
      }
      const nextPath = data.path || '/';
      currentPathRef.current = nextPath;
      setCurrentPath(nextPath);
      setPathInput(nextPath);
      try { setLastFilePath(agentId, nextPath); } catch {}
      try { setLastActivity('files', nextPath, agentId); } catch {}
      const mapped = (data.files || []).map((f: any) => ({
        name: f.name,
        type: f.type,
        size: f.size,
        modified: new Date(f.modified || Date.now()),
        path: f.path,
        extension: f.extension
      }));
      setFiles(mapped);
      setIsLoading(false);
      // Trigger background size fetch for directories missing size
      const dirs = mapped.filter((f: any) => f.type === 'directory' && !(typeof f.size === 'number' && f.size >= 0));
      const esc = (p: string) => p.replace(/'/g, "''");
      let i = 0;
      const kick = () => {
        if (!socket || !agentId) return;
        if (i >= dirs.length) return;
        const p = dirs[i++].path;
        const ps = [
          "$ErrorActionPreference='SilentlyContinue'",
          `$p='${esc(p)}'`,
          "$s=(Get-ChildItem -LiteralPath $p -Recurse -File -Force | Measure-Object -Sum Length).Sum",
          "if ($null -eq $s) { $s=0 }",
          "Write-Output ('NCH_SIZE:'+ $p + ':' + $s)"
        ].join("; ");
        const cmd = `powershell -NoProfile -EncodedCommand ${psEncode(ps)}`;
        socket.emit('execute_command', { agent_id: agentId, command: cmd });
        setTimeout(kick, 400);
      };
      setTimeout(kick, 300);
    };
    socket.on('file_list', handler);
    return () => { socket.off('file_list', handler); };
  }, [socket, agentId]);

  useEffect(() => {
    if (!previewOpen) return;
    if (previewItems.length === 0) return;
    const item = previewItems[previewIndex];
    if (!item || !agentId) return;
    previewSessionRef.current += 1;
    previewVideoReadyRef.current = false;
    if (previewVideoStartupTimerRef.current) {
      window.clearTimeout(previewVideoStartupTimerRef.current);
      previewVideoStartupTimerRef.current = null;
    }
    const ext = (item.extension || getExtension(item.name)).toLowerCase();
    const kind = getPreviewKind(ext);
    setPreviewKind(kind);
    setPreviewErrorCount(0);
    setPreviewUrl(null);
    if (kind === 'video' && previewVideoRef.current) {
      try {
        previewVideoRef.current.pause();
        previewVideoRef.current.removeAttribute('src');
        previewVideoRef.current.load();
      } catch {}
    }
    if (kind === 'video') {
      setPreviewVideoMode('normal');
      setPreviewUrl(makeStreamUrl(item.path));
      const sessionId = previewSessionRef.current;
      previewVideoStartupTimerRef.current = window.setTimeout(() => {
        if (!previewOpen) return;
        if (previewSessionRef.current !== sessionId) return;
        if (previewVideoReadyRef.current) return;
        setPreviewVideoMode('faststart');
        setPreviewUrl(makeStreamFastUrl(item.path));
      }, 1500);
      return;
    }
    setPreviewUrl(makeStreamUrl(item.path));
  }, [previewOpen, previewIndex, previewItems, agentId]);

  useEffect(() => {
    if (!agentId || !socket) return;
    const reqPath = getLastFilePath(agentId);
    currentPathRef.current = reqPath;
    setCurrentPath(reqPath);
    setPathInput(reqPath);
    socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${reqPath}` });
  }, [agentId, socket, getLastFilePath]);

  useEffect(() => {
    if (previewOpen) return;
    setPreviewUrl(null);
    setPreviewKind(null);
    setPreviewItems([]);
    setPreviewIndex(0);
    setPreviewVideoMode('normal');
    previewVideoReadyRef.current = false;
    if (previewVideoStartupTimerRef.current) {
      window.clearTimeout(previewVideoStartupTimerRef.current);
      previewVideoStartupTimerRef.current = null;
    }
    if (previewVideoRef.current) {
      try {
        previewVideoRef.current.pause();
        previewVideoRef.current.removeAttribute('src');
        previewVideoRef.current.load();
      } catch {}
    }
  }, [previewOpen]);

  // Listen for upload progress events
  useEffect(() => {
    const handleUploadProgress = (event: any) => {
      const data = event.detail;
      console.log('📊 FileManager: Upload progress received:', data);
      if (data && typeof data.progress === 'number' && data.progress >= 0) {
        setUploadProgress(data.progress);
        console.log(`📊 FileManager: Setting upload progress to ${data.progress}%`);
      }
    };

    const handleUploadComplete = (event: any) => {
      const data = event.detail;
      console.log('✅ FileManager: Upload complete received:', data);
      setUploadProgress(100);
      setTimeout(() => {
        setUploadProgress(null);
        setTransferFileName(null);
        // If upload failed, show error and do a lightweight refresh of current directory
        if (data?.success === false || data?.error) {
          toast.error(`Upload failed: ${data?.error || 'Unknown error'}`);
          handleRefresh();
          return;
        }
        // When server-side completion arrives first, show provisional toast and refresh target dir
        if (data?.source && String(data.source) === 'server') {
          try {
            const dst = String(data?.destination_path || '');
            const dir = dst ? dst.replace(/[\\/]?[^\\/]+$/, '') : '';
            toast.info(`Upload forwarded to agent: ${dst || data.filename}`);
            if (dir && agentId && socket) {
              currentPathRef.current = dir;
              setCurrentPath(dir);
              setPathInput(dir);
              try { setLastFilePath(agentId, dir); } catch {}
              socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${dir}` });
            } else {
              handleRefresh();
            }
          } catch {
            handleRefresh();
          }
          // Wait for agent-confirmed completion to show final success toast
          return;
        }
        toast.success(`File uploaded successfully to ${data.destination_path || data.filename}`);
        try {
          const dst = String(data?.destination_path || '');
          const dir = dst ? dst.replace(/[\\/]?[^\\/]+$/, '') : '';
          if (dir && agentId && socket) {
            currentPathRef.current = dir;
            setCurrentPath(dir);
            setPathInput(dir);
            try { setLastFilePath(agentId, dir); } catch {}
            socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${dir}` });
          } else {
            handleRefresh();
          }
        } catch {
          handleRefresh();
        }
      }, 1000);
    };

    window.addEventListener('file_upload_progress', handleUploadProgress);
    window.addEventListener('file_upload_complete', handleUploadComplete);

    return () => {
      window.removeEventListener('file_upload_progress', handleUploadProgress);
      window.removeEventListener('file_upload_complete', handleUploadComplete);
    };
  }, []);

  // Listen for download progress events
  useEffect(() => {
    const handleDownloadProgress = (event: any) => {
      const data = event.detail;
      console.log('📊 FileManager: Download progress received:', data);
      if (data && typeof data.progress === 'number' && data.progress >= 0) {
        setDownloadProgress(data.progress);
        console.log(`📊 FileManager: Setting download progress to ${data.progress}%`);
      }
    };

    const handleDownloadComplete = (event: any) => {
      const data = event.detail;
      console.log('✅ FileManager: Download complete received:', data);
      setDownloadProgress(100);
      setTimeout(() => {
        setDownloadProgress(null);
        setTransferFileName(null);
        toast.success(`File downloaded successfully: ${data.filename}`);
        try {
          const dest = zipInProgress?.dest;
          if (dest && String(data?.filename || '').includes(dest)) {
            if (socket && agentId) {
              const esc = dest.replace(/'/g, "''");
              const ps = `$ErrorActionPreference='SilentlyContinue'; Remove-Item -LiteralPath '${esc}' -Force`;
              const cmd = `powershell -NoProfile -Command "${ps}"`;
              socket.emit('execute_command', { agent_id: agentId, command: cmd });
            }
          }
        } catch {}
        setZipInProgress(null);
      }, 1000);
    };

    window.addEventListener('file_download_progress', handleDownloadProgress);
    window.addEventListener('file_download_complete', handleDownloadComplete);

    return () => {
      window.removeEventListener('file_download_progress', handleDownloadProgress);
      window.removeEventListener('file_download_complete', handleDownloadComplete);
    };
  }, []);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm flex items-center">
              <Files className="h-4 w-4 mr-2" />
              File Manager
            </CardTitle>
            {agentId && (
              <Badge variant="outline" className="text-xs">
                {(() => {
                  try {
                    const a = agents?.find(x => x.id === agentId);
                    // prefer alias if set; else show full ID; else show name
                    return a?.alias || agentId || a?.name || '';
                  } catch {
                    return agentId;
                  }
                })()}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {!agentId ? (
            <div className="text-center text-muted-foreground py-8">
              <Files className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>Select an agent to browse files</p>
            </div>
          ) : (
            <>
              <div className="sticky top-20 z-40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75 border-b rounded-md p-2 space-y-2">
                <div className="flex items-center gap-2 flex-nowrap">
                  <Button variant="ghost" size="sm" className="w-auto" onClick={() => handleNavigate('/')}>
                    <Home className="h-3 w-3" />
                  </Button>
                  <Button variant="ghost" size="sm" className="w-auto" onClick={() => handleNavigate('..')}>
                    <ArrowLeft className="h-3 w-3" />
                  </Button>
                  <Input
                    value={pathInput}
                    onChange={(e) => setPathInput(e.target.value)}
                    onKeyDown={handlePathKeyDown}
                    className="w-full min-w-0 basis-0 text-sm text-muted-foreground font-mono bg-muted"
                  />
                  <Button variant="ghost" size="sm" className="w-auto" onClick={handleRefresh} disabled={isLoading}>
                    <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
                <div className="flex items-center gap-2 flex-nowrap overflow-x-auto">
                  <div className="relative w-full max-w-[280px] sm:max-w-sm md:max-w-[300px]">
                    <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                    <Input
                      placeholder="Search files..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="pl-8 w-full"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Select value={sortBy} onValueChange={(v) => setSortBy(v as any)}>
                      <SelectTrigger className="h-8 w-[120px]">
                        <SelectValue placeholder="Sort by" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="name">Name</SelectItem>
                        <SelectItem value="modified">Date</SelectItem>
                        <SelectItem value="size">Size</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={sortOrder} onValueChange={(v) => setSortOrder(v as any)}>
                      <SelectTrigger className="h-8 w-[110px]">
                        <SelectValue placeholder="Order" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="asc">Asc</SelectItem>
                        <SelectItem value="desc">Desc</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2 flex-nowrap ml-auto">
                    <Button 
                      size="sm" 
                      className="w-auto whitespace-nowrap"
                      onClick={handleDownload}
                      disabled={selectedFiles.length === 0 || uploadProgress !== null || downloadProgress !== null}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Download ({selectedFiles.length})
                    </Button>
                    <label className="inline-flex items-center w-auto">
                      <input type="file" className="hidden" ref={fileInputRef} onChange={handleUpload} multiple />
                      <Button size="sm" variant="outline" className="w-auto whitespace-nowrap" disabled={uploadProgress !== null || downloadProgress !== null} asChild>
                        <span className="inline-flex items-center"><Upload className="h-3 w-3 mr-1" />Upload</span>
                      </Button>
                    </label>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="w-auto whitespace-nowrap"
                      onClick={handlePlay}
                      disabled={selectedPreviewableIndex < 0 || uploadProgress !== null || downloadProgress !== null}
                    >
                      <Video className="h-3 w-3 mr-1" />
                      Preview
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      className="w-auto px-2 justify-center"
                      disabled={selectedFiles.length === 0}
                      onClick={() => setConfirmDeleteOpen(true)}
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              </div>

              <Dialog open={false} onOpenChange={setPreviewOpen}>
                <DialogContent className="w-[90vw] max-w-5xl h-[85vh] p-4 flex flex-col">
                  <div className="flex flex-col h-full gap-3 min-w-0">
                    {/* Header with word-wrap for long filenames */}
                    <DialogHeader className="shrink-0 min-w-0 max-w-full space-y-2">
                      <DialogTitle className="text-base font-semibold break-words leading-tight line-clamp-3 pr-8">
                        {previewItems[previewIndex]?.name || 'Preview'}
                      </DialogTitle>
                      <DialogDescription className="text-sm text-muted-foreground flex items-center gap-2 flex-wrap">
                        <span>{previewIndex + 1} / {previewItems.length}</span>
                        <span>•</span>
                        <span>{formatFileSize(previewItems[previewIndex]?.size)}</span>
                        {previewItems[previewIndex]?.extension && (
                          <>
                            <span>•</span>
                            <span className="uppercase">{previewItems[previewIndex].extension}</span>
                          </>
                        )}
                      </DialogDescription>
                    </DialogHeader>
                    
                    {/* Preview area - responsive viewport sizing */}
                    <div className="shrink-0 bg-muted/50 rounded overflow-hidden flex items-center justify-center relative w-[85vw] h-[45vh] md:w-[70vw] md:h-[60vh] lg:w-[50vw] lg:h-[50vh] mx-auto">
                      {previewUrl && previewKind === 'image' && (
                        <div className="w-full h-full flex items-center justify-center p-2">
                          <img 
                            src={previewUrl} 
                            className={`${fitMode === 'contain' ? 'max-w-full max-h-full' : 'w-full h-full'} ${fitMode === 'contain' ? 'object-contain' : fitMode === 'cover' ? 'object-cover' : 'object-fill'}`} 
                            alt={previewItems[previewIndex]?.name}
                          />
                        </div>
                      )}
                      
                      {previewUrl && previewKind === 'video' && (
                        <div className="w-full h-full flex items-center justify-center p-2">
                          <video
                            key={`${previewItems[previewIndex]?.path || ''}:${previewErrorCount}:${previewVideoMode}`}
                            ref={previewVideoRef}
                            className={`${fitMode === 'contain' ? 'max-w-full max-h-full' : 'w-full h-full'} ${fitMode === 'contain' ? 'object-contain' : fitMode === 'cover' ? 'object-cover' : 'object-fill'}`}
                            controls
                            playsInline
                            preload="auto"
                            onLoadedMetadata={() => {
                              previewVideoReadyRef.current = true;
                              if (previewVideoStartupTimerRef.current) {
                                window.clearTimeout(previewVideoStartupTimerRef.current);
                                previewVideoStartupTimerRef.current = null;
                              }
                            }}
                            onCanPlay={() => {
                              previewVideoReadyRef.current = true;
                              if (previewVideoStartupTimerRef.current) {
                                window.clearTimeout(previewVideoStartupTimerRef.current);
                                previewVideoStartupTimerRef.current = null;
                              }
                            }}
                            onError={() => {
                              const item = previewItems[previewIndex];
                              if (!item) return;
                              if (previewErrorCount > 0) return;
                              setPreviewErrorCount(1);
                              if (previewVideoMode === 'normal') {
                                setPreviewVideoMode('faststart');
                                setPreviewUrl(makeStreamFastUrl(item.path));
                              } else {
                                setPreviewVideoMode('normal');
                                setPreviewUrl(makeStreamUrl(item.path));
                              }
                            }}
                          >
                            <source src={previewUrl} type={previewSourceType} />
                          </video>
                        </div>
                      )}
                      
                      {previewUrl && previewKind === 'pdf' && (
                        <div className="w-full h-full">
                          <iframe 
                            src={previewUrl} 
                            className="w-full h-full border-0" 
                            title="PDF Preview" 
                          />
                        </div>
                      )}
                      
                      {previewKind === 'ppt' && (
                        <div className="w-full h-full flex flex-col items-center justify-center gap-3 text-muted-foreground">
                          <div className="text-sm text-center px-4">
                            <p className="font-medium mb-1">Preview not available</p>
                            <p className="text-xs">PowerPoint files must be downloaded to view</p>
                          </div>
                          <Button size="sm" onClick={handleDownload}>
                            <Download className="h-3 w-3 mr-1" />
                            Download to view
                          </Button>
                        </div>
                      )}
                      
                      {!previewUrl && (
                        <div className="w-full h-full flex items-center justify-center">
                          <div className="flex flex-col items-center gap-3">
                            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
                            <div className="text-sm text-muted-foreground">Loading preview...</div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Navigation footer */}
                    <div className="shrink-0 flex items-center justify-between gap-2">
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={handlePrevPreview} 
                        disabled={previewIndex <= 0}
                        className="min-w-[100px]"
                      >
                        ← Previous
                      </Button>
                      <div className="text-xs text-muted-foreground text-center">
                        <div>{formatFileSize(previewItems[previewIndex]?.size)}</div>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={handleNextPreview}
                        disabled={previewIndex >= previewItems.length - 1}
                        className="min-w-[100px]"
                      >
                        Next →
                      </Button>
                      <div className="flex items-center gap-2">
                        <Button size="sm" variant="outline" onClick={() => setFitMode('contain')} disabled={fitMode === 'contain'}>
                          Fit: contain
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setFitMode('cover')} disabled={fitMode === 'cover'}>
                          Fit: cover
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setFitMode('fill')} disabled={fitMode === 'fill'}>
                          Fit: fill
                        </Button>
                      </div>
                    </div>
                  </div>
                </DialogContent>
              </Dialog>
              
              <Dialog open={confirmDeleteOpen} onOpenChange={setConfirmDeleteOpen}>
                <DialogContent className="sm:max-w-[440px]">
                  <DialogHeader>
                    <DialogTitle className="text-sm">Delete selected files?</DialogTitle>
                    <DialogDescription className="text-sm text-muted-foreground">
                      This action can't be undone.
                    </DialogDescription>
                  </DialogHeader>
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div>{selectedFiles.length} item(s) will be deleted.</div>
                    <div className="max-h-32 overflow-auto rounded bg-muted p-2">
                      {selectedFiles.slice(0, 5).map((p, i) => (
                        <div key={i} className="truncate">{p}</div>
                      ))}
                      {selectedFiles.length > 5 && (
                        <div>and {selectedFiles.length - 5} more…</div>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="outline" onClick={() => setConfirmDeleteOpen(false)}>Cancel</Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => {
                        setConfirmDeleteOpen(false);
                        handleDelete();
                      }}
                    >
                      Delete
                    </Button>
                  </div>
                </DialogContent>
              </Dialog>

              {/* Upload/Download Progress */}
              {(uploadProgress !== null || downloadProgress !== null) && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="flex items-center gap-2">
                      {uploadProgress !== null ? (
                        <>
                          <Upload className="h-3 w-3 animate-pulse" />
                          Uploading {transferFileName || '...'}
                        </>
                      ) : (
                        <>
                          <Download className="h-3 w-3 animate-pulse" />
                          Downloading {transferFileName || '...'}
                        </>
                      )}
                    </span>
                    <span className="font-mono font-semibold">
                      {uploadProgress !== null ? uploadProgress : downloadProgress}%
                    </span>
                  </div>
                  <Progress value={uploadProgress !== null ? uploadProgress : downloadProgress || 0} />
                </div>
              )}

              <Card>
                <CardContent className="p-0">
                  <ScrollArea className="h-[50vh] md:h-[60vh] lg:h-[65vh]">
                    <div className="space-y-1 p-4">
                      {filteredFiles.map((file, index) => {
                        const Icon = getFileIcon(file);
                        const isSelected = selectedFiles.includes(file.path);
                        const ext = (file.extension || getExtension(file.name)).toLowerCase();
                        const kind = file.type === 'file' ? getPreviewKind(ext) : null;
                        const showThumb = Boolean(agentId && file.type === 'file' && (kind === 'image' || kind === 'video'));
                        
                        return (
                          <div
                            key={index}
                            className={`flex items-center gap-3 p-2 rounded hover:bg-muted ${isSelected ? 'bg-secondary' : ''}`}
                            onClick={() => {
                              if (file.type === 'directory') {
                                handleNavigate(file.path);
                                setSearchTerm('');
                              } else {
                                setSelectedFiles([]);
                                const ext2 = (file.extension || getExtension(file.name)).toLowerCase();
                                const kind2 = getPreviewKind(ext2);
                                openActual(file.path, kind2);
                              }
                            }}
                          >
                            {showThumb ? (
                              <img
                                src={makeThumbUrl(file.path)}
                                className="h-10 w-10 rounded object-cover bg-background"
                                loading="lazy"
                                alt=""
                                onClick={(e) => { e.stopPropagation(); handleFileSelect(file.path); }}
                              />
                            ) : (
                            <Icon 
                              className={`h-5 w-5 ${file.type === 'directory' ? 'text-blue-500' : 'text-muted-foreground'} cursor-pointer`} 
                              onClick={(e: any) => { 
                                e.stopPropagation(); 
                                handleFileSelect(file.path); 
                              }} 
                            />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm truncate">{file.name}</div>
                            </div>
                            <div className="hidden sm:block text-xs text-muted-foreground w-20 text-right">
                              {formatFileSize(file.size)}
                            </div>
                            <div className="hidden md:block text-xs text-muted-foreground w-32 text-right">
                              {file.modified.toLocaleDateString()}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

              {/* Floating action bar when selection exists */}
              {selectedFiles.length > 0 && (
                <div className="sticky bottom-0 z-30 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/75 border-t rounded-t-md p-2 shadow-lg">
                  <div className="flex items-center gap-2 justify-end flex-wrap">
                    <div className="text-xs text-muted-foreground mr-auto">
                      {selectedFiles.length} selected
                    </div>
                    <Button 
                      size="sm" 
                      className="w-auto whitespace-nowrap"
                      onClick={handleDownload}
                      disabled={uploadProgress !== null || downloadProgress !== null}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Download ({selectedFiles.length})
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="w-auto whitespace-nowrap"
                      onClick={handlePlay}
                      disabled={selectedPreviewableIndex < 0 || uploadProgress !== null || downloadProgress !== null}
                    >
                      <Video className="h-3 w-3 mr-1" />
                      Preview
                    </Button>
                    <Button 
                      size="sm" 
                      variant="destructive"
                      className="w-auto px-2"
                      disabled={selectedFiles.length === 0}
                      onClick={() => setConfirmDeleteOpen(true)}
                      title="Delete"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="ghost"
                      className="w-auto px-2"
                      onClick={() => setSelectedFiles([])}
                      title="Clear selection"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                </div>
              )}

              <div className="text-xs text-muted-foreground">
                {filteredFiles.length} items • {selectedFiles.length} selected
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
