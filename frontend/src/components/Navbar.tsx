import { NavLink } from "react-router-dom";

function Navbar() {
  const linkClass = ({
    isActive,
  }: {
    isActive: boolean;
  }) =>
    isActive
      ? "nav-link active"
      : "nav-link";

  return (
    <nav className="navbar">

      <NavLink
        to="/"
        end
        className="brand"
      >
        <div className="brand-mark">
          ✦
        </div>

        <div className="brand-text">

          <span className="brand-title">
            CodeReview AI
          </span>

          <span className="brand-subtitle">
            RAG-Powered Analysis
          </span>

        </div>
      </NavLink>


      <div className="nav-links">

        <NavLink
          to="/"
          end
          className={linkClass}
        >
          Home
        </NavLink>

        <NavLink
          to="/review"
          className={linkClass}
        >
          Review
        </NavLink>

        <NavLink
          to="/dashboard"
          className={linkClass}
        >
          Dashboard
        </NavLink>

        <NavLink
          to="/history"
          className={linkClass}
        >
          History
        </NavLink>

        <NavLink
          to="/about"
          className={linkClass}
        >
          About
        </NavLink>

        <NavLink
          to="/contact"
          className={linkClass}
        >
          Contact
        </NavLink>

      </div>


      <div className="nav-status">

        <span className="status-dot" />

        AI Online

      </div>

    </nav>
  );
}

export default Navbar;