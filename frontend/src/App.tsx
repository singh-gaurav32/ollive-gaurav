import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { NavBar } from "./components/NavBar";
import { LoginPage } from "./pages/LoginPage";
import { ChatPage } from "./pages/ChatPage";
import { DashboardPage } from "./pages/DashboardPage";
import { AboutPage } from "./pages/AboutPage";

function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div className="flex h-screen items-center justify-center text-sm text-gray-500">Loading...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return (
    <div>
      <NavBar />
      {children}
    </div>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/about" element={<AboutPage />} />
      <Route
        path="/chat"
        element={
          <ProtectedLayout>
            <ChatPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/chat/:conversationId"
        element={
          <ProtectedLayout>
            <ChatPage />
          </ProtectedLayout>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedLayout>
            <DashboardPage />
          </ProtectedLayout>
        }
      />
      <Route path="*" element={<Navigate to="/chat" replace />} />
    </Routes>
  );
}
