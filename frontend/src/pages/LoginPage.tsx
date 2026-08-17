import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { listDemoUsers } from "../api/auth";
import { useAuth } from "../context/AuthContext";
import type { User } from "../types";

export function LoginPage() {
  const [demoUsers, setDemoUsers] = useState<User[]>([]);
  const [isLoggingIn, setIsLoggingIn] = useState(false);
  const { login, user } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    listDemoUsers().then(setDemoUsers);
  }, []);

  useEffect(() => {
    if (user) navigate("/chat");
  }, [user, navigate]);

  async function handleLogin(username: string) {
    setIsLoggingIn(true);
    try {
      await login(username);
      navigate("/chat");
    } finally {
      setIsLoggingIn(false);
    }
  }

  return (
    <div className="flex h-screen items-center justify-center bg-gray-50">
      <div className="w-80 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h1 className="mb-1 text-lg font-semibold text-gray-900">Ollive</h1>
        <p className="mb-4 text-sm text-gray-500">Pick a demo user to continue</p>
        <div className="space-y-2">
          {demoUsers.map((u) => (
            <button
              key={u.id}
              data-testid={`login-${u.username}`}
              disabled={isLoggingIn}
              onClick={() => void handleLogin(u.username)}
              className="w-full rounded border border-gray-300 px-3 py-2 text-left text-sm hover:bg-gray-50 disabled:opacity-50"
            >
              {u.username}
            </button>
          ))}
        </div>
        <Link
          to="/about"
          className="mt-4 block text-center text-sm text-gray-500 hover:text-gray-700 hover:underline"
        >
          What is this? (architecture &amp; design decisions)
        </Link>
      </div>
    </div>
  );
}
