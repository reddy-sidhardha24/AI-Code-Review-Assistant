import axios from "axios";

let clerkAccessToken = "";

export const setClerkAccessToken = (token: string) => {
  clerkAccessToken = token;
};

const API = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "",
  withCredentials: true,
});

// Automatically inject user credentials from localStorage / Clerk session to backend headers
API.interceptors.request.use((config) => {
  const userId = localStorage.getItem("clerk_user_id") || localStorage.getItem("auth_user_id") || "";
  const userEmail = localStorage.getItem("clerk_user_email") || localStorage.getItem("auth_user_email") || "";
  const userName = localStorage.getItem("clerk_user_name") || localStorage.getItem("auth_user_name") || "";
  const token = clerkAccessToken;

  if (userId) {
    config.headers["X-User-Id"] = userId;
  }
  if (userEmail) {
    config.headers["X-User-Email"] = userEmail;
  }
  if (userName) {
    config.headers["X-User-Name"] = userName;
  }
  if (token) {
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  const ghUsername = localStorage.getItem("clerk_github_username") || "";
  if (ghUsername) {
    config.headers["X-User-Github-Username"] = ghUsername;
  }

  return config;
});

// Helper API methods
export const fetchLLMConfigs = () => API.get("/api/config/llm");
export const fetchMultiAgentModels = () => API.get("/api/config/multi-agent-models");
export const saveMultiAgentModels = (config_ids: string[]) => API.put("/api/config/multi-agent-models", { config_ids });
export const fetchSingleAgentModel = () => API.get("/api/config/single-agent-model");
export const saveSingleAgentModel = (config_id: string) => API.put("/api/config/single-agent-model", { config_id });
export const saveLLMConfig = (data: any) => API.post("/api/config/llm", data);
export const activateLLMConfig = (id: string) => API.post(`/api/config/llm/${id}/activate`);
export const deleteLLMConfig = (id: string) => API.delete(`/api/config/llm/${id}`);
export const testLLMConnection = (data: any) => API.post("/api/config/llm/test", data);
export const fetchPreferences = () => API.get("/api/config/preferences");
export const updatePreferences = (data: any) => API.put("/api/config/preferences", data);
export const fetchOllamaModels = (baseUrl?: string) => API.get(`/api/ollama/models?base_url=${encodeURIComponent(baseUrl || "http://localhost:11434")}`);
export const cancelReviewRequest = (request_id: string) => API.post("/review/cancel", { request_id });

export const fetchGitHubStatus = () => API.get("/api/github/status");
export const fetchGitHubAuthUrl = () => API.get("/api/github/auth-url");
export const connectGitHub = (data: { username: string; token: string; installation_id?: string }) => API.post("/api/github/connect", data);
export const connectGitHubApp = (data?: string | { installation_id?: string; github_username?: string }) => {
  const payload = typeof data === "string" ? { installation_id: data } : (data || {});
  return API.post("/api/github/connect-app", payload);
};
export const disconnectGitHub = () => API.post("/api/github/disconnect");
export const fetchGitHubRepos = () => API.get("/api/github/repos");
export const fetchGitHubBranches = (owner: string, repo: string) => API.get(`/api/github/repos/${owner}/${repo}/branches`);
export const pushGitHubFix = (data: any) => API.post("/api/github/push-fix", data);
export const refineReviewFix = (data: { file_name: string; before_code: string; current_fix: string; instruction: string }) => API.post("/api/review/refine-fix", data);

export const sendContactMessage = (data: { name: string; email: string; subject: string; message: string }) => API.post("/api/contact", data);

export default API;
