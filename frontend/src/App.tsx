import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "@/context/AuthContext";
import { useAuth } from "@/context/auth-context";
import { AppShell } from "@/components/AppShell";
import { Spinner } from "@/components/ui/Feedback";
import { ApiKeys } from "@/pages/ApiKeys";
import { Dashboard } from "@/pages/Dashboard";
import { Documentation } from "@/pages/Documentation";
import { Login } from "@/pages/Login";
import { Logs } from "@/pages/Logs";
import { NotFound } from "@/pages/NotFound";
import { Settings } from "@/pages/Settings";

/** Gate for everything behind a session; the API enforces it again server side. */
function RequireAuth() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner label="Checking session" />;
  return user ? <AppShell /> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<RequireAuth />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/keys" element={<ApiKeys />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/docs" element={<Documentation />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </AuthProvider>
  );
}
