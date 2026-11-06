import React from "react";
import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function MainLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <nav className="navbar">
        <div className="nav-left">
          <Link to="/recipes" className="brand">
            Recipe Finder
          </Link>
          <Link to="/recipes">My Recipes</Link>
          <Link to="/recipes/new">Add Recipe</Link>
          <Link to="/search">Search</Link>
        </div>
        <div className="nav-right">
          {user && <span className="user-email">{user.email}</span>}
          <button onClick={handleLogout}>Log out</button>
        </div>
      </nav>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
