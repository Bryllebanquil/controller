import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useSocket } from './SocketProvider';

export function Login() {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  
  const { login } = useSocket();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const resp = await login(password);
      if (resp?.success) {
        return;
      }
      setError(resp?.error || 'Login failed. Check password.');
    } catch (error) {
      setError('Login failed. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    (async () => {
      try {
        const p = new URLSearchParams(window.location.search);
        let t = p.get('supabase_token') || '';
        if (!t && typeof window !== 'undefined') {
          const hash = (window.location.hash || '').replace(/^#/, '');
          if (hash) {
            const hp = new URLSearchParams(hash);
            t = hp.get('access_token') || hp.get('token') || '';
            if (t) {
              try {
                const newUrl = window.location.origin + window.location.pathname + window.location.search;
                window.history.replaceState({}, document.title, newUrl);
              } catch {}
            }
          }
        }
        if (t) {
          try { (globalThis as any).__SUPABASE_JWT__ = t; } catch {}
          try { localStorage.setItem('supabase_token', t); } catch {}
        }
      } catch {}
    })();
  }, []);
  
  // Removed auto-enroll to prevent repeated unauthorized calls while typing.
  // Enrollment is triggered explicitly via button or after login indicates not enrolled.

  

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <Shield className="h-8 w-8 text-primary" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold">Neural Control Hub</CardTitle>
            <CardDescription className="text-base">
              Advanced Agent Management System
            </CardDescription>
          </div>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            <div className="space-y-2">
              <label htmlFor="password" className="text-sm font-medium">
                Admin Password
              </label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  className="pr-10"
                  disabled={isLoading}
                  autoFocus
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <Eye className="h-4 w-4 text-muted-foreground" />
                  )}
                </Button>
              </div>
            </div>
            
           
            
            <Button 
              type="submit" 
              className="w-full" 
              disabled={!password.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Authenticating...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
            
            
          </form>
          
          <div className="mt-6 pt-6 border-t text-center text-xs text-muted-foreground">
            <p>Secure authentication required</p>
            <p className="mt-1">Contact your administrator for access credentials</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
