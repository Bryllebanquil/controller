
  import * as React from "react";
  import App from "./App.tsx";
  import "./index.css";
  import { SocketProvider } from "./components/SocketProvider";

  React.createRoot(document.getElementById("root")!).render(
    <SocketProvider>
      <App />
    </SocketProvider>
  );
  