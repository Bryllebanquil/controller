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

  return (
    <>
      {/* Mobile/Laptop Overlay - Starts below header */}
      {isOpen && (
        <div 
          className="fixed inset-x-0 top-16 bottom-0 bg-black/50 z-[60] xl:hidden"
          role="button"
          aria-label="Close menu overlay"
          tabIndex={0}
          onClick={() => onClose?.()}
          onKeyDown={(e) => {
            if (e.key === 'Escape' || e.key === 'Enter' || e.key === ' ') onClose?.();
          }}
        />
      )}
      
      {/* Sidebar */}
      <div id="app-sidebar" aria-hidden={!isOpen} ref={containerRef} className={cn(
        "fixed xl:sticky xl:top-16 left-0 top-16 bottom-0 z-[70] w-[260px] border-r bg-background flex-shrink-0 transition-transform duration-300 ease-in-out xl:translate-x-0 xl:bottom-auto xl:h-[calc(100vh-4rem)]",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-full flex-col">
          {/* Mobile Close Button */}
          <div className="xl:hidden flex items-center justify-between p-4 border-b">
            <h2 className="text-lg font-semibold">Menu</h2>
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
            >
              <X className="h-5 w-5" />
            </Button>
          </div>
          
          <div className="flex-1 overflow-auto p-4">
            <nav className="space-y-1">
              {sidebarItems.map((item) => {
                const Icon = item.icon;
                return (
                  <Button
                    key={item.id}
                    variant={activeTab === item.id ? "secondary" : "ghost"}
                    className={cn(
                      "w-full justify-start h-10",
                      activeTab === item.id && "bg-secondary"
                    )}
                    onClick={() => onTabChange(item.id)}
                  >
                    <Icon className="mr-2 h-4 w-4 flex-shrink-0" />
                    <span className="flex-1 text-left">{item.label}</span>
                    {item.id === 'agents' && (
                      <Badge variant="secondary" className="ml-2 h-5 text-xs">
                        {agentCount}
                      </Badge>
                    )}
                    {item.badge && (
                      <Badge variant="default" className="ml-2 h-5 text-xs">
                        {item.badge}
                      </Badge>
                    )}
                  </Button>
                );
              })}
            </nav>
          </div>
          
          <div className="border-t p-4 flex-shrink-0">
            <div className="space-y-1">
              <Button 
                variant={activeTab === 'settings' ? "secondary" : "ghost"} 
                className="w-full justify-start h-9" 
                size="sm"
                onClick={() => onTabChange('settings')}
              >
                <SettingsIcon className="mr-2 h-4 w-4" />
                Settings
              </Button>
              <Button 
                variant={activeTab === 'about' ? "secondary" : "ghost"} 
                className="w-full justify-start h-9" 
                size="sm"
                onClick={() => onTabChange('about')}
              >
                <HelpCircle className="mr-2 h-4 w-4" />
                About
              </Button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}