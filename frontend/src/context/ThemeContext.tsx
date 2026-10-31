import React, { createContext, useContext, useEffect, useState } from "react";
import API from "../api";

export type ThemeType = "dark" | "light" | "purple" | "emerald";

export interface ThemeMeta {
  id: ThemeType;
  name: string;
  subtitle: string;
  description: string;
  primaryColor: string;
  secondaryColor: string;
  bgColor: string;
  cardColor: string;
  textColor: string;
  accentBadge: string;
  badgeClass: string;
}

export const THEMES_LIST: ThemeMeta[] = [
  {
    id: "dark",
    name: "Dark Theme",
    subtitle: "Default Midnight SaaS",
    description: "Deep obsidian & slate navy designed for high-contrast, low eye fatigue long coding sessions.",
    primaryColor: "#6366f1",
    secondaryColor: "#818cf8",
    bgColor: "#070b14",
    cardColor: "#0f141f",
    textColor: "#f8fafc",
    accentBadge: "Existing Default",
    badgeClass: "badge-dark"
  },
  {
    id: "light",
    name: "Light Theme",
    subtitle: "Crisp Slate & Clean Indigo",
    description: "Modern high-clarity daylight theme with clean borders, ultra-readable typography, and crisp contrast.",
    primaryColor: "#4f46e5",
    secondaryColor: "#6366f1",
    bgColor: "#f8fafc",
    cardColor: "#ffffff",
    textColor: "#0f172a",
    accentBadge: "Daylight Focus",
    badgeClass: "badge-light"
  },
  {
    id: "purple",
    name: "Purple / Lavender",
    subtitle: "Royal Amethyst & Violet Mist",
    description: "Vibrant cosmic violet and soothing lavender accents tailored for creative engineers and deep focus.",
    primaryColor: "#9333ea",
    secondaryColor: "#c084fc",
    bgColor: "#0d0a1a",
    cardColor: "#1b1437",
    textColor: "#faf5ff",
    accentBadge: "Creative Flow",
    badgeClass: "badge-purple"
  },
  {
    id: "emerald",
    name: "Emerald Green",
    subtitle: "Cyber Forest & Mint Glow",
    description: "Futuristic matrix emerald and refreshing mint tones engineered for sustained algorithmic analysis.",
    primaryColor: "#10b981",
    secondaryColor: "#34d399",
    bgColor: "#04140e",
    cardColor: "#0d3527",
    textColor: "#ecfdf5",
    accentBadge: "Terminal Zen",
    badgeClass: "badge-emerald"
  }
];

interface ThemeContextValue {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  themes: ThemeMeta[];
  currentThemeMeta: ThemeMeta;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeType>(() => {
    const saved = localStorage.getItem("app_theme") as ThemeType;
    if (saved && ["dark", "light", "purple", "emerald"].includes(saved)) {
      return saved;
    }
    return "dark";
  });

  const setTheme = (newTheme: ThemeType) => {
    setThemeState(newTheme);
    localStorage.setItem("app_theme", newTheme);
    document.documentElement.setAttribute("data-theme", newTheme);

    // Sync with backend API if user is authenticated
    const userId = localStorage.getItem("clerk_user_id") || localStorage.getItem("auth_user_id");
    if (userId) {
      API.put("/api/user/theme", { theme: newTheme }).catch((err) => {
        // Non-blocking sync error
        console.warn("Could not sync theme with server:", err.message);
      });
    }
  };

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  const currentThemeMeta = THEMES_LIST.find((t) => t.id === theme) || THEMES_LIST[0];

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES_LIST, currentThemeMeta }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
