import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAppAuth } from "../context/AuthContext";
import { useTheme } from "../context/ThemeContext";
import { UserButton } from "@clerk/clerk-react";
import ThemeDropdown from "./ThemeDropdown";

function Navbar() {
  const { isSignedIn, user, signOut, isClerkConfigured } = useAppAuth();
  const { currentThemeMeta } = useTheme();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    isActive ? "nav-link active" : "nav-link";

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
            <span className="brand-title">ReviewSphere</span>
            <span className="brand-subtitle">RAG-Powered Project Review</span>
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

          <NavLink to="/review" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Review
          </NavLink>

          <NavLink to="/final-output" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Final Output
          </NavLink>

          <NavLink to="/dashboard" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Dashboard
          </NavLink>

          <NavLink to="/history" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            History
          </NavLink>

          <NavLink to="/about" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            About
          </NavLink>

          <NavLink to="/contact" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Contact
          </NavLink>

          {/* Themes gallery */}
          <NavLink to="/themes" className={linkClass} onClick={() => setMobileMenuOpen(false)}>
            Themes
          </NavLink>
        </div>

        {/* Right Section: Theme Selector Dropdown & User Profile */}
        <div className="nav-actions">
          {/* Grouped 10-Theme Selector Dropdown */}
          <ThemeDropdown />

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
                    <span className="user-name">{user.fullName}</span>
                    <span className="user-email">{user.email}</span>
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

          <div className="nav-status">
            <span className="status-dot" />
            <span>AI Online</span>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;