import * as React from "react";
import { useEffect, useState } from 'react';
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
  const { uploadFile, downloadFile } = useSocket();
  const { socket } = useSocket();
  const [currentPath, setCurrentPath] = useState('/');
  const [files, setFiles] = useState(mockFiles);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const filteredFiles = files.filter(file => 
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleFileSelect = (fileName: string) => {
    setSelectedFiles(prev => 
      prev.includes(fileName) 
        ? prev.filter(f => f !== fileName)
        : [...prev, fileName]
    );
  };

  const handleNavigate = (path: string) => {
    setCurrentPath(path);
    setSelectedFiles([]);
    if (agentId && socket) {
      const reqPath = path === '..' ? '/' : path;
      socket.emit('execute_command', { agent_id: agentId, command: `list-dir:${reqPath}` });
    }
  };

  const handleDownload = () => {
    if (selectedFiles.length === 0) return;
    // Request download via socket (first selected file)
    downloadFile(agentId!, selectedFiles[0]);
  };

  const handleUpload = (e?: React.ChangeEvent<HTMLInputElement>) => {
    const file = e?.target?.files?.[0];
    if (!file || !agentId) return;
    setUploadProgress(0);
    uploadFile(agentId, file, currentPath === '/' ? `/${file.name}` : `${currentPath}/${file.name}`);
  };

  const handleRefresh = () => {
    setIsLoading(true);
    handleNavigate(currentPath);
    setTimeout(() => setIsLoading(false), 500);
  };

  // Delete selected files
  const handleDelete = () => {
    if (!agentId || selectedFiles.length === 0 || !socket) return;
    selectedFiles.forEach(name => {
      const item = files.find(f => f.name === name);
      if (item) {
        socket.emit('execute_command', { agent_id: agentId, command: `delete-file:${item.path}` });
      }
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
      setCurrentPath(data.path || '/');
      const mapped = (data.files || []).map((f: any) => ({
        name: f.name,
        type: f.type,
        size: f.size,
        modified: new Date(f.modified || Date.now()),
        path: f.path,
        extension: f.extension
      }));
      setFiles(mapped);
    };
    socket.on('file_list', handler);
    return () => { socket.off('file_list', handler); };
  }, [socket, agentId]);

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
                <div className="flex-1 text-sm text-muted-foreground font-mono bg-muted px-2 py-1 rounded">
                  {currentPath}
                </div>
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
                  disabled={selectedFiles.length === 0 || uploadProgress !== null}
                >
                  <Download className="h-3 w-3 mr-1" />
                  Download ({selectedFiles.length})
                </Button>
                <label className="inline-flex items-center">
                  <input type="file" className="hidden" onChange={handleUpload} />
                  <Button size="sm" variant="outline" disabled={uploadProgress !== null} asChild>
                    <span className="inline-flex items-center"><Upload className="h-3 w-3 mr-1" />Upload</span>
                  </Button>
                </label>
                <Button 
                  size="sm" 
                  variant="destructive"
                  disabled={selectedFiles.length === 0}
                  onClick={handleDelete}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>

              {/* Upload/Download Progress */}
              {uploadProgress !== null && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Transfer Progress</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} />
                </div>
              )}

              {/* File List */}
              <Card>
                <CardContent className="p-0">
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-1 p-4">
                      {filteredFiles.map((file, index) => {
                        const Icon = getFileIcon(file);
                        const isSelected = selectedFiles.includes(file.name);
                        
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
                                handleFileSelect(file.name);
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