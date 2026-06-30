import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_LINKS = [
  { to: "/products", label: "商品列表" },
  { to: "/watchlist", label: "我的關注" },
  { to: "/alerts", label: "我的警示" },
];

export function NavBar() {
  const { loggedIn, logout } = useAuth();
  const { pathname } = useLocation();

  return (
    <nav
      style={{
        background: "#fff",
        borderBottom: "1px solid #ebebeb",
        position: "sticky",
        top: 0,
        zIndex: 100,
      }}
    >
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "0 20px",
          display: "flex",
          alignItems: "center",
          height: 56,
          gap: 32,
        }}
      >
        {/* Logo */}
        <Link
          to="/products"
          style={{
            fontWeight: 800,
            fontSize: 18,
            color: "#1a1a2e",
            textDecoration: "none",
            letterSpacing: -0.5,
          }}
        >
          PriceWatch
        </Link>

        {/* Nav links */}
        <div style={{ display: "flex", gap: 4, flex: 1 }}>
          {NAV_LINKS.map(({ to, label }) => {
            const active = pathname.startsWith(to);
            return (
              <Link
                key={to}
                to={to}
                style={{
                  padding: "6px 14px",
                  borderRadius: 8,
                  fontSize: 14,
                  fontWeight: active ? 700 : 400,
                  color: active ? "#1a1a2e" : "#666",
                  background: active ? "#f0f0f5" : "transparent",
                  textDecoration: "none",
                  transition: "background 0.15s",
                }}
              >
                {label}
              </Link>
            );
          })}
        </div>

        {/* Auth action */}
        {loggedIn ? (
          <button
            onClick={logout}
            style={{
              padding: "6px 16px",
              border: "1px solid #ddd",
              borderRadius: 8,
              background: "#fff",
              color: "#555",
              fontSize: 13,
              cursor: "pointer",
            }}
          >
            登出
          </button>
        ) : (
          <Link
            to="/login"
            style={{
              padding: "6px 16px",
              border: "1px solid #1a1a2e",
              borderRadius: 8,
              background: "#1a1a2e",
              color: "#fff",
              fontSize: 13,
              textDecoration: "none",
            }}
          >
            登入
          </Link>
        )}
      </div>
    </nav>
  );
}
