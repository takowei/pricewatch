import { useEffect, useState } from "react";
import { alerts as alertsApi } from "../lib/api";
import type { AlertResponse } from "../types";
import { Spinner } from "../components/Spinner";
import { ErrorMessage } from "../components/ErrorMessage";

const REASON_LABEL: Record<string, string> = {
  at_target: "達到目標價",
  price_drop: "價格下降",
};

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("zh-TW", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function AlertsPage() {
  const [items, setItems] = useState<AlertResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [offset, setOffset] = useState(0);
  const LIMIT = 50;

  useEffect(() => {
    setLoading(true);
    setError(null);
    alertsApi
      .list({ offset, limit: LIMIT })
      .then((data) => {
        setItems((prev) => (offset === 0 ? data : [...prev, ...data]));
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "載入失敗");
        setLoading(false);
      });
  }, [offset]);

  const reasonLabel = (reason: string) => REASON_LABEL[reason] ?? reason;

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "32px 20px 60px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 24 }}>
        我的警示
      </h1>

      {loading && offset === 0 && (
        <div style={{ display: "flex", justifyContent: "center", padding: 40 }}>
          <Spinner />
        </div>
      )}

      {error && <ErrorMessage message={error} />}

      {!loading && !error && items.length === 0 && (
        <div
          style={{
            textAlign: "center",
            padding: "60px 0",
            color: "#aaa",
            fontSize: 15,
          }}
        >
          <div style={{ fontSize: 36, marginBottom: 12 }}>--</div>
          目前沒有警示記錄
          <div style={{ fontSize: 13, marginTop: 6 }}>
            在「我的關注」設定關鍵字與目標價後，達標時會出現在這裡
          </div>
        </div>
      )}

      {items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {items.map((alert) => (
            <div
              key={alert.id}
              style={{
                background: "#fff",
                borderRadius: 12,
                padding: "16px 20px",
                boxShadow: "0 1px 4px rgba(0,0,0,.08)",
                display: "flex",
                alignItems: "center",
                gap: 14,
                flexWrap: "wrap",
              }}
            >
              {/* Reason badge */}
              <span
                style={{
                  background:
                    alert.reason === "at_target" ? "#ebf8f0" : "#fff5f5",
                  color: alert.reason === "at_target" ? "#38a169" : "#e53e3e",
                  fontSize: 11,
                  fontWeight: 700,
                  borderRadius: 6,
                  padding: "3px 9px",
                  whiteSpace: "nowrap",
                }}
              >
                {reasonLabel(alert.reason)}
              </span>

              {/* Info */}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 13, color: "#555" }}>
                  商品 #{alert.product_id}
                  <span style={{ margin: "0 6px", color: "#ddd" }}>·</span>
                  關注 #{alert.watchlist_id}
                </div>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: 16,
                    color: "#e53e3e",
                    marginTop: 2,
                  }}
                >
                  NT$ {alert.triggered_price.toLocaleString()}
                </div>
              </div>

              {/* Meta */}
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 12, color: "#aaa" }}>
                  {formatDateTime(alert.created_at)}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    marginTop: 4,
                    color: alert.is_notified ? "#38a169" : "#aaa",
                  }}
                >
                  {alert.is_notified ? "已通知" : "未通知"}
                </div>
              </div>
            </div>
          ))}

          {/* Load more */}
          {items.length === offset + LIMIT && (
            <button
              onClick={() => setOffset((prev) => prev + LIMIT)}
              disabled={loading}
              style={{
                marginTop: 8,
                padding: "10px 0",
                background: "#fff",
                border: "1px solid #ddd",
                borderRadius: 8,
                fontSize: 14,
                color: "#555",
                cursor: loading ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
              }}
            >
              {loading && <Spinner size={16} />}
              載入更多
            </button>
          )}
        </div>
      )}
    </div>
  );
}
