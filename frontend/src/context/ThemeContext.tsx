import React, { createContext, useContext, useEffect, useState } from "react";
import API from "../api";

export type DarkThemeType =
  | "neural-aurora"
  | "cyber-space"
  | "digital-galaxy"
  | "emerald-intelligence"
  | "crimson-cyber";

export type LightThemeType =
  | "arctic-ai"
  | "sky-intelligence"
  | "lavender-ai"
  | "mint-technology"
  | "holographic-light";

export type ThemeType = DarkThemeType | LightThemeType;

export interface ThemeMeta {
  id: ThemeType;
  name: string;
  category: "dark" | "light";
  subtitle: string;
  description: string;
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  bgColor: string;
  cardColor: string;
  textColor: string;
  textMuted: string;
  accentBadge: string;
  badgeClass: string;
  previewGradient: string;
}

export const THEMES_LIST: ThemeMeta[] = [
  // ========================================================
  // 🌙 5 DARK THEMES
  // ========================================================
  {
    id: "neural-aurora",
    name: "Neural Aurora",
    category: "dark",
    subtitle: "Deep Navy & Cosmic Violet",
    description: "Dark navy base with blue and purple glowing neural connections, floating particles, and soft glowing orbs.",
    primaryColor: "#6366f1",
    secondaryColor: "#a855f7",
    accentColor: "#38bdf8",
    bgColor: "#070b14",
    cardColor: "#0f1422",
    textColor: "#f8fafc",
    textMuted: "#94a3b8",
    accentBadge: "Futuristic AI",
    badgeClass: "badge-dark",
    previewGradient: "linear-gradient(135deg, #070b14 0%, #1e1b4b 50%, #0c1838 100%)"
  },
  {
    id: "cyber-space",
    name: "Cyber Space",
    category: "dark",
    subtitle: "Deep Void & Cyan Circuits",
    description: "Deep black and dark blue canvas with glowing cyan circuits, subtle digital grid, and modern developer aesthetics.",
    primaryColor: "#06b6d4",
    secondaryColor: "#0284c7",
    accentColor: "#22d3ee",
    bgColor: "#030712",
    cardColor: "#091224",
    textColor: "#f0fdf4",
    textMuted: "#67e8f9",
    accentBadge: "Cyber Grid",
    badgeClass: "badge-cyber",
    previewGradient: "linear-gradient(135deg, #030712 0%, #082f49 50%, #064e3b 100%)"
  },
  {
    id: "digital-galaxy",
    name: "Digital Galaxy",
    category: "dark",
    subtitle: "Midnight Void & Cosmic Nebula",
    description: "Dark navy space background infused with purple, blue and pink cosmic lighting, twinkling stars, and floating dust.",
    primaryColor: "#c084fc",
    secondaryColor: "#f472b6",
    accentColor: "#60a5fa",
    bgColor: "#050814",
    cardColor: "#110e2c",
    textColor: "#faf5ff",
    textMuted: "#c4b5fd",
    accentBadge: "Cosmic Glow",
    badgeClass: "badge-galaxy",
    previewGradient: "linear-gradient(135deg, #050814 0%, #3b0764 50%, #172554 100%)"
  },
  {
    id: "emerald-intelligence",
    name: "Emerald Intelligence",
    category: "dark",
    subtitle: "Charcoal Matrix & Teal Neural",
    description: "Dark charcoal background featuring emerald and teal neural effects, glowing connections, and algorithmic precision.",
    primaryColor: "#10b981",
    secondaryColor: "#14b8a6",
    accentColor: "#34d399",
    bgColor: "#04140e",
    cardColor: "#0a261c",
    textColor: "#ecfdf5",
    textMuted: "#6ee7b7",
    accentBadge: "Neural Matrix",
    badgeClass: "badge-emerald",
    previewGradient: "linear-gradient(135deg, #04140e 0%, #064e3b 50%, #0f766e 100%)"
  },
  {
    id: "crimson-cyber",
    name: "Crimson Cyber",
    category: "dark",
    subtitle: "Obsidian & Scarlet Pulse",
    description: "Dark charcoal/black backdrop with crimson and red glowing elements, futuristic circuit patterns, and bold tech attitude.",
    primaryColor: "#f43f5e",
    secondaryColor: "#ef4444",
    accentColor: "#fb7185",
    bgColor: "#090407",
    cardColor: "#1a0b12",
    textColor: "#fff1f2",
    textMuted: "#fda4af",
    accentBadge: "Bold Tech",
    badgeClass: "badge-crimson",
    previewGradient: "linear-gradient(135deg, #090407 0%, #4c0519 50%, #1f040d 100%)"
  },

  // ========================================================
  // ☀️ 5 LIGHT THEMES
  // ========================================================
  {
    id: "arctic-ai",
    name: "Arctic AI",
    category: "light",
    subtitle: "Glacial White & Ice Blue",
    description: "Clean white/light-gray background with soft ice-blue accents, crystalline neural patterns, and crisp dark typography.",
    primaryColor: "#0284c7",
    secondaryColor: "#38bdf8",
    accentColor: "#0369a1",
    bgColor: "#f8fafc",
    cardColor: "#ffffff",
    textColor: "#0f172a",
    textMuted: "#475569",
    accentBadge: "Crisp Focus",
    badgeClass: "badge-arctic",
    previewGradient: "linear-gradient(135deg, #ffffff 0%, #e0f2fe 50%, #f1f5f9 100%)"
  },
  {
    id: "sky-intelligence",
    name: "Sky Intelligence",
    category: "light",
    subtitle: "Airy Light Sky & Azure Orbs",
    description: "White and light sky-blue background with soft glowing azure effects, floating cloud-like light shapes, and modern clarity.",
    primaryColor: "#2563eb",
    secondaryColor: "#60a5fa",
    accentColor: "#0ea5e9",
    bgColor: "#f0f9ff",
    cardColor: "#ffffff",
    textColor: "#0c2340",
    textMuted: "#334155",
    accentBadge: "Daylight AI",
    badgeClass: "badge-sky",
    previewGradient: "linear-gradient(135deg, #f0f9ff 0%, #bae6fd 50%, #ffffff 100%)"
  },
  {
    id: "lavender-ai",
    name: "Lavender AI",
    category: "light",
    subtitle: "Silken Lilac & Violet Mist",
    description: "White/light lavender background with gentle purple and violet accents, elegant neural patterns, and premium SaaS refinement.",
    primaryColor: "#7c3aed",
    secondaryColor: "#a78bfa",
    accentColor: "#9333ea",
    bgColor: "#faf5ff",
    cardColor: "#ffffff",
    textColor: "#1e1133",
    textMuted: "#4c3b63",
    accentBadge: "Creative SaaS",
    badgeClass: "badge-lavender",
    previewGradient: "linear-gradient(135deg, #faf5ff 0%, #e9d5ff 50%, #ffffff 100%)"
  },
  {
    id: "mint-technology",
    name: "Mint Technology",
    category: "light",
    subtitle: "Pristine Mint & Emerald Glow",
    description: "White and light-mint background with refreshing teal and green accents, soft geometric patterns, and clean readability.",
    primaryColor: "#059669",
    secondaryColor: "#10b981",
    accentColor: "#0d9488",
    bgColor: "#f0fdf4",
    cardColor: "#ffffff",
    textColor: "#062817",
    textMuted: "#2d5540",
    accentBadge: "Fresh Clarity",
    badgeClass: "badge-mint",
    previewGradient: "linear-gradient(135deg, #f0fdf4 0%, #bbf7d0 50%, #ffffff 100%)"
  },
  {
    id: "holographic-light",
    name: "Holographic Light",
    category: "light",
    subtitle: "Prism Pastel & Glassmorphism",
    description: "White/light-gray background with soft pastel pink, violet and cyan lighting, subtle iridescent effects, and glassmorphism.",
    primaryColor: "#8b5cf6",
    secondaryColor: "#ec4899",
    accentColor: "#06b6d4",
    bgColor: "#fdfbf7",
    cardColor: "rgba(255, 255, 255, 0.94)",
    textColor: "#18181b",
    textMuted: "#52525b",
    accentBadge: "Next-Gen Glass",
    badgeClass: "badge-holographic",
    previewGradient: "linear-gradient(135deg, #fff7ed 0%, #fce7f3 40%, #e0e7ff 100%)"
  }
];

