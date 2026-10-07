import axios from "axios";
const baseURL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001/api";
export const api = axios.create({ baseURL, timeout: 20000 });
let refreshRequest = null;
export function clearSession() {
  sessionStorage.removeItem("tokens");
  window.dispatchEvent(new Event("session-ended"));
}
export function saveTokens(tokens) {
  sessionStorage.setItem("tokens", JSON.stringify(tokens));
}
function tokens() {
  try {
    return JSON.parse(sessionStorage.getItem("tokens") || "{}");
  } catch {
    return {};
  }
}
api.interceptors.request.use((config) => {
  if (tokens().access)
    config.headers.Authorization = `Bearer ${tokens().access}`;
  return config;
});
api.interceptors.response.use(
  (r) => r,
  async (error) => {
    const original = error.config;
    if (
      error.response?.status !== 401 ||
      original?._retry ||
      original?.url?.includes("/auth/login") ||
      original?.url?.includes("/auth/token/refresh")
    )
      return Promise.reject(error);
    original._retry = true;
    try {
      if (!tokens().refresh) throw error;
      if (!refreshRequest)
        refreshRequest = axios
          .post(`${baseURL}/auth/token/refresh/`, { refresh: tokens().refresh })
          .then((r) => {
            saveTokens(r.data);
            return r.data.access;
          })
          .finally(() => {
            refreshRequest = null;
          });
      original.headers.Authorization = `Bearer ${await refreshRequest}`;
      return api(original);
    } catch (e) {
      clearSession();
      return Promise.reject(e);
    }
  },
);
export async function errorText(error) {
  let data = error.response?.data;
  if (data instanceof Blob) {
    try {
      data = JSON.parse(await data.text());
    } catch {
      data = null;
    }
  }
  if (!data)
    return "Unable to connect. Please check your connection and try again.";
  const flatten = (value) =>
    typeof value === "string"
      ? value
      : Array.isArray(value)
        ? value.map(flatten).join(" ")
        : Object.entries(value)
            .map(
              ([k, v]) =>
                `${k === "detail" ? "" : k.replaceAll("_", " ") + ": "}${flatten(v)}`,
            )
            .join(" ");
  return flatten(data.errors || data.detail || data.message || data);
}
export async function pdfBlob(path) {
  return (await api.get(path, { responseType: "blob" })).data;
}
export async function downloadCertificate(cert) {
  const blob = await pdfBlob(`/certificates/${cert.id}/download/`);
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = `${cert.certificate_id}.pdf`;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 2000);
}
export function resolveMediaUrl(path) {
  if (!path) return "";
  if (
    path.startsWith("data:") ||
    path.startsWith("blob:") ||
    path.startsWith("http://") ||
    path.startsWith("https://")
  ) {
    return path;
  }
  const backendOrigin = (baseURL || "http://127.0.0.1:8001/api").replace(
    /\/api\/?$/,
    "",
  );
  return `${backendOrigin}${path.startsWith("/") ? "" : "/"}${path}`;
}


