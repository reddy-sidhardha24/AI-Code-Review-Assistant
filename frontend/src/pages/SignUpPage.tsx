import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { SignUp } from "@clerk/clerk-react";
import { useAppAuth } from "../context/AuthContext";

const SignUpPage: React.FC = () => {
  const { isClerkConfigured, isSignedIn, signUpDev } = useAppAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const redirectUrl = searchParams.get("redirect_url") || "/dashboard";

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

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
      await signUpDev(email.trim(), name.trim() || email.split("@")[0]);
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
            <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
          </div>
        ) : (
          <div className="auth-card">
            <div className="auth-header">
              <div className="auth-logo-badge">&lt;/&gt;</div>
              <h2 className="auth-title">Create your Account</h2>
              <p className="auth-subtitle">
                Join ReviewSphere to run automated security audits, code reviews, and AST checks.
              </p>
            </div>

            <form onSubmit={handleDevSubmit} className="auth-form">
              <div className="auth-field">
                <label>Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ada Lovelace"
                  required
                />
              </div>

              <div className="auth-field">
                <label>Work Email</label>
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
                {loading ? "Creating Account..." : "Sign Up"}
              </button>
            </form>

            <div className="auth-footer">
              Already have an account?{" "}
              <Link to={`/sign-in?redirect_url=${encodeURIComponent(redirectUrl)}`}>
                Sign In
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SignUpPage;
