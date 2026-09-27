import axios from "axios";

const API = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || "",
});

// Automatically inject user credentials from localStorage / Clerk session to backend headers
API.interceptors.request.use((config) => {
  const userId = localStorage.getItem("clerk_user_id") || localStorage.getItem("auth_user_id") || "";
  const userEmail = localStorage.getItem("clerk_user_email") || localStorage.getItem("auth_user_email") || "";
  const userName = localStorage.getItem("clerk_user_name") || localStorage.getItem("auth_user_name") || "";
  const token = localStorage.getItem("clerk_jwt_token") || "";

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

  return config;
});

export default API;