// Helper to normalize legacy or incoming theme names
export function normalizeThemeId(rawId?: string | null): ThemeType {
  if (!rawId) return "neural-aurora";

  const lower = rawId.toLowerCase().trim();

  // Direct matches
  const found = THEMES_LIST.find((t) => t.id === lower);
  if (found) return found.id;

  // Legacy mappings
  if (lower === "dark") return "neural-aurora";
  if (lower === "light") return "arctic-ai";
  if (lower === "purple") return "lavender-ai";
  if (lower === "emerald") return "emerald-intelligence";

  return "neural-aurora";
}

interface ThemeContextValue {
  theme: ThemeType;
  setTheme: (theme: ThemeType) => void;
  themes: ThemeMeta[];
  darkThemes: ThemeMeta[];
  lightThemes: ThemeMeta[];
  currentThemeMeta: ThemeMeta;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<ThemeType>(() => {
    const saved = localStorage.getItem("app_theme");
    return normalizeThemeId(saved);
  });

  const setTheme = (newTheme: ThemeType) => {
    const validTheme = normalizeThemeId(newTheme);
    setThemeState(validTheme);
    localStorage.setItem("app_theme", validTheme);
    document.documentElement.setAttribute("data-theme", validTheme);

    const isLightCategory = THEMES_LIST.find((t) => t.id === validTheme)?.category === "light";
    if (isLightCategory) {
      document.documentElement.setAttribute("data-theme-category", "light");
    } else {
      document.documentElement.setAttribute("data-theme-category", "dark");
    }

    // Sync with backend API if user is authenticated
    const userId = localStorage.getItem("clerk_user_id") || localStorage.getItem("auth_user_id");
    if (userId) {
      API.put("/api/user/theme", { theme: validTheme }).catch((err) => {
        console.warn("Could not sync theme with server:", err.message);
      });
    }
  };

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    const meta = THEMES_LIST.find((t) => t.id === theme) || THEMES_LIST[0];
    document.documentElement.setAttribute("data-theme-category", meta.category);
  }, [theme]);

  const currentThemeMeta = THEMES_LIST.find((t) => t.id === theme) || THEMES_LIST[0];
  const darkThemes = THEMES_LIST.filter((t) => t.category === "dark");
  const lightThemes = THEMES_LIST.filter((t) => t.category === "light");
  const isDark = currentThemeMeta.category === "dark";

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        themes: THEMES_LIST,
        darkThemes,
        lightThemes,
        currentThemeMeta,
        isDark
      }}
    >
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
