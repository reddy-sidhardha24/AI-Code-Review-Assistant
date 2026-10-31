import React, { useState, useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAppAuth } from "../context/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactElement;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { isLoaded, isSignedIn } = useAppAuth();
  const location = useLocation();
  const [delayedNotice, setDelayedNotice] = useState(false);

  useEffect(() => {
    if (!isLoaded) {
      const timer = setTimeout(() => {
        setDelayedNotice(true);
      }, 2500);
      return () => clearTimeout(timer);
    }
  }, [isLoaded]);

  if (!isLoaded) {
    return (
      <div className="auth-loading-screen">
        <div className="auth-loading-card">
          <div className="auth-loading-spinner"></div>
          <h3 className="auth-loading-title">Verifying Secure Session</h3>
          <p className="auth-loading-subtitle">
            Authenticating your workspace credentials with ReviewSphere...
          </p>
          {delayedNotice && (
            <div className="auth-loading-fallback">
              <p className="auth-fallback-text">
                Session verification is taking longer than expected. Keep this page open while your sign-in provider responds.
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (!isSignedIn) {
    return (
      <Navigate
        to={`/sign-in?redirect_url=${encodeURIComponent(location.pathname)}`}
        replace
      />
    );
  }

  return children;
};

export default ProtectedRoute;
