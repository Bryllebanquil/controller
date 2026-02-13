import { useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { StreamViewer } from "./StreamViewer";
import { useSocket } from "./SocketProvider";
import { AlertCircle, Monitor, Camera } from "lucide-react";

export function VirtualDesktop({ agentId }: { agentId: string | null }) {
  const { setLastActivity, startStream, agents } = useSocket();

  useEffect(() => {
    try {
      setLastActivity("virtual_desktop", "opened", agentId || null);
    } catch {}
  }, [agentId, setLastActivity]);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Monitor className="h-4 w-4" />
              Virtual Desktop
            </CardTitle>
            {agentId && (
              <Badge variant="outline" className="text-xs">
                {(() => {
                  const a = agents.find(x => x.id === agentId);
                  return a ? a.name : agentId;
                })()}
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent>
          {!agentId ? (
            <div className="text-center text-muted-foreground py-16">
              <AlertCircle className="h-10 w-10 mx-auto mb-2 opacity-50" />
              <div>Select an agent to start the virtual desktop</div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="relative overflow-visible">
                <StreamViewer agentId={agentId} type="screen" title="Desktop Screen" defaultCaptureMouse={false} defaultCaptureKeyboard={false} autoResume={false} hideCursor={true} />
              </div>
              <div className="space-y-4">
                <div className="text-xs text-muted-foreground flex items-center gap-2">
                  <Camera className="h-3 w-3" />
                  Optional Camera Stream
                </div>
                <div className="relative overflow-visible">
                  <StreamViewer agentId={agentId} type="camera" title="Camera" defaultCaptureMouse={false} defaultCaptureKeyboard={false} autoResume={false} hideCursor={true} />
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
