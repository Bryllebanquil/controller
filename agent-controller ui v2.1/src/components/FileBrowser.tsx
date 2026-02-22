import React, { useEffect, useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import apiClient from '../services/api';

interface FileItem {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  path: string;
  extension?: string;
}

interface FileBrowserProps {
  agentId: string | null;
}

export function FileBrowser({ agentId }: FileBrowserProps) {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState('/');
  const [loading, setLoading] = useState(false);
  const [thumbnailCache, setThumbnailCache] = useState<Record<string, string>>({});

  const imageExtensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'avif', 'heic', 'heif', 'tif', 'tiff', 'ico', 'jfif'];
  const videoExtensions = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm'];

  const isMediaFile = (file: FileItem) => {
    const ext = (file.extension || '').toLowerCase();
    return imageExtensions.includes(ext) || videoExtensions.includes(ext);
  };

  const getThumbnail = (file: FileItem) => {
    const cacheKey = `${agentId}:${file.path}`;
    return thumbnailCache[cacheKey];
  };

  const loadThumbnail = async (file: FileItem) => {
    if (!agentId || !isMediaFile(file)) return;
    const cacheKey = `${agentId}:${file.path}`;
    if (thumbnailCache[cacheKey]) return;
    try {
      const url = `/api/agents/${agentId}/files/thumbnail?path=${encodeURIComponent(file.path)}&size=128`;
      const response = await fetch(url);
      if (response.ok) {
        const blob = await response.blob();
        const objectUrl = URL.createObjectURL(blob);
        setThumbnailCache(prev => ({ ...prev, [cacheKey]: objectUrl }));
      }
    } catch {}
  };

  const loadFiles = async (path: string) => {
    if (!agentId) return;
    setLoading(true);
    try {
      const res = await apiClient.browseFiles(agentId, path);
      const data: any = res.data;
      if (data && Array.isArray(data.files)) {
        setFiles(data.files);
        setCurrentPath(path);
        for (const f of data.files as FileItem[]) {
          if (isMediaFile(f)) {
            void loadThumbnail(f);
          }
        }
      }
    } catch {
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (agentId) {
      void loadFiles(currentPath);
    }
  }, [agentId]);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="grid grid-cols-4 md:grid-cols-6 lg:grid-cols-8 gap-4">
          {files.map((file, idx) => (
            <div key={idx} className="flex flex-col items-center space-y-2">
              <div className="w-20 h-20 rounded border flex items-center justify-center bg-muted overflow-hidden">
                {isMediaFile(file) && getThumbnail(file) ? (
                  <img
                    src={getThumbnail(file)}
                    alt={file.name}
                    className="w-full h-full object-contain"
                    loading="lazy"
                  />
                ) : (
                  <div className="text-2xl">
                    {file.type === 'directory' ? '📁' : '📄'}
                  </div>
                )}
              </div>
              <div className="text-xs text-center truncate w-full">{file.name}</div>
              {file.size && (
                <Badge variant="secondary" className="text-xs">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </Badge>
              )}
            </div>
          ))}
        </div>
        {loading && <div className="text-center text-muted-foreground mt-4">Loading...</div>}
      </CardContent>
    </Card>
  );
}
