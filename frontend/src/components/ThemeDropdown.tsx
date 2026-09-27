import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { useTheme, ThemeType, ThemeMeta } from "../context/ThemeContext";

const ThemeDropdown: React.FC = () => {
  const { theme, setTheme, darkThemes, lightThemes, currentThemeMeta } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement | null>(null);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = (id: ThemeType) => {
    setTheme(id);
    setIsOpen(false);
  };

  const renderThemeOption = (t: ThemeMeta) => {
    const isActive = theme === t.id;
    return (
      <button
        key={t.id}
        type="button"
        className={`theme-dropdown-item ${isActive ? "active" : ""}`}
        onClick={() => handleSelect(t.id)}
        role="option"
        aria-selected={isActive}
      >
        {/* Visual Swatch Preview */}
        <div
          className="theme-item-preview"
          style={{ background: t.previewGradient }}
        >
          <span
            className="theme-item-dot"
            style={{ backgroundColor: t.primaryColor }}
          />
          <span
            className="theme-item-dot"
            style={{ backgroundColor: t.secondaryColor }}
          />
        </div>

        {/* Theme Name & Tag */}
        <div className="theme-item-info">
          <span className="theme-item-name">{t.name}</span>
          <span className="theme-item-badge">{t.accentBadge}</span>
        </div>

        {/* Active Indicator */}
        {isActive && (
          <span className="theme-item-active-check" title="Currently Active">
            ✓
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="theme-dropdown-wrapper" ref={dropdownRef}>
      {/* Trigger Button in Navbar */}
      <button
        type="button"
        className={`nav-theme-btn ${isOpen ? "open" : ""}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        title={`Current Theme: ${currentThemeMeta.name}. Click to change theme.`}
      >
        <span
          className="nav-theme-dot"
          style={{ backgroundColor: currentThemeMeta.primaryColor }}
        />
        <span className="nav-theme-label">{currentThemeMeta.name}</span>
        <span className="nav-theme-caret">▾</span>
      </button>

      {/* Grouped Dropdown Modal */}
      {isOpen && (
        <div className="theme-dropdown-menu" role="listbox">
          <div className="theme-dropdown-header">
            <div className="theme-dropdown-title">
              <span>🎨 Workspace Themes</span>
              <span className="theme-count-badge">10 Available</span>
            </div>
            <Link
              to="/themes"
              className="theme-view-all-link"
              onClick={() => setIsOpen(false)}
            >
              Full Gallery →
            </Link>
          </div>

          <div className="theme-dropdown-scroll">
            {/* 🌙 Dark Themes Group */}
            <div className="theme-group">
              <div className="theme-group-label">
                <span>🌙 Dark Themes</span>
                <span className="theme-group-count">5</span>
              </div>
              <div className="theme-group-list">
                {darkThemes.map(renderThemeOption)}
              </div>
            </div>

            <div className="theme-group-divider" />

            {/* ☀️ Light Themes Group */}
            <div className="theme-group">
              <div className="theme-group-label">
                <span>☀️ Light Themes</span>
                <span className="theme-group-count">5</span>
              </div>
              <div className="theme-group-list">
                {lightThemes.map(renderThemeOption)}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ThemeDropdown;
