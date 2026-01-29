
  import { createRoot } from "react-dom/client";
   import App from "./App";
  import "./index.css";
import { SocketProvider } from "./components/SocketProvider";
import { initSupabaseAuth } from './services/supabaseClient'

try { initSupabaseAuth() } catch {}

  createRoot(document.getElementById("root")!).render(
    <SocketProvider>
      <App />
    </SocketProvider>
  );
  
