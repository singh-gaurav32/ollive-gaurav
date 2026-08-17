import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function NavBar() {
  const { user, logout } = useAuth();

  return (
    <nav className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
      <div className="flex items-center gap-4">
        <span className="font-semibold text-gray-900">Ollive</span>
        <Link to="/chat" className="text-sm text-gray-600 hover:text-gray-900">
          Chat
        </Link>
        <Link to="/dashboard" className="text-sm text-gray-600 hover:text-gray-900">
          Dashboard
        </Link>
        <Link to="/about" className="text-sm text-gray-600 hover:text-gray-900">
          About
        </Link>
      </div>
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">{user?.username}</span>
        <button
          onClick={() => void logout()}
          className="rounded bg-gray-100 px-3 py-1 text-sm text-gray-700 hover:bg-gray-200"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
