import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAppAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { useReview } from "../context/ReviewContext";
import { UserButton } from "@clerk/clerk-react";

function Navbar() {
  const { isSignedIn, user, signOut, isClerkConfigured } = useAppAuth();
  const { loading: reviewLoading } = useReview();
  const { theme, setTheme, themes, currentThemeMeta } = useTheme();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? "nav-link active" : "nav-link";

  const toggleNextTheme = () => {
    const ids = themes.map((t) => t.id);
    const nextIdx = (ids.indexOf(theme) + 1) % ids.length;
    setTheme(ids[nextIdx]);
  };

  const handleSignOut = async () => {
    await signOut();
    navigate("/");
  };

  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Brand */}
        <NavLink to="/" end className="brand">
          <div className="brand-mark">
            <span>&lt;/&gt;</span>
          </div>
          <div className="brand-text">
            <span className="brand-title">CodeReview AI</span>
            <span className="brand-subtitle">Grounded Code Intelligence</span>
          </div>
        </NavLink>

        {/* Mobile Hamburger Button */}
        <button
          className="mobile-menu-btn"
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          aria-label="Toggle navigation menu"
        >
          {mobileMenuOpen ? "✕" : "☰"}
        </button>

        {/* Navigation Links */}
        <div className={`nav-links ${mobileMenuOpen ? "mobile-open" : ""}`}>
          <NavLink to="/" end className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Home
          </NavLink>

          {/* Protected Workspace Links - only shown when signed in */}
          {isSignedIn && (
            <>
              <NavLink to="/review" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
                Review {reviewLoading && (
                  <span
                    className="nav-analyzing-indicator"
                    title="Analysis in progress"
                    aria-label="Analysis in progress"
                  />
                )}
              </NavLink>

              <NavLink to="/dashboard" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
                Dashboard
              </NavLink>

              <NavLink to="/history" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
                History
              </NavLink>
            </>
          )}

          <NavLink to="/how-to-use" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            How to Use
          </NavLink>

          <NavLink to="/about" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            About
          </NavLink>

          <NavLink to="/contact" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Contact
          </NavLink>
        </div>

        {/* Right Section: Configuration, Theme & User */}
        <div className="nav-actions">
          {/* Quick Theme Toggle Pill */}
          <button
            type="button"
            className="nav-theme-toggle"
            onClick={toggleNextTheme}
            title={`Active: ${currentThemeMeta.name}. Click to switch theme.`}
          >
            <span
              className="theme-dot"
              style={{ backgroundColor: currentThemeMeta.primaryColor }}
            />
            <span className="theme-toggle-label">{currentThemeMeta.name.split(" ")[0]}</span>
          </button>

          {/* Configuration Settings Button */}
          <NavLink
            to="/configuration"
            className="nav-config-btn"
            title="Workspace Configuration & AI Models"
          >
            ⚙️
          </NavLink>

          {/* User Profile Section */}
          {isSignedIn && user ? (
            <div className="user-profile-widget">
              {isClerkConfigured ? (
                <div className="clerk-user-btn-wrapper">
                  <UserButton afterSignOutUrl="/" showName />
                </div>
              ) : (
                <div className="custom-user-badge">
                  {user.imageUrl ? (
                    <img
                      src={user.imageUrl}
                      alt={user.fullName || "User"}
                      className="user-avatar-img"
                    />
                  ) : (
                    <div className="user-avatar-placeholder">
                      {(user.fullName || user.email || "U")[0].toUpperCase()}
                    </div>
                  )}
                  <div className="user-info-text">
                    <span className="user-name">{user.fullName || "User"}</span>
                  </div>
                  <button
                    type="button"
                    className="btn-signout"
                    onClick={handleSignOut}
                    title="Sign Out"
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="nav-auth-buttons">
              <NavLink to="/sign-in" className="btn-nav-signin">
                Sign In
              </NavLink>
              <NavLink to="/sign-up" className="btn-nav-signup">
                Sign Up
              </NavLink>
            </div>
          )}

          {/* Workspace status badge shown when authenticated */}
          {isSignedIn && (
            <div className="nav-status">
              <span className="status-dot" />
              <span>AI Ready</span>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
