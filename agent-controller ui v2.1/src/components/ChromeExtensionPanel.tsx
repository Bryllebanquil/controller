import { useEffect, useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Badge } from "./ui/badge";
import apiClient from "../services/api";
import { toast } from "sonner";

export function ChromeExtensionPanel() {
  const [url, setUrl] = useState<string>("");
  const [extId, setExtId] = useState<string>("cicnkiabgagcfkheiplebojnbjpldlff");
  const [displayName, setDisplayName] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    let mounted = true;
    (async () => {
      const res = await apiClient.getExtensionConfig();
      if (res?.success && res.data) {
        const d: any = res.data;
        if (!mounted) return;
        setUrl(String(d.download_url || ""));
        setExtId(String(d.extension_id || "cicnkiabgagcfkheiplebojnbjpldlff"));
        setDisplayName(String(d.display_name || ""));
      }
    })();
    return () => { mounted = false; };
  }, []);

  const handleSave = async () => {
    setSaving(true);
    const res = await apiClient.setExtensionConfig(url.trim(), extId.trim(), displayName.trim());
    setSaving(false);
    if (res?.success) {
      try {
        const d: any = res.data;
        if (d?.extension_id) setExtId(String(d.extension_id));
        if (typeof d?.display_name === 'string') setDisplayName(String(d.display_name));
      } catch {}
      toast.success("Chrome Extension config saved");
      setLastUpdated(new Date().toLocaleTimeString());
    } else {
      toast.error(res?.error || "Failed to save config");
    }
  };

  return (
    <Card className="bg-background">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Chrome Extension</CardTitle>
            <CardDescription>Provide a ZIP or CRX link (folder ZIP supported, including MEGA). Agents download, unpack, and install with enterprise policy.</CardDescription>
          </div>
          {lastUpdated ? <Badge variant="secondary">Updated {lastUpdated}</Badge> : null}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">Remote ZIP/CRX URL</div>
            <Input
              placeholder="https://mega.nz/file/...#... or https://.../extension.zip"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="font-mono"
            />
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">Display Name (optional)</div>
            <Input
              placeholder="Rename extension display name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <div className="text-xs text-muted-foreground">Extension ID</div>
            <Input
              placeholder="cicnkiabgagcfkheiplebojnbjpldlff"
              value={extId}
              onChange={(e) => setExtId(e.target.value)}
              className="font-mono"
            />
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleSave} disabled={saving}>{saving ? "Saving..." : "Save"}</Button>
          </div>
          <div className="text-xs text-muted-foreground">
            - Agents periodically fetch and auto-install if missing (policy enforced).<br/>
            - Folder ZIPs are unpacked locally; manifest name is updated if provided.<br/>
            - Extension ID is required for policy and updates (Chrome matches CRX key to ID).
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
