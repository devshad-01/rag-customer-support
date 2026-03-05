import api from "./api";

// ── Download helper ──────────────────────────────────────────
export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

// ── CSV Exports ──────────────────────────────────────────────
export async function getQueryLogsCSV(params = {}) {
  const { data } = await api.get("/reports/query-logs", {
    params,
    responseType: "blob",
  });
  return data;
}

export async function getEscalationCSV(params = {}) {
  const { data } = await api.get("/reports/escalations", {
    params: { ...params, format: "csv" },
    responseType: "blob",
  });
  return data;
}

export async function getAgentPerformanceCSV() {
  const { data } = await api.get("/reports/agent-performance", {
    responseType: "blob",
  });
  return data;
}

export async function getAnalyticsSummaryCSV(params = {}) {
  const { data } = await api.get("/reports/analytics-summary", {
    params,
    responseType: "blob",
  });
  return data;
}

// ── PDF Exports ──────────────────────────────────────────────
export async function getAnalyticsPDF(params = {}) {
  const { data } = await api.get("/reports/analytics", {
    params,
    responseType: "blob",
  });
  return data;
}

export async function getEscalationPDF(params = {}) {
  const { data } = await api.get("/reports/escalations", {
    params: { ...params, format: "pdf" },
    responseType: "blob",
  });
  return data;
}
