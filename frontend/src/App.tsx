import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import { NavBar } from "./components/NavBar";
import { AuthPage } from "./pages/AuthPage";
import { ProductsPage } from "./pages/ProductsPage";
import { WatchlistPage } from "./pages/WatchlistPage";
import { AlertsPage } from "./pages/AlertsPage";
import { Spinner } from "./components/Spinner";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { loggedIn, loading } = useAuth();
  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "60vh",
        }}
      >
        <Spinner size={40} />
      </div>
    );
  }
  return loggedIn ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  const { loading } = useAuth();

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "100vh",
        }}
      >
        <Spinner size={40} />
      </div>
    );
  }

  return (
    <>
      <NavBar />
      <Routes>
        {/* Public */}
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />

        {/* Products: public-accessible (auth optional per spec) */}
        <Route path="/products" element={<ProductsPage />} />

        {/* Protected */}
        <Route
          path="/watchlist"
          element={
            <RequireAuth>
              <WatchlistPage />
            </RequireAuth>
          }
        />
        <Route
          path="/alerts"
          element={
            <RequireAuth>
              <AlertsPage />
            </RequireAuth>
          }
        />

        {/* Default redirect */}
        <Route path="*" element={<Navigate to="/products" replace />} />
      </Routes>
    </>
  );
}
