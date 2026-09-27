import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import { ThemeProvider } from "./context/ThemeContext";
import { AppAuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Navbar from "./components/Navbar";
import ThemeBackground from "./components/ThemeBackground";

import Home from "./pages/Home";
import Review from "./components/Review";
import FinalOutput from "./pages/FinalOutput";
import Dashboard from "./components/Dashboard";

import History from "./pages/History";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Themes from "./pages/Themes";
import SignInPage from "./pages/SignInPage";
import SignUpPage from "./pages/SignUpPage";

function App() {
  return (
    <ThemeProvider>
      <ThemeBackground />
      <AppAuthProvider>
        <BrowserRouter>
          <Navbar />

          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/themes" element={<Themes />} />
            <Route path="/sign-in/*" element={<SignInPage />} />
            <Route path="/sign-up/*" element={<SignUpPage />} />

            {/* Protected Routes (Clerk Auth Required) */}
            <Route
              path="/review"
              element={
                <ProtectedRoute>
                  <Review />
                </ProtectedRoute>
              }
            />

            <Route
              path="/final-output"
              element={
                <ProtectedRoute>
                  <FinalOutput />
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
      </AppAuthProvider>
    </ThemeProvider>
  );
}

export default App;