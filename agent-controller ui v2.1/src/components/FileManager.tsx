import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useSocket } from './SocketProvider';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Progress } from './ui/progress';
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
  const { uploadFile, downloadFile, socket } = useSocket();
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
  const [previewKind, setPreviewKind] = useState<'image' | 'video' | null>(null);
  const [previewItems, setPreviewItems] = useState<FileItem[]>([]);
  const [previewIndex, setPreviewIndex] = useState<number>(0);
  const lastPreviewUrlRef = useRef<string | null>(null);
  const currentPathRef = useRef<string>('/');

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
      socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${reqPath}` });
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
  };

  const getExtension = (name: string) => {
    const idx = name.lastIndexOf('.');
    return idx >= 0 ? name.slice(idx + 1).toLowerCase() : '';
  };

  const getPreviewKind = (ext: string): 'image' | 'video' | null => {
    const image = new Set(['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg']);
    const video = new Set(['mp4', 'webm', 'mov', 'mkv', 'avi', 'm4v']);
    if (image.has(ext)) return 'image';
    if (video.has(ext)) return 'video';
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

  const requestPreviewAtIndex = (index: number) => {
    if (!agentId || !socket) return;
    if (index < 0 || index >= previewItems.length) return;
    const item = previewItems[index];
    const ext = (item.extension || getExtension(item.name)).toLowerCase();
    const kind = getPreviewKind(ext);
    setPreviewKind(kind);
    setTransferFileName(item.name);
    setDownloadProgress(0);
    socket.emit('download_file', {
      agent_id: agentId,
      filename: item.path,
      download_id: `preview_${Date.now()}_${Math.random().toString(16).slice(2)}`
    });
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
    const filePath = selectedFiles[0];
    const item = files.find(f => f.path === filePath);
    setDownloadProgress(0);
    setUploadProgress(null);
    setTransferFileName(item?.name || filePath);
    // Request download via socket (first selected file)
    downloadFile(agentId!, filePath);
  };

  const handleUpload = (e?: ChangeEvent<HTMLInputElement>) => {
    const file = e?.target?.files?.[0];
    if (!file || !agentId) return;
    setUploadProgress(0);
    setDownloadProgress(null);
    setTransferFileName(file.name);
    uploadFile(agentId, file, currentPath === '/' ? '' : currentPath);
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
    const handler = (event: any) => {
      const data = event.detail;
      if (!data || !agentId || data.agent_id !== agentId) return;
      if (typeof data.url === 'string') {
        if (lastPreviewUrlRef.current) {
          URL.revokeObjectURL(lastPreviewUrlRef.current);
        }
        lastPreviewUrlRef.current = data.url;
        setPreviewUrl(data.url);
        setDownloadProgress(null);
        setTransferFileName(null);
      }
    };
    window.addEventListener('file_preview_ready', handler);
    return () => {
      window.removeEventListener('file_preview_ready', handler);
    };
  }, [agentId]);

  useEffect(() => {
    if (!previewOpen) return;
    requestPreviewAtIndex(previewIndex);
  }, [previewOpen, previewIndex]);

  useEffect(() => {
    if (previewOpen) return;
    if (lastPreviewUrlRef.current) {
      URL.revokeObjectURL(lastPreviewUrlRef.current);
      lastPreviewUrlRef.current = null;
    }
    setPreviewUrl(null);
    setPreviewKind(null);
    setPreviewItems([]);
    setPreviewIndex(0);
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
                  <input type="file" className="hidden" onChange={handleUpload} />
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
                  onClick={handleDelete}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>

              {previewOpen && (
                <div className="border rounded p-3 space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="text-sm truncate">{previewItems[previewIndex]?.name || ''}</div>
                    <Button size="sm" variant="ghost" onClick={() => setPreviewOpen(false)}>
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                  <div className="w-[500px] h-[500px] bg-muted rounded overflow-hidden flex items-center justify-center">
                    {previewUrl && previewKind === 'image' && (
                      <img src={previewUrl} className="max-w-full max-h-full object-contain" />
                    )}
                    {previewUrl && previewKind === 'video' && (
                      <video src={previewUrl} className="max-w-full max-h-full" controls />
                    )}
                    {!previewUrl && (
                      <div className="text-xs text-muted-foreground">Loading preview…</div>
                    )}
                  </div>
                  <div className="flex items-center justify-between">
                    <Button size="sm" variant="outline" onClick={handlePrevPreview} disabled={previewIndex <= 0}>
                      Prev
                    </Button>
                    <div className="text-xs text-muted-foreground">
                      {previewIndex + 1}/{previewItems.length}
                    </div>
                    <Button size="sm" variant="outline" onClick={handleNextPreview} disabled={previewIndex >= previewItems.length - 1}>
                      Next
                    </Button>
                  </div>
                </div>
              )}

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

              {/* File List */}
              <Card>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-1 p-4">
                      {filteredFiles.map((file, index) => {
                        const Icon = getFileIcon(file);
                        const isSelected = selectedFiles.includes(file.path);
                        
                        return (
                          <div
                            key={index}
                            className={`flex items-center space-x-3 p-2 rounded cursor-pointer hover:bg-muted ${
                              isSelected ? 'bg-secondary' : ''
                            }`}
                            onClick={() => {
                              if (file.type === 'directory') {
                                handleNavigate(file.path);
                              } else {
                                handleFileSelect(file.path);
                              }
                            }}
                          >
                            <Icon className={`h-4 w-4 ${file.type === 'directory' ? 'text-blue-500' : 'text-muted-foreground'}`} />
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

              {/* File Info */}
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
