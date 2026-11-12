import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import RealApp from "./live/RealApp";
import "./styles.css";
import "./theme.css";
import "./visual-system.css";
import "./terminal.css";
const Workspace =
  new URLSearchParams(location.search).get("mode") === "demo" ? App : RealApp;
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <Workspace />
  </React.StrictMode>,
);
