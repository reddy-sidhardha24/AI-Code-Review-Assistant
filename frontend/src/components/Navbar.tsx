import { NavLink } from "react-router-dom";

function Navbar() {
  return (
    <nav className="navbar">

      <h2 className="logo">AI Code Review Assistant</h2>

      <div className="nav-links">

        <NavLink 
          to="/" 
          className={({isActive}) => isActive ? "active" : ""}
        >
          Home
        </NavLink>

        <NavLink 
          to="/review" 
          className={({isActive}) => isActive ? "active" : ""}
        >
          Review
        </NavLink>

        <NavLink 
          to="/dashboard" 
          className={({isActive}) => isActive ? "active" : ""}
        >
          Dashboard
        </NavLink>

        <NavLink 
          to="/history" 
          className={({isActive}) => isActive ? "active" : ""}
        >
          History
        </NavLink>

        <NavLink 
          to="/about" 
          className={({isActive}) => isActive ? "active" : ""}
        >
          About
        </NavLink>

        <NavLink 
          to="/contact" 
          className={({isActive}) => isActive ? "active" : ""}
        >
          Contact
        </NavLink>

      </div>

    </nav>
  );
}

export default Navbar;