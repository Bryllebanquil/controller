import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useSocket } from './SocketProvider';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
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
  Music
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
  if (!bytes) return '-';
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
};

export function FileManager({ agentId }: FileManagerProps) {
  const { uploadFile, downloadFile, socket, setLastActivity, getLastFilePath, setLastFilePath } = useSocket();
  const [currentPath, setCurrentPath] = useState('/');
  const [pathInput, setPathInput] = useState('/');
  const [files, setFiles] = useState(mockFiles);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [downloadProgress, setDownloadProgress] = useState<number | null>(null);
  const [transferFileName, setTransferFileName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
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

  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
    const image = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg']);
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

  const makeThumbUrl = (path: string) => {
    if (!agentId) return '';
    return `${API_BASE_URL}/api/agents/${agentId}/files/thumbnail?path=${encodeURIComponent(path)}&size=64`;
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
    if (selectedFiles.length === 0) return;
    setDownloadProgress(0);
    setUploadProgress(null);
    setTransferFileName(`${selectedFiles.length} files`);
    // Request download via socket for all selected files
    selectedFiles.forEach(filePath => {
      downloadFile(agentId!, filePath);
    });
  };

  const handleUpload = (e?: ChangeEvent<HTMLInputElement>) => {
    const files = e?.target?.files;
    if (!files || files.length === 0 || !agentId) return;
    setUploadProgress(0);
    setDownloadProgress(null);
    setTransferFileName(`${files.length} files`);
    
    Array.from(files).forEach(file => {
      uploadFile(agentId, file, currentPath === '/' ? '' : currentPath);
    });
  };

  const handleRefresh = () => {
    setIsLoading(true);
    handleNavigate(currentPath);
    setTimeout(() => setIsLoading(false), 500);
  };

  // Delete selected files
  const handleDelete = () => {
    if (!agentId || selectedFiles.length === 0 || !socket) return;
    selectedFiles.forEach(path => {
      socket.emit('execute_command', { agent_id: agentId, command: `delete-file:${path}` });
    });
  };

  // Listen to operation results
  useEffect(() => {
    if (!socket) return;
    const handler = (data: any) => {
      if (!agentId || data.agent_id !== agentId) return;
      if (data.success) {
        toast.success(`${data.op} ok: ${data.path || data.dst || ''}`);
        handleRefresh();
      } else {
        toast.error(`${data.op} failed: ${data.error || ''}`);
      }
    };
    socket.on('file_op_result', handler);
    return () => { socket.off('file_op_result', handler); };
  }, [socket, agentId, files]);

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
        toast.success(`File uploaded successfully: ${data.filename}`);
        handleRefresh();
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
              <Badge variant="outline">{agentId.substring(0, 8)}</Badge>
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
              {/* Navigation */}
              <div className="flex items-center space-x-2">
                <Button variant="ghost" size="sm" onClick={() => handleNavigate('/')}>
                  <Home className="h-3 w-3" />
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleNavigate('..')}>
                  <ArrowLeft className="h-3 w-3" />
                </Button>
                <Input
                  value={pathInput}
                  onChange={(e) => setPathInput(e.target.value)}
                  onKeyDown={handlePathKeyDown}
                  className="flex-1 text-sm text-muted-foreground font-mono bg-muted"
                />
                <Button variant="ghost" size="sm" onClick={handleRefresh} disabled={isLoading}>
                  <RefreshCw className={`h-3 w-3 ${isLoading ? 'animate-spin' : ''}`} />
                </Button>
              </div>

              {/* Search and Actions */}
              <div className="flex items-center space-x-2">
                <div className="flex-1 relative">
                  <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 h-3 w-3 text-muted-foreground" />
                  <Input
                    placeholder="Search files..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-8"
                  />
                </div>
                <Button 
                  size="sm" 
                  onClick={handleDownload}
                  disabled={selectedFiles.length === 0 || uploadProgress !== null || downloadProgress !== null}
                >
                  <Download className="h-3 w-3 mr-1" />
                  Download ({selectedFiles.length})
                </Button>
                <label className="inline-flex items-center">
                  <input type="file" className="hidden" onChange={handleUpload} multiple />
                  <Button size="sm" variant="outline" disabled={uploadProgress !== null || downloadProgress !== null} asChild>
                    <span className="inline-flex items-center"><Upload className="h-3 w-3 mr-1" />Upload</span>
                  </Button>
                </label>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handlePreview}
                  disabled={selectedPreviewableIndex < 0 || uploadProgress !== null || downloadProgress !== null}
                >
                  <Image className="h-3 w-3 mr-1" />
                  Preview
                </Button>
                <Button 
                  size="sm" 
                  variant="destructive"
                  disabled={selectedFiles.length === 0}
                  onClick={() => setConfirmDeleteOpen(true)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>

              <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
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
                    
                    {/* Preview area - constrained to 50% of viewport */}
                    <div className="shrink-0 bg-muted/50 rounded overflow-hidden flex items-center justify-center relative w-[50vw] h-[50vh] mx-auto">
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
                  <ScrollArea className="h-[400px]">
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
                            className={`flex items-center space-x-3 p-2 rounded cursor-pointer hover:bg-muted ${isSelected ? 'bg-secondary' : ''}`}
                            onClick={() => {
                              if (file.type === 'directory') {
                                handleNavigate(file.path);
                                setSearchTerm('');
                              } else {
                                const ext2 = (file.extension || getExtension(file.name)).toLowerCase();
                                const kind2 = getPreviewKind(ext2);
                                if (kind2) {
                                  setSelectedFiles([file.path]);
                                  const idx = previewableItems.findIndex(f => f.path === file.path);
                                  if (idx >= 0) {
                                    setPreviewItems(previewableItems);
                                    setPreviewIndex(idx);
                                    setPreviewOpen(true);
                                  } else {
                                    handleFileSelect(file.path);
                                  }
                                } else {
                                  handleFileSelect(file.path);
                                }
                                const now = Date.now();
                                if (now - (lastRefreshRef.current || 0) > 700) {
                                  lastRefreshRef.current = now;
                                  handleRefresh();
                                }
                              }
                            }}
                          >
                            {showThumb ? (
                              <img
                                src={makeThumbUrl(file.path)}
                                className="h-8 w-8 rounded object-cover bg-background"
                                loading="lazy"
                                alt=""
                              />
                            ) : (
                              <Icon className={`h-4 w-4 ${file.type === 'directory' ? 'text-blue-500' : 'text-muted-foreground'}`} />
                            )}
                            <div className="flex-1 min-w-0">
                              <div className="text-sm truncate">{file.name}</div>
                            </div>
                            <div className="text-xs text-muted-foreground w-20 text-right">
                              {formatFileSize(file.size)}
                            </div>
                            <div className="text-xs text-muted-foreground w-32 text-right">
                              {file.modified.toLocaleDateString()}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>

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
