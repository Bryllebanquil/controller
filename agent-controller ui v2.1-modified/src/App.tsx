import React from "react";
import { ThemeProvider } from "./components/ThemeProvider";
import { Dashboard } from "./components/Dashboard";
import { Toaster } from "./components/ui/sonner";

function AppContent() {
  return (
    <>
      <Dashboard />
      <Toaster />
    </>
  );
}

export default function App() {
  return (
    <ThemeProvider
      defaultTheme="system"
      storageKey="neural-control-hub-theme"
      children={<AppContent />}
    />
  );
}