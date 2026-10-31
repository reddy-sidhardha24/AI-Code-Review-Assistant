import {
  BrowserRouter,
  Routes,
  Route
} from "react-router-dom";
import React from "react";

import { ThemeProvider } from "./context/ThemeContext";
import { AppAuthProvider } from "./context/AuthContext";
import { ReviewProvider } from "./context/ReviewContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Navbar from "./components/Navbar";

import Home from "./pages/Home";
import Review from "./components/Review";
import Dashboard from "./components/Dashboard";

import History from "./pages/History";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Configuration from "./pages/Configuration";
import HowToUse from "./pages/HowToUse";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";

function App() {
  return (
    <ThemeProvider>
      <AppAuthProvider>
        <ReviewProvider>
          <BrowserRouter>
            <Navbar />

          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/how-to-use" element={<HowToUse />} />
            <Route
              path="/configuration"
              element={
                <ProtectedRoute>
                  <Configuration />
                </ProtectedRoute>
              }
            />
            <Route path="/sign-in/*" element={<SignInPage />} />
            <Route path="/sign-up/*" element={<SignUpPage />} />

            {/* Protected Routes (Auth Required) */}
            <Route
              path="/review"
              element={
                <ProtectedRoute>
                  <Review />
                </ProtectedRoute>
              }
            />

            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard />
                </ProtectedRoute>
              }
            />

            <Route
              path="/history"
              element={
                <ProtectedRoute>
                  <History />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
        </ReviewProvider>
      </AppAuthProvider>
    </ThemeProvider>
  );
}

export default App;
