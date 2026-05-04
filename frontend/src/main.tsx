import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);

window.addEventListener("unhandledrejection", (event) => {
  console.error("未捕获的 Promise 错误:", event.reason);
});
