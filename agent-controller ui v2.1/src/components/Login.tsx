import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Alert, AlertDescription } from './ui/alert';
import { Badge } from './ui/badge';
import { Shield, Eye, EyeOff, Loader2 } from 'lucide-react';
import { useSocket } from './SocketProvider';
import apiClient from '../services/api';

export function Login() {
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [otp, setOtp] = useState('');
  const [qrUri, setQrUri] = useState('');
  const [totpInfo, setTotpInfo] = useState<{ enabled: boolean; enrolled: boolean; verified_once?: boolean; issuer?: string } | null>(null);
  
  const { login } = useSocket();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      if (totpInfo?.enrolled && (otp.trim().length !== 6)) {
        setError('Enter the 6-digit OTP from your Auth-App.');
        setIsLoading(false);
        return;
      }
      const resp = await login(password, otp.trim() || undefined);
      if (resp?.success) {
        return;
      }
      const requiresTotp = !!(resp?.data && (resp.data as any).requires_totp);
      const showQr = !!(resp?.data && (resp.data as any).show_qr);
      if (showQr) {
        const uri = (resp?.data as any).uri || '';
        if (uri) setQrUri(uri);
        setTotpInfo({ enabled: false, enrolled: true, verified_once: false, issuer: (totpInfo?.issuer || 'Neural Control Hub') });
        setError('Scan the QR and enter the OTP to sign in.');
      } else if (requiresTotp) {
        setError('Enter the 6-digit OTP from your Auth-App.');
      } else {
        setError(resp?.error || 'Login failed. Check password or OTP.');
      }
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
        const t = p.get('supabase_token');
        if (t) {
          try { (globalThis as any).__SUPABASE_JWT__ = t; } catch {}
          try { localStorage.setItem('supabase_token', t); } catch {}
        }
      } catch {}
      const res = await apiClient.getTotpStatus();
      if (res.success && res.data) {
        setTotpInfo(res.data);
      }
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
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label htmlFor="otp" className="text-sm font-medium">
                  Auth-App OTP
                </label>
                {totpInfo ? (
                  <Badge variant={totpInfo.verified_once ? 'default' : 'secondary'} className="text-xs">
                    {totpInfo.verified_once ? 'Enrolled' : 'Not enrolled'}
                  </Badge>
                ) : null}
              </div>
              <Input
                id="otp"
                type="text"
                inputMode="numeric"
                pattern="[0-9]*"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="6-digit code"
                disabled={isLoading}
              />
              <div className="text-xs text-muted-foreground">
                {totpInfo?.enrolled ? 'Two-factor authentication is required' : 'Two-factor authentication is optional'}
              </div>
            </div>
            
            <Button 
              type="submit" 
              className="w-full" 
              disabled={!password.trim() || isLoading || (totpInfo?.enrolled ? otp.trim().length !== 6 : false)}
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
            
            {qrUri ? (
              <div className="space-y-2">
                <div className="text-sm font-medium">Set up Auth-App (Google Authenticator)</div>
                <div className="text-xs text-muted-foreground">
                  Scan the QR and enter OTP to sign in
                </div>
                <div className="mt-2 flex justify-center">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?data=${encodeURIComponent(qrUri)}&size=220x220`}
                    alt="Scan with Authenticator"
                    className="border rounded p-2"
                  />
                </div>
              </div>
            ) : null}
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
