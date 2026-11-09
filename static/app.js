// PayPilot AI ACCESS - Frontend Application
// Note: All dynamic rendering uses textContent exclusively.

document.addEventListener("DOMContentLoaded", () => {
  const statusEl = document.getElementById("app-status");
  if (statusEl) {
    statusEl.textContent = "PayPilot AI ACCESS ready.";
  }
});
