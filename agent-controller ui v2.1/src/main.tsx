
  import { createRoot } from "react-dom/client";
   import App from "./App";
  import "./index.css";
import { SocketProvider } from "./components/SocketProvider";
import { initSupabaseAuth } from './services/supabaseClient'

try { initSupabaseAuth() } catch {}

try {
  window.addEventListener('error', (e: any) => {
    try {
      const m = e?.error?.message || e?.message || '';
      const s = e?.error?.stack || '';
      const payload = { message: String(m || ''), stack: String(s || ''), ts: Date.now() };
      localStorage.setItem('nch:last_error', JSON.stringify(payload));
    } catch {}
  });
  window.addEventListener('unhandledrejection', (e: any) => {
    try {
      const r = e?.reason;
      const m = r?.message || String(r || '');
      const s = r?.stack || '';
      const payload = { message: String(m || ''), stack: String(s || ''), ts: Date.now() };
      localStorage.setItem('nch:last_error', JSON.stringify(payload));
    } catch {}
  });
} catch {}

  createRoot(document.getElementById("root")!).render(
    <SocketProvider>
      <App />
    </SocketProvider>
  );
  
