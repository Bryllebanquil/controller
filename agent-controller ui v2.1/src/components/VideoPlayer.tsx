import { useEffect, useMemo, useRef, useState } from "react";
import Hls from "hls.js";
import apiClient, { StreamSource, Video } from "../services/api";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";

interface SourceState extends StreamSource {
  type: "mp4" | "hls";
}

export function VideoPlayer() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [source, setSource] = useState<SourceState | null>(null);
  const [loading, setLoading] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [hlsInstance, setHlsInstance] = useState<any>(null);

  useEffect(() => {
    let mounted = true;
    apiClient.getVideos().then((res) => {
      if (mounted && res.success && res.data) {
        setVideos(res.data.videos || []);
        if ((res.data.videos || []).length > 0) {
          setSelectedVideoId(res.data.videos[0].id);
        }
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    let mounted = true;
    if (!selectedVideoId) {
      setSource(null);
      return;
    }
    setLoading(true);
    apiClient.getStreamSource(selectedVideoId).then((res) => {
      setLoading(false);
      if (!mounted) return;
      if (res.success && res.data) {
        const s = res.data as SourceState;
        setSource(s);
      } else {
        setSource(null);
      }
    });
    return () => {
      mounted = false;
    };
  }, [selectedVideoId]);

  useEffect(() => {
    if (hlsInstance) {
      try {
        hlsInstance.destroy();
      } catch {}
      setHlsInstance(null);
    }
    const video = videoRef.current;
    if (!video || !source) return;
    if (source.type === "hls") {
      if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(source.url);
        hls.attachMedia(video);
        setHlsInstance(hls);
      } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
        video.src = source.url;
      }
    } else if (source.type === "mp4") {
      video.src = source.url;
    }
    return () => {
      if (hlsInstance) {
        try {
          hlsInstance.destroy();
        } catch {}
      }
    };
  }, [source]);

  const selectedVideo = useMemo(
    () => videos.find((v) => v.id === selectedVideoId),
    [videos, selectedVideoId]
  );

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Videos</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              {(videos || []).map((v) => (
                <div
                  key={v.id}
                  className={`flex items-center justify-between rounded-md border p-3 ${
                    selectedVideoId === v.id
                      ? "border-primary"
                      : "border-muted"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="text-sm font-medium">{v.title}</div>
                    <div className="text-xs text-muted-foreground">
                      {(v.duration || 0) >= 900 ? "Long" : "Short"} •{" "}
                      {Math.round((v.duration || 0) / 60)} min
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">
                      {(v.duration || 0) >= 900 ? "HLS" : "MP4"}
                    </Badge>
                    <Button
                      size="sm"
                      variant={
                        selectedVideoId === v.id ? "default" : "outline"
                      }
                      onClick={() => setSelectedVideoId(v.id)}
                    >
                      Play
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            <div className="lg:col-span-2">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm">
                    {selectedVideo ? selectedVideo.title : "No selection"}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {source ? source.type.toUpperCase() : ""}
                  </div>
                </div>
                <div className="relative aspect-video w-full rounded-md overflow-hidden border">
                  <video
                    ref={videoRef}
                    id="video-player"
                    className="w-full h-full bg-black"
                    controls
                    preload="metadata"
                  >
                    {source && source.type === "mp4" && (
                      <source src={source.url} type="video/mp4" />
                    )}
                  </video>
                </div>
                {loading && (
                  <div className="text-xs text-muted-foreground">
                    Loading source...
                  </div>
                )}
                {!loading && source && source.type === "hls" && (
                  <div className="text-xs text-muted-foreground">
                    If playback fails, try Safari which supports HLS natively.
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
      <Tabs defaultValue="notes" className="space-y-4">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="notes">Notes</TabsTrigger>
          <TabsTrigger value="details">Details</TabsTrigger>
        </TabsList>
        <TabsContent value="notes">
          <Card>
            <CardContent className="p-4 text-sm text-muted-foreground">
              MP4 is used for previews and shorter videos. HLS is used for long videos and unstable networks.
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="details">
          <Card>
            <CardContent className="p-4 text-sm text-muted-foreground">
              URLs are short-lived and signed. The player decides between MP4 and HLS based on backend selection.
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

