import * as React from "react";
import { useEffect, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogTrigger } from './ui/dialog';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Keyboard } from 'lucide-react';

interface Shortcut {
  key: string;
  description: string;
  category: 'navigation' | 'agents' | 'streaming' | 'commands' | 'general';
}

const shortcuts: Shortcut[] = [
  // Navigation
  { key: 'Ctrl + 1', description: 'Go to Overview', category: 'navigation' },
  { key: 'Ctrl + 2', description: 'Go to Agents', category: 'navigation' },
  { key: 'Ctrl + 3', description: 'Go to Streaming', category: 'navigation' },
  { key: 'Ctrl + 4', description: 'Go to Commands', category: 'navigation' },
  { key: 'Ctrl + 5', description: 'Go to Files', category: 'navigation' },
  { key: 'Ctrl + 6', description: 'Go to Monitoring', category: 'navigation' },
  
  // Agents
  { key: 'Ctrl + A', description: 'Select first online agent', category: 'agents' },
  { key: 'Ctrl + D', description: 'Deselect current agent', category: 'agents' },
  { key: 'ArrowUp/Down', description: 'Navigate through agents', category: 'agents' },
  
  // Streaming
  { key: 'Space', description: 'Start/Stop stream', category: 'streaming' },
  { key: 'F', description: 'Toggle fullscreen', category: 'streaming' },
  { key: 'M', description: 'Mute/Unmute', category: 'streaming' },
  
  // Commands
  { key: 'Ctrl + Enter', description: 'Execute command', category: 'commands' },
  { key: 'Ctrl + L', description: 'Clear command output', category: 'commands' },
  { key: 'Ctrl + H', description: 'Show command history', category: 'commands' },
  
  // General
  { key: 'Ctrl + K', description: 'Open command palette', category: 'general' },
  { key: 'Ctrl + /', description: 'Show shortcuts', category: 'general' },
  { key: 'Ctrl + N', description: 'Open notifications', category: 'general' },
  { key: 'Escape', description: 'Close dialogs/cancel actions', category: 'general' }
];

const categoryNames = {
  navigation: 'Navigation',
  agents: 'Agent Management',
  streaming: 'Streaming Controls',
  commands: 'Command Execution',
  general: 'General'
};

interface KeyboardShortcutsProps {
  onTabChange?: (tab: string) => void;
  onAgentSelect?: () => void;
  onAgentDeselect?: () => void;
}

export function KeyboardShortcuts({ onTabChange, onAgentSelect, onAgentDeselect }: KeyboardShortcutsProps) {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Prevent shortcuts when typing in inputs
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        if (e.key === 'Escape') {
          (e.target as HTMLElement).blur();
        }
        return;
      }

      // Check for Ctrl combinations
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case '1':
            e.preventDefault();
            onTabChange?.('overview');
            break;
          case '2':
            e.preventDefault();
            onTabChange?.('agents');
            break;
          case '3':
            e.preventDefault();
            onTabChange?.('streaming');
            break;
          case '4':
            e.preventDefault();
            onTabChange?.('commands');
            break;
          case '5':
            e.preventDefault();
            onTabChange?.('files');
            break;
          case '6':
            e.preventDefault();
            onTabChange?.('monitoring');
            break;
          case 'a':
            e.preventDefault();
            onAgentSelect?.();
            break;
          case 'd':
            e.preventDefault();
            onAgentDeselect?.();
            break;
          case '/':
            e.preventDefault();
            setIsOpen(true);
            break;
          case 'k':
            e.preventDefault();
            // Command palette would go here
            break;
        }
      }

      // Single key shortcuts
      switch (e.key) {
        case 'Escape':
          setIsOpen(false);
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onTabChange, onAgentSelect, onAgentDeselect]);

  const groupedShortcuts = shortcuts.reduce((acc, shortcut) => {
    if (!acc[shortcut.category]) {
      acc[shortcut.category] = [];
    }
    acc[shortcut.category].push(shortcut);
    return acc;
  }, {} as Record<string, Shortcut[]>);

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm" className="hidden md:flex">
          <Keyboard className="h-4 w-4 mr-2" />
          Shortcuts
        </Button>
      </DialogTrigger>
      
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Keyboard Shortcuts</DialogTitle>
          <DialogDescription>
            Quick access keys to navigate and control the Neural Control Hub interface efficiently.
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6">
          {Object.entries(groupedShortcuts).map(([category, categoryShortcuts]) => (
            <div key={category}>
              <h3 className="text-sm font-medium mb-3">{categoryNames[category as keyof typeof categoryNames]}</h3>
              <div className="space-y-2">
                {categoryShortcuts.map((shortcut, index) => (
                  <div key={index} className="flex items-center justify-between py-2 px-3 rounded bg-muted/50">
                    <span className="text-sm">{shortcut.description}</span>
                    <Badge variant="secondary" className="font-mono text-xs">
                      {shortcut.key}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-6 p-4 bg-muted rounded-lg">
          <p className="text-xs text-muted-foreground">
            💡 Press <Badge variant="secondary" className="mx-1 font-mono">Ctrl + /</Badge> to open this dialog anytime
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}