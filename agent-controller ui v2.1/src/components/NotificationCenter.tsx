import * as React from "react";
import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger } from './ui/sheet';
import { 
  Bell, 
  X, 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  Wifi, 
  WifiOff,
  Shield,
  Terminal,
  Activity
} from 'lucide-react';
import { cn } from './ui/utils';

interface Notification {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  agentId?: string;
  read: boolean;
  category: 'agent' | 'system' | 'security' | 'command';
}

const mockNotifications: Notification[] = [];

const notificationIcons = {
  success: CheckCircle,
  warning: AlertTriangle,
  error: Shield,
  info: Info
};

const categoryIcons = {
  agent: Wifi,
  system: Activity,
  security: Shield,
  command: Terminal
};

export function NotificationCenter() {
  const [notifications, setNotifications] = useState<Notification[]>(mockNotifications);
  const [filter, setFilter] = useState<'all' | 'unread' | 'agent' | 'system' | 'security'>('all');
  
  const unreadCount = notifications.filter(n => !n.read).length;
  
  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !notification.read;
    return notification.category === filter;
  });

  const markAsRead = (id: string) => {
    setNotifications(prev => prev.map(n => 
      n.id === id ? { ...n, read: true } : n
    ));
  };

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Remove simulated notifications in production; rely on real events

  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="sm" className="relative">
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs">
              {unreadCount > 9 ? '9+' : unreadCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      
      <SheetContent className="w-96 sm:w-[540px]">
        <SheetHeader>
          <SheetTitle className="flex items-center justify-between">
            <span>Notifications</span>
            {unreadCount > 0 && (
              <Button variant="ghost" size="sm" onClick={markAllAsRead}>
                Mark all as read
              </Button>
            )}
          </SheetTitle>
          <SheetDescription>
            System alerts, status updates, and important notifications from your connected agents.
          </SheetDescription>
        </SheetHeader>
        
        <div className="mt-6 space-y-4">
          {/* Filter buttons */}
          <div className="flex flex-wrap gap-2">
            {[
              { key: 'all', label: 'All' },
              { key: 'unread', label: 'Unread' },
              { key: 'agent', label: 'Agents' },
              { key: 'system', label: 'System' },
              { key: 'security', label: 'Security' }
            ].map(({ key, label }) => (
              <Button
                key={key}
                variant={filter === key ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter(key as any)}
              >
                {label}
                {key === 'unread' && unreadCount > 0 && (
                  <Badge className="ml-1 h-4 w-4 p-0 text-xs">{unreadCount}</Badge>
                )}
              </Button>
            ))}
          </div>
          
          {/* Notifications list */}
          <ScrollArea className="h-[calc(100vh-200px)]">
            <div className="space-y-3">
              {filteredNotifications.length === 0 ? (
                <div className="text-center text-muted-foreground py-8">
                  <Bell className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p>No notifications</p>
                </div>
              ) : (
                filteredNotifications.map((notification) => {
                  const NotificationIcon = notificationIcons[notification.type];
                  const CategoryIcon = categoryIcons[notification.category];
                  
                  return (
                    <div
                      key={notification.id}
                      className={cn(
                        "p-4 rounded-lg border transition-all hover:bg-accent/50",
                        !notification.read && "bg-muted/50 border-primary/20"
                      )}
                      onClick={() => markAsRead(notification.id)}
                    >
                      <div className="flex items-start justify-between space-x-3">
                        <div className="flex items-start space-x-3 flex-1">
                          <div className={cn(
                            "mt-0.5 p-1 rounded-full",
                            notification.type === 'success' && "text-green-600 bg-green-100",
                            notification.type === 'warning' && "text-yellow-600 bg-yellow-100",
                            notification.type === 'error' && "text-red-600 bg-red-100",
                            notification.type === 'info' && "text-blue-600 bg-blue-100"
                          )}>
                            <NotificationIcon className="h-3 w-3" />
                          </div>
                          
                          <div className="flex-1 space-y-1">
                            <div className="flex items-center space-x-2">
                              <p className="text-sm font-medium">{notification.title}</p>
                              {!notification.read && (
                                <div className="w-2 h-2 bg-primary rounded-full"></div>
                              )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                              {notification.message}
                            </p>
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                              <CategoryIcon className="h-3 w-3" />
                              <span className="capitalize">{notification.category}</span>
                              <span>•</span>
                              <span>{notification.timestamp.toLocaleTimeString()}</span>
                              {notification.agentId && (
                                <>
                                  <span>•</span>
                                  <span>{notification.agentId.substring(0, 8)}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteNotification(notification.id);
                          }}
                          className="h-6 w-6 p-0"
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </div>
      </SheetContent>
    </Sheet>
  );
}