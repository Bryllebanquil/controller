import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Shield, Loader2 } from 'lucide-react';
import { useSocket } from './SocketProvider';
import apiClient from '../services/api';
import { toast } from 'sonner';

export function TwoFactor() {
  const { login } = useSocket();
  const [otp, setOtp] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showQr, setShowQr] = useState(false);
  const [qrB64, setQrB64] = useState<string | null>(null);
  const [issuer, setIssuer] = useState<string>('Neural Control Hub');
  const [digits, setDigits] = useState<number>(6);
  const inputsRef = useRef<Array<HTMLInputElement | null>>([]);

  useEffect(() => {
    (async () => {
      try {
        const url = new URL(window.location.href);
        if (url.searchParams.has('tab')) {
          url.searchParams.delete('tab');
          window.history.replaceState({}, '', url.toString());
        }
      } catch {}
      try {
        const nav = (performance && typeof performance.getEntriesByType === 'function') ? performance.getEntriesByType('navigation') : [];
        const isReload = Array.isArray(nav) && nav[0] && (nav[0] as any).type === 'reload';
        if (isReload) {
          backToPassword();
          return;
        }
      } catch {}
      try {
        const raw = sessionStorage.getItem('nch:pending_totp');
        if (raw) {
          const d = JSON.parse(raw);
          setShowQr(!!d?.show_qr);
          setQrB64(d?.qr_png_b64 || null);
          setIssuer(d?.issuer || 'Neural Control Hub');
          setDigits(d?.digits || 6);
        } else {
          const check = await apiClient.totpCheck();
          const d: any = (check as any)?.data || {};
          if (d?.present === true) {
            setShowQr(false);
            setDigits(d?.digits || 6);
            setIssuer(d?.issuer || 'Neural Control Hub');
          } else if (d?.show_qr) {
            setShowQr(true);
            setQrB64(d?.qr_png_b64 || null);
            setIssuer(d?.issuer || 'Neural Control Hub');
            setDigits(d?.digits || 6);
          }
        }
      } catch {}
      try {
        const pwd = sessionStorage.getItem('nch:pending_login_password') || '';
        const ts = Number(sessionStorage.getItem('nch:pending_login_password_ts') || '0');
        const tooOld = !ts || (Date.now() - ts) > 120000;
        if (!pwd) {
          window.location.replace('/login');
        } else if (tooOld) {
          backToPassword();
          return;
        }
      } catch {
        try { window.location.replace('/login'); } catch {}
      }
    })();
  }, []);

  const backToPassword = () => {
    try { sessionStorage.removeItem('nch:pending_login_password'); } catch {}
    try { sessionStorage.removeItem('nch:pending_totp'); } catch {}
    try { window.location.replace('/login'); } catch {}
  };

  const applyOtpFromInputs = () => {
    const value = inputsRef.current.map((el) => (el?.value || '').trim()).join('');
    setOtp(value.replace(/\D+/g, '').slice(0, digits));
  };

  const handleDigitChange = (idx: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const v = (e.target.value || '').replace(/\D+/g, '');
    e.target.value = v.slice(0, 1);
    applyOtpFromInputs();
    if (v && inputsRef.current[idx + 1]) {
      inputsRef.current[idx + 1]?.focus();
    }
  };

  const handleKeyDown = (idx: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (/^[0-9]$/.test(e.key)) {
      e.preventDefault();
      const ch = e.key;
      if (inputsRef.current[idx]) {
        inputsRef.current[idx]!.value = ch;
      }
      applyOtpFromInputs();
      if (inputsRef.current[idx + 1]) {
        inputsRef.current[idx + 1]?.focus();
      }
      return;
    }
    if (e.key === 'Backspace' && !inputsRef.current[idx]?.value && inputsRef.current[idx - 1]) {
      inputsRef.current[idx - 1]?.focus();
    }
    if (e.key === 'ArrowLeft' && inputsRef.current[idx - 1]) {
      e.preventDefault();
      inputsRef.current[idx - 1]?.focus();
    }
    if (e.key === 'ArrowRight' && inputsRef.current[idx + 1]) {
      e.preventDefault();
      inputsRef.current[idx + 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const text = (e.clipboardData.getData('text') || '').replace(/\D+/g, '').slice(0, digits);
    if (!text) return;
    for (let i = 0; i < digits; i++) {
      const ch = text[i] || '';
      if (inputsRef.current[i]) {
        inputsRef.current[i]!.value = ch;
      }
    }
    applyOtpFromInputs();
    const lastIdx = Math.min(text.length, digits) - 1;
    if (lastIdx >= 0 && inputsRef.current[lastIdx]) {
      inputsRef.current[lastIdx]?.focus();
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otp.length !== digits) {
      const msg = 'Enter the 6-digit code from your authenticator.';
      setError(msg);
      toast.error(msg);
      return;
    }
    setIsLoading(true);
    setError('');
    try {
      const pwd = sessionStorage.getItem('nch:pending_login_password') || '';
      if (!pwd) {
        toast.error('Password step expired. Please login again.');
        backToPassword();
        return;
      }
      const resp = await login(pwd, otp);
      if (resp?.success) {
        try { sessionStorage.removeItem('nch:pending_login_password'); } catch {}
        try { sessionStorage.removeItem('nch:pending_totp'); } catch {}
        return;
      }
      const d: any = (resp as any)?.data || {};
      if (d?.totp_required) {
        setShowQr(!!d?.show_qr);
        setIssuer(d?.issuer || 'Neural Control Hub');
        setQrB64(d?.qr_png_b64 || null);
        setDigits(d?.digits || 6);
        const msg = d?.error || 'Invalid code. Try again.';
        setError(msg);
        toast.error(msg);
      } else {
        const msg = resp?.error || d?.error || 'Login failed.';
        setError(msg);
        toast.error(msg);
        if (/password/i.test(String(msg))) {
          backToPassword();
        }
      }
    } catch {
      const msg = 'Verification failed. Check your connection and try again.';
      setError(msg);
      toast.error(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-4 text-center">
          <div className="mx-auto w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
            <Shield className="h-8 w-8 text-primary" />
          </div>
          <div>
            <CardTitle className="text-2xl font-bold">Two-Factor Authentication</CardTitle>
            <CardDescription className="text-base">
              Enter the 6‑digit code to continue
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleVerify} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            {showQr && qrB64 && (
              <div className="flex flex-col items-center space-y-2">
                <img src={`data:image/png;base64,${qrB64}`} alt="TOTP QR" className="w-48 h-48" />
                <div className="text-xs text-muted-foreground">Scan in {issuer}</div>
              </div>
            )}
            <div className="space-y-3">
              <div
                className="mx-auto w-full max-w-xs select-none"
                onPaste={handlePaste}
              >
                <div className="p-[2px] rounded-2xl bg-gradient-to-r from-indigo-500 via-sky-500 to-emerald-500">
                  <div className="rounded-2xl bg-background/80 backdrop-blur-sm p-3">
                    <div className="flex items-center justify-between gap-2">
                      {Array.from({ length: digits }).map((_, i) => (
                        <input
                          key={i}
                          ref={(el) => (inputsRef.current[i] = el)}
                          inputMode="numeric"
                          pattern="[0-9]*"
                          maxLength={1}
                          className="w-12 h-14 text-center text-2xl font-semibold rounded-xl border border-zinc-800/70 bg-zinc-950/60 focus:outline-none focus:border-transparent focus:ring-2 focus:ring-indigo-500 text-foreground caret-transparent"
                          onChange={(e) => handleDigitChange(i, e)}
                          onKeyDown={(e) => handleKeyDown(i, e)}
                          autoFocus={i === 0}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <Button 
              type="submit" 
              className="w-full" 
              disabled={otp.length !== digits || isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify'
              )}
            </Button>
          </form>
          {showQr && (
            <div className="mt-6 pt-6 border-t text-center text-xs text-muted-foreground">
              <p>Scan the QR if shown, then enter your 6‑digit code</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
