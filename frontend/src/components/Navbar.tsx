import { Newspaper, Search, Bookmark, LayoutDashboard, LogOut, LogIn, UserCircle, Mail } from "lucide-react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import DarkModeToggle from "./DarkModeToggle";

const navLinks = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/feed", label: "For You", icon: Newspaper },
  { to: "/search", label: "Search", icon: Search },
  { to: "/bookmarks", label: "Saved", icon: Bookmark },
  { to: "/newsletter", label: "Newsletter", icon: Mail },
];

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Newspaper size={20} />
          </div>
          <div className="leading-tight">
            <div className="text-lg font-bold">NewsPulse</div>
            <div className="text-[10px] uppercase tracking-wider text-slate-500">
              Personalized News
            </div>
          </div>
        </Link>

        <nav className="hidden items-center gap-1 md:flex">
          {navLinks.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`
              }
            >
              <link.icon size={16} />
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <DarkModeToggle />
          {user ? (
            <>
              <Link to="/profile" className="btn-ghost" title="Profile">
                <UserCircle size={20} />
                <span className="hidden text-sm font-medium sm:inline">{user.username}</span>
              </Link>
              <button onClick={handleLogout} className="btn-ghost" title="Logout">
                <LogOut size={18} />
              </button>
            </>
          ) : (
            <Link to="/login" className="btn-primary">
              <LogIn size={16} />
              <span className="hidden sm:inline">Sign in</span>
            </Link>
          )}
        </div>
      </div>

      {/* Mobile nav */}
      <nav className="flex items-center gap-1 overflow-x-auto border-t border-slate-200 px-2 py-1.5 md:hidden dark:border-slate-800">
        {navLinks.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-1.5 whitespace-nowrap rounded-md px-2.5 py-1.5 text-xs font-medium ${
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                  : "text-slate-600 dark:text-slate-300"
              }`
            }
          >
            <link.icon size={14} />
            {link.label}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
