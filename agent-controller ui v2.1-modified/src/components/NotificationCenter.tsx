import React from 'react';
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
import { useSocket } from './SocketProvider';
import { apiClient } from '../services/api';
import { toast } from 'sonner';

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
  const [notifications, setNotifications] = useState([] as Notification[]);
  const [filter, setFilter] = useState('all' as 'all' | 'unread' | 'agent' | 'system' | 'security');
  const [loading, setLoading] = useState(false);
  const { socket } = useSocket();
  
  const unreadCount = notifications.filter(n => !n.read).length;
  
  const filteredNotifications = notifications.filter(notification => {
    if (filter === 'all') return true;
    if (filter === 'unread') return !notification.read;
    return notification.category === filter;
  });

  // Load notifications from API
  const loadNotifications = async () => {
    try {
      setLoading(true);
      // Use fetch directly since apiClient doesn't have generic get method
      const response = await fetch('/api/notifications?limit=100', {
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      if (data.success) {
        const apiNotifications = data.notifications.map((n: any) => ({
          ...n,
          timestamp: new Date(n.timestamp),
          read: n.read || false
        }));
        setNotifications(apiNotifications);
      }
    } catch (error) {
      console.error('Failed to load notifications:', error);
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (id: string) => {
    try {
      await fetch(`/api/notifications/${id}/read`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      setNotifications(prev => prev.map(n => 
        n.id === id ? { ...n, read: true } : n
      ));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await fetch('/api/notifications/read-all', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
    }
  };

  const deleteNotification = async (id: string) => {
    try {
      await fetch(`/api/notifications/${id}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' }
      });
      setNotifications(prev => prev.filter(n => n.id !== id));
    } catch (error) {
      console.error('Failed to delete notification:', error);
    }
  };

  // Load notifications on mount
  useEffect(() => {
    loadNotifications();
  }, []);

  // Listen for real-time notifications via Socket.IO
  useEffect(() => {
    if (!socket) return;

    const handleNotification = (notification: any) => {
      console.log('🔔 NotificationCenter: Received notification via socket:', notification);
      const newNotification: Notification = {
        ...notification,
        timestamp: new Date(notification.timestamp),
        read: false
      };
      setNotifications(prev => [newNotification, ...prev]);
      
      // Show popup toast notification
      showToast(newNotification);
    };

    socket.on('notification', handleNotification);
    
    return () => {
      socket.off('notification', handleNotification);
    };
  }, [socket]);

  // Also listen via custom window event as backup
  useEffect(() => {
    const handleWindowNotification = (event: any) => {
      console.log('🔔 NotificationCenter: Received notification via window event:', event.detail);
      const notification = event.detail;
      const newNotification: Notification = {
        ...notification,
        timestamp: new Date(notification.timestamp),
        read: false
      };
      setNotifications(prev => [newNotification, ...prev]);
      
      // Show popup toast notification
      showToast(newNotification);
    };

    window.addEventListener('socket_notification', handleWindowNotification);
    
    return () => {
      window.removeEventListener('socket_notification', handleWindowNotification);
    };
  }, []);
  
  // Show toast popup for new notifications
  const showToast = (notification: Notification) => {
    const icon = React.createElement(notificationIcons[notification.type], { 
      className: "h-5 w-5" 
    });
    
    switch (notification.type) {
      case 'success':
        toast.success(notification.title, {
          description: notification.message,
          icon: icon,
        });
        break;
      case 'error':
        toast.error(notification.title, {
          description: notification.message,
          icon: icon,
        });
        break;
      case 'warning':
        toast.warning(notification.title, {
          description: notification.message,
          icon: icon,
        });
        break;
      case 'info':
      default:
        toast.info(notification.title, {
          description: notification.message,
          icon: icon,
        });
        break;
    }
  };

  return React.createElement(Sheet, null,
    React.createElement(SheetTrigger, { asChild: true },
      React.createElement(Button, {
        variant: "ghost",
        size: "sm",
        className: "relative"
      }, React.createElement(Bell, { className: "h-4 w-4" }), unreadCount > 0 && React.createElement(Badge, {
        className: "absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs"
      }, unreadCount > 9 ? '9+' : unreadCount))
    ),
    React.createElement(SheetContent, { className: "w-96 sm:w-[540px]" }, 
      React.createElement(SheetHeader, null,
        React.createElement(SheetTitle, { className: "flex items-center justify-between" },
          React.createElement("span", null, "Notifications"),
          unreadCount > 0 && React.createElement(Button, {
            variant: "ghost",
            size: "sm",
            onClick: markAllAsRead
          }, "Mark all as read")
        ),
        React.createElement(SheetDescription, null,
          "System alerts, status updates, and important notifications from your connected agents."
        )
      ),
      React.createElement("div", { className: "mt-6 space-y-4" }, 
        React.createElement("div", { className: "flex flex-wrap gap-2" }, 
          [
            { key: 'all', label: 'All' },
            { key: 'unread', label: 'Unread' },
            { key: 'agent', label: 'Agents' },
            { key: 'system', label: 'System' },
            { key: 'security', label: 'Security' }
          ].map(({ key, label }) => {
            return React.createElement(Button, {
              key: key,
              variant: filter === key ? 'default' : 'outline',
              size: "sm",
              onClick: () => setFilter(key as any)
            }, label, key === 'unread' && unreadCount > 0 && React.createElement(Badge, {
              className: "ml-1 h-4 w-4 p-0 text-xs"
            }, unreadCount));
          })
        ),
        React.createElement(ScrollArea, { className: "h-[calc(100vh-200px)]" },
          React.createElement("div", { className: "space-y-3" },
            loading ? React.createElement("div", { className: "text-center text-muted-foreground py-8" },
              React.createElement(Activity, { className: "h-12 w-12 mx-auto mb-2 opacity-50 animate-spin" }),
              React.createElement("p", null, "Loading notifications...")
            ) : filteredNotifications.length === 0 ? React.createElement("div", { className: "text-center text-muted-foreground py-8" },
              React.createElement(Bell, { className: "h-12 w-12 mx-auto mb-2 opacity-50" }),
              React.createElement("p", null, "No notifications")
            ) : filteredNotifications.map((notification) => {
              const NotificationIcon = notificationIcons[notification.type];
              const CategoryIcon = categoryIcons[notification.category];
              
              return React.createElement("div", {
                key: notification.id,
                className: cn(
                  "p-4 rounded-lg border transition-all hover:bg-accent/50",
                  !notification.read && "bg-muted/50 border-primary/20"
                ),
                onClick: () => markAsRead(notification.id)
              },
                React.createElement("div", { className: "flex items-start justify-between space-x-3" },
                  React.createElement("div", { className: "flex items-start space-x-3 flex-1" },
                    React.createElement("div", {
                      className: cn(
                        "mt-0.5 p-1 rounded-full",
                        notification.type === 'success' && "text-green-600 bg-green-100",
                        notification.type === 'warning' && "text-yellow-600 bg-yellow-100",
                        notification.type === 'error' && "text-red-600 bg-red-100",
                        notification.type === 'info' && "text-blue-600 bg-blue-100"
                      )
                    }, React.createElement(NotificationIcon, { className: "h-3 w-3" })),
                    React.createElement("div", { className: "flex-1 space-y-1" },
                      React.createElement("div", { className: "flex items-center space-x-2" },
                        React.createElement("p", { className: "text-sm font-medium" }, notification.title),
                        !notification.read && React.createElement("div", { className: "w-2 h-2 bg-primary rounded-full" })
                      ),
                      React.createElement("p", { className: "text-xs text-muted-foreground" }, notification.message),
                      React.createElement("div", { className: "flex items-center space-x-2 text-xs text-muted-foreground" },
                        React.createElement(CategoryIcon, { className: "h-3 w-3" }),
                        React.createElement("span", { className: "capitalize" }, notification.category),
                        React.createElement("span", null, "•"),
                        React.createElement("span", null, notification.timestamp.toLocaleTimeString()),
                        notification.agentId && React.createElement(React.Fragment, null,
                          React.createElement("span", null, "•"),
                          React.createElement("span", null, notification.agentId.substring(0, 8))
                        )
                      )
                    )
                  ),
                  React.createElement(Button, {
                    variant: "ghost",
                    size: "sm",
                    onClick: (e: any) => {
                      e.stopPropagation();
                      deleteNotification(notification.id);
                    },
                    className: "h-6 w-6 p-0"
                  }, React.createElement(X, { className: "h-3 w-3" }))
                )
              );
            })
          )
        )
      )
    )
  );
}