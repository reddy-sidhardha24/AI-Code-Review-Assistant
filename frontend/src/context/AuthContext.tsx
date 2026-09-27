import React, { createContext, useContext, useEffect, useState } from "react";
import {
  ClerkProvider,
  useUser as useClerkUser,
  useClerk
} from "@clerk/clerk-react";
import API from "../api";

export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
  imageUrl?: string;
  createdAt?: string;
}

interface AuthContextValue {
  isLoaded: boolean;
  isSignedIn: boolean;
  user: AuthUser | null;
  signOut: () => Promise<void>;
  signInDev: (email: string, name?: string) => Promise<void>;
  signUpDev: (email: string, name: string) => Promise<void>;
  isClerkConfigured: boolean;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// Raw publishable key from environment
const rawClerkKey = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY || "";
const isClerkKeyValid =
  Boolean(rawClerkKey) &&
  rawClerkKey.trim() !== "" &&
  rawClerkKey !== "pk_test_placeholder_key" &&
  (rawClerkKey.startsWith("pk_test_") || rawClerkKey.startsWith("pk_live_"));

// ============================================================
// INNER CLERK SYNCHRONIZER (Used when Clerk key is valid)
// ============================================================

const ClerkSessionBridge: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isLoaded, isSignedIn, user: clerkUser } = useClerkUser();
  const { signOut: clerkSignOut } = useClerk();

  const [authUser, setAuthUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    if (isLoaded && isSignedIn && clerkUser) {
      const email = clerkUser.primaryEmailAddress?.emailAddress || "";
      const fullName = clerkUser.fullName || clerkUser.firstName || email.split("@")[0] || "User";
      const imageUrl = clerkUser.imageUrl || "";
      const id = clerkUser.id;

      const userObj: AuthUser = {
        id,
        email,
        fullName,
        imageUrl
      };

      setAuthUser(userObj);

      // Store in localStorage for API headers
      localStorage.setItem("clerk_user_id", id);
      localStorage.setItem("clerk_user_email", email);
      localStorage.setItem("clerk_user_name", fullName);

      // Sync to SQLite database
      API.post("/api/users/sync", {
        id,
        email,
        full_name: fullName,
        image_url: imageUrl
      }).catch((err) => {
        console.warn("[Auth] Clerk user sync to SQLite warning:", err.message);
      });
    } else if (isLoaded && !isSignedIn) {
      setAuthUser(null);
      localStorage.removeItem("clerk_user_id");
      localStorage.removeItem("clerk_user_email");
      localStorage.removeItem("clerk_user_name");
      localStorage.removeItem("clerk_jwt_token");
    }
  }, [isLoaded, isSignedIn, clerkUser]);

  const signOut = async () => {
    localStorage.removeItem("clerk_user_id");
    localStorage.removeItem("clerk_user_email");
    localStorage.removeItem("clerk_user_name");
    await clerkSignOut();
  };

  const devNoop = async () => {};

  return (
    <AuthContext.Provider
      value={{
        isLoaded,
        isSignedIn: Boolean(isSignedIn),
        user: authUser,
        signOut,
        signInDev: devNoop,
        signUpDev: devNoop,
        isClerkConfigured: true
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// ============================================================
// FALLBACK LOCAL AUTH PROVIDER (When Clerk key is not provided yet)
// ============================================================

const FallbackAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const savedId = localStorage.getItem("auth_user_id");
    const savedEmail = localStorage.getItem("auth_user_email");
    const savedName = localStorage.getItem("auth_user_name");

    if (savedId && savedEmail) {
      return {
        id: savedId,
        email: savedEmail,
        fullName: savedName || savedEmail.split("@")[0],
        imageUrl: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(savedName || savedEmail)}`
      };
    }
    return null;
  });

  const [isLoaded, setIsLoaded] = useState(true);

  const signInDev = async (email: string, name?: string) => {
    const id = `user_${Date.now()}`;
    const fullName = name || email.split("@")[0];
    const userObj: AuthUser = {
      id,
      email,
      fullName,
      imageUrl: `https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(fullName)}`
    };

    localStorage.setItem("auth_user_id", id);
    localStorage.setItem("auth_user_email", email);
    localStorage.setItem("auth_user_name", fullName);
    setUser(userObj);

    // Sync to SQLite
    try {
      await API.post("/api/users/sync", {
        id,
        email,
        full_name: fullName,
        image_url: userObj.imageUrl
      });
    } catch (e) {
      console.warn("Dev auth sync warning:", e);
    }
  };

  const signUpDev = async (email: string, name: string) => {
    return signInDev(email, name);
  };

  const signOut = async () => {
    localStorage.removeItem("auth_user_id");
    localStorage.removeItem("auth_user_email");
    localStorage.removeItem("auth_user_name");
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isLoaded,
        isSignedIn: Boolean(user),
        user,
        signOut,
        signInDev,
        signUpDev,
        isClerkConfigured: false
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

// ============================================================
// MAIN APP AUTH PROVIDER
// ============================================================

export const AppAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  if (isClerkKeyValid) {
    return (
      <ClerkProvider publishableKey={rawClerkKey}>
        <ClerkSessionBridge>{children}</ClerkSessionBridge>
      </ClerkProvider>
    );
  }

  return <FallbackAuthProvider>{children}</FallbackAuthProvider>;
};

export const useAppAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAppAuth must be used within an AppAuthProvider");
  }
  return context;
};
