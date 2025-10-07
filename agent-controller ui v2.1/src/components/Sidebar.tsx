import { cn } from './ui/utils';
import { useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  BarChart3, 
  Monitor, 
  Terminal, 
  Files, 
  Activity, 
  Users,
  Settings as SettingsIcon,
  HelpCircle,
  Zap,
  Mic,
  X
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  agentCount: number;
  isOpen?: boolean;
  onClose?: () => void;
}

const sidebarItems = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'agents', label: 'Agents', icon: Users },
  { id: 'streaming', label: 'Streaming', icon: Monitor },
  { id: 'commands', label: 'Commands', icon: Terminal },
  { id: 'files', label: 'Files', icon: Files },
  { id: 'voice', label: 'Voice Control', icon: Mic, badge: 'AI' },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
  { id: 'webrtc', label: 'WebRTC Pro', icon: Zap, badge: 'NEW' },
];

export function Sidebar({ activeTab, onTabChange, agentCount, isOpen = true, onClose }: SidebarProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Click-outside to close (mobile/tablet only)
  useEffect(() => {
    const handlePointer = (e: MouseEvent | TouchEvent) => {
      if (!isOpen) return;
      if (typeof window !== 'undefined' && window.innerWidth >= 1280) return; // only below xl
      const target = e.target as Node | null;
      if (containerRef.current && target && !containerRef.current.contains(target)) {
        onClose?.();
      }
    };
    document.addEventListener('mousedown', handlePointer);
    document.addEventListener('touchstart', handlePointer, { passive: true });
    return () => {
      document.removeEventListener('mousedown', handlePointer);
      document.removeEventListener('touchstart', handlePointer as any);
    };
  }, [isOpen, onClose]);

  return null;
}