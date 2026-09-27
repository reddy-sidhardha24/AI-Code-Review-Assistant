import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { SignIn } from "@clerk/clerk-react";
import { useAppAuth } from "../context/AuthContext";

const SignInPage: React.FC = () => {
  const { isClerkConfigured, isSignedIn, signInDev } = useAppAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectUrl = searchParams.get("redirect_url") || "/dashboard";

  const [email, setEmail] = useState("developer@reviewsphere.ai");
  const [password, setPassword] = useState("password123");
  const [loading, setLoading] = useState(false);

  // If already signed in, navigate immediately
  React.useEffect(() => {
    if (isSignedIn) {
      navigate(redirectUrl, { replace: true });
    }
  }, [isSignedIn, navigate, redirectUrl]);

  const handleDevSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    try {
      await signInDev(email.trim());
      navigate(redirectUrl, { replace: true });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card-container">
        {isClerkConfigured ? (
          <div className="clerk-widget-wrapper">
            <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
          </div>
        ) : (
          <div className="auth-card">
            <div className="auth-header">
              <div className="auth-logo-badge">&lt;/&gt;</div>
              <h2 className="auth-title">Sign In to ReviewSphere</h2>
              <p className="auth-subtitle">
                Access your protected AI code reviews, project dashboard, and vector database.
              </p>
            </div>

            <div className="auth-notice-box">
              <span className="notice-icon">ℹ️</span>
              <div className="notice-text">
                <strong>Clerk Auth Ready:</strong> Add your publishable key in <code>frontend/.env</code> (<code>REACT_APP_CLERK_PUBLISHABLE_KEY</code>) for live Clerk sign-in, or sign in below with the local developer session.
              </div>
            </div>

            <form onSubmit={handleDevSubmit} className="auth-form">
              <div className="auth-field">
                <label>Email Address</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                />
              </div>

              <div className="auth-field">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <button
                type="submit"
                className="btn-auth-primary"
                disabled={loading}
              >
                {loading ? "Signing in..." : "Sign In with Credentials"}
              </button>

              <button
                type="button"
                className="btn-auth-demo"
                onClick={() => {
                  signInDev("developer@reviewsphere.ai", "Demo Engineer");
                  navigate(redirectUrl, { replace: true });
                }}
              >
                ⚡ Instant One-Click Developer Sign-In
              </button>
            </form>

            <div className="auth-footer">
              Don't have an account?{" "}
              <Link to={`/sign-up?redirect_url=${encodeURIComponent(redirectUrl)}`}>
                Sign Up
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SignInPage;
