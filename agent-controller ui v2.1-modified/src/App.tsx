import React from "react";
import { ThemeProvider } from "./components/ThemeProvider";
import { Dashboard } from "./components/Dashboard";

function AppContent() {
  return <Dashboard />;
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