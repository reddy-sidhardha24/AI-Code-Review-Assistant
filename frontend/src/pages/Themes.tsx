import React, { useState } from "react";
import { useTheme, ThemeType } from "../context/ThemeContext";

const Themes: React.FC = () => {
  const { theme, setTheme, themes, currentThemeMeta } = useTheme();
  const [filter, setFilter] = useState<"all" | "dark" | "light">("all");

  const displayedThemes = themes.filter((t) => {
    if (filter === "all") return true;
    return t.category === filter;
  });

  return (
    <div className="themes-page">
      <div className="themes-container">
        {/* Header */}
        <div className="themes-header">
          <div className="themes-badge">🎨 Workspace Appearance</div>
          <h1 className="themes-title">Theme Customization</h1>
          <p className="themes-subtitle">
            Personalize your AI Code Review workspace with 10 distinct, finely calibrated themes:
            5 futuristic dark themes and 5 ultra-crisp light themes. Your selection is automatically
            preserved across all pages and sessions.
          </p>

          <div className="current-theme-pill">
            <span
              className="pill-dot"
              style={{ backgroundColor: currentThemeMeta.primaryColor }}
            />
            <span>
              Currently Active: <strong>{currentThemeMeta.name}</strong> ({currentThemeMeta.subtitle})
            </span>
          </div>

          {/* Filter Pills */}
          <div className="themes-filter-tabs">
            <button
              type="button"
              className={`filter-tab ${filter === "all" ? "active" : ""}`}
              onClick={() => setFilter("all")}
            >
              All Themes (10)
            </button>
            <button
              type="button"
              className={`filter-tab ${filter === "dark" ? "active" : ""}`}
              onClick={() => setFilter("dark")}
            >
              🌙 Dark Themes (5)
            </button>
            <button
              type="button"
              className={`filter-tab ${filter === "light" ? "active" : ""}`}
              onClick={() => setFilter("light")}
            >
              ☀️ Light Themes (5)
            </button>
          </div>
        </div>

        {/* Theme Cards Grid */}
        <div className="themes-grid">
          {displayedThemes.map((t) => {
            const isActive = theme === t.id;
            return (
              <div
                key={t.id}
                className={`theme-card ${isActive ? "active" : ""} ${t.category}-theme-card`}
                onClick={() => setTheme(t.id)}
              >
                {/* Visual Header Banner */}
                <div
                  className="theme-card-banner"
                  style={{ background: t.previewGradient }}
                >
                  <span className="theme-category-tag">
                    {t.category === "dark" ? "🌙 Dark" : "☀️ Light"}
                  </span>
                  {isActive && <span className="theme-active-tag">✓ Active Theme</span>}
                </div>

                <div className="theme-card-body">
                  <div className="theme-card-header">
                    <div>
                      <div className="theme-name">{t.name}</div>
                      <div className="theme-subtitle">{t.subtitle}</div>
                    </div>
                  </div>

                  <p className="theme-desc">{t.description}</p>

                  {/* Color Palette Swatches */}
                  <div className="theme-swatches">
                    <div className="swatch-item">
                      <span
                        className="swatch-circle"
                        style={{
                          background: t.bgColor,
                          border: "1px solid rgba(128,128,128,0.3)"
                        }}
                      />
                      <span className="swatch-label">Base</span>
                    </div>
                    <div className="swatch-item">
                      <span
                        className="swatch-circle"
                        style={{
                          background: t.cardColor,
                          border: "1px solid rgba(128,128,128,0.3)"
                        }}
                      />
                      <span className="swatch-label">Card</span>
                    </div>
                    <div className="swatch-item">
                      <span
                        className="swatch-circle"
                        style={{ background: t.primaryColor }}
                      />
                      <span className="swatch-label">Primary</span>
                    </div>
                    <div className="swatch-item">
                      <span
                        className="swatch-circle"
                        style={{ background: t.secondaryColor }}
                      />
                      <span className="swatch-label">Accent</span>
                    </div>
                  </div>

                  {/* Live Mock UI preview inside the card */}
                  <div
                    className="theme-mock-box"
                    style={{
                      background: t.bgColor,
                      borderColor: t.primaryColor,
                      color: t.textColor
                    }}
                  >
                    <div
                      className="mock-title-bar"
                      style={{
                        background: t.cardColor,
                        borderBottom: `1px solid ${t.primaryColor}22`
                      }}
                    >
                      <span className="mock-dot red" />
                      <span className="mock-dot yellow" />
                      <span className="mock-dot green" />
                      <span
                        className="mock-tab-text"
                        style={{ color: t.textColor }}
                      >
                        review_analysis.py
                      </span>
                    </div>
                    <div className="mock-content" style={{ color: t.textColor }}>
                      <div className="mock-line" style={{ color: t.secondaryColor }}>
                        # AI Quality Verdict
                      </div>
                      <div className="mock-line">def verify_pipeline():</div>
                      <div
                        className="mock-tag"
                        style={{
                          background: t.primaryColor,
                          color: t.category === "dark" ? "#ffffff" : "#ffffff"
                        }}
                      >
                        ● Production Ready (98%)
                      </div>
                    </div>
                  </div>

                  <button
                    type="button"
                    className={`theme-select-btn ${isActive ? "selected" : ""}`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setTheme(t.id);
                    }}
                  >
                    {isActive ? "✓ Currently Active" : `Activate ${t.name}`}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Live UI Components Demonstration */}
        <div className="themes-demo-section">
          <div className="demo-header">
            <h3>Live Workspace Elements</h3>
            <p>
              Preview how interactive controls adapt instantly to your selected{" "}
              <strong>{currentThemeMeta.name}</strong> theme.
            </p>
          </div>

          <div className="demo-grid">
            <div className="demo-card">
              <h4>Action Buttons</h4>
              <div className="demo-btn-group">
                <button className="btn-primary">Primary Action</button>
                <button className="btn-secondary">Secondary Action</button>
                <button className="btn-outline">Outline Button</button>
              </div>
            </div>

            <div className="demo-card">
              <h4>Review Status Badges</h4>
              <div className="demo-pills-group">
                <span className="demo-pill pill-success">✓ 0 Critical Vulnerabilities</span>
                <span className="demo-pill pill-warning">⚠ 2 Warnings</span>
                <span className="demo-pill pill-danger">✕ 1 Syntax Issue</span>
                <span className="demo-pill pill-info">ℹ Score: 95 / 100</span>
              </div>
            </div>

            <div className="demo-card">
              <h4>Code Token Rendering</h4>
              <div className="demo-code-box">
                <code>
                  <span style={{ color: "var(--primary-light)" }}>async function</span> analyzeCode(ast) &#123;<br />
                  &nbsp;&nbsp;<span style={{ color: "var(--success)" }}>const</span> result = await rag.inspect();<br />
                  &nbsp;&nbsp;<span style={{ color: "var(--primary)" }}>return</span> result.score;<br />
                  &#125;
                </code>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Themes;
