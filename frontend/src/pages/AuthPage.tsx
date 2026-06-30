import { useState, type FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ErrorMessage } from "../components/ErrorMessage";
import { Spinner } from "../components/Spinner";

interface Props {
  mode: "login" | "register";
}

export function AuthPage({ mode }: Props) {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isRegister = mode === "register";

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (isRegister) {
        await register(email, password);
      } else {
        await login(email, password);
      }
      navigate("/products");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "操作失敗，請再試一次");
    } finally {
      setLoading(false);
    }
  }

  const inputStyle: React.CSSProperties = {
    width: "100%",
    padding: "10px 14px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: 15,
    outline: "none",
    boxSizing: "border-box",
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f7f8fa",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 20,
      }}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 16,
          padding: 36,
          width: "100%",
          maxWidth: 400,
          boxShadow: "0 2px 16px rgba(0,0,0,.08)",
        }}
      >
        {/* Logo / title */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{ fontWeight: 800, fontSize: 24, color: "#1a1a2e" }}>
            PriceWatch
          </div>
          <div style={{ fontSize: 14, color: "#888", marginTop: 6 }}>
            {isRegister ? "建立帳號" : "登入你的帳號"}
          </div>
        </div>

        {error && (
          <div style={{ marginBottom: 16 }}>
            <ErrorMessage message={error} />
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div>
              <label
                style={{ fontSize: 13, fontWeight: 600, color: "#444" }}
                htmlFor="email"
              >
                電子郵件
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                style={{ ...inputStyle, marginTop: 6 }}
                autoComplete="email"
              />
            </div>

            <div>
              <label
                style={{ fontSize: 13, fontWeight: 600, color: "#444" }}
                htmlFor="password"
              >
                密碼
                {isRegister && (
                  <span style={{ color: "#aaa", fontWeight: 400 }}>
                    {" "}
                    (最少 8 字元)
                  </span>
                )}
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                style={{ ...inputStyle, marginTop: 6 }}
                autoComplete={isRegister ? "new-password" : "current-password"}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                marginTop: 8,
                width: "100%",
                padding: "11px 0",
                background: loading ? "#aaa" : "#1a1a2e",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                fontSize: 15,
                fontWeight: 700,
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 10,
              }}
            >
              {loading && <Spinner size={18} />}
              {isRegister ? "建立帳號" : "登入"}
            </button>
          </div>
        </form>

        <div
          style={{
            textAlign: "center",
            marginTop: 20,
            fontSize: 13,
            color: "#888",
          }}
        >
          {isRegister ? (
            <>
              已有帳號？{" "}
              <Link to="/login" style={{ color: "#1a1a2e", fontWeight: 600 }}>
                登入
              </Link>
            </>
          ) : (
            <>
              還沒有帳號？{" "}
              <Link
                to="/register"
                style={{ color: "#1a1a2e", fontWeight: 600 }}
              >
                立即註冊
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
