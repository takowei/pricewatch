import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { products as productsApi } from "../lib/api";
import type { PriceHistoryPoint, ProductResponse } from "../types";
import { Spinner } from "./Spinner";
import { ErrorMessage } from "./ErrorMessage";

interface Props {
  product: ProductResponse;
  onClose: () => void;
}

export function PriceHistoryModal({ product, onClose }: Props) {
  const [history, setHistory] = useState<PriceHistoryPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    productsApi
      .history(product.id)
      .then((data) => {
        setHistory(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "載入失敗");
        setLoading(false);
      });
  }, [product.id]);

  const chartData = history.map((h) => ({
    date: h.recorded_date,
    price: h.sale_price,
    discount: h.discount,
  }));

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.45)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 200,
        padding: 20,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 16,
          padding: 28,
          width: "100%",
          maxWidth: 640,
          maxHeight: "90vh",
          overflowY: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: 16,
          }}
        >
          <div>
            <div style={{ fontSize: 12, color: "#888", marginBottom: 4 }}>
              {product.brand.toUpperCase()} · {product.category}
            </div>
            <div style={{ fontWeight: 700, fontSize: 16, lineHeight: 1.4 }}>
              {product.name}
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              fontSize: 22,
              cursor: "pointer",
              color: "#999",
              lineHeight: 1,
              marginLeft: 12,
              flexShrink: 0,
            }}
          >
            x
          </button>
        </div>

        {/* Current price */}
        {product.current_sale_price !== null && (
          <div
            style={{
              display: "flex",
              gap: 12,
              alignItems: "baseline",
              marginBottom: 20,
            }}
          >
            {product.original_price !== null && (
              <span style={{ textDecoration: "line-through", color: "#aaa" }}>
                NT$ {product.original_price.toLocaleString()}
              </span>
            )}
            <span style={{ color: "#e53e3e", fontWeight: 800, fontSize: 22 }}>
              NT$ {product.current_sale_price.toLocaleString()}
            </span>
            {product.discount !== null && (
              <span
                style={{
                  background: "#e53e3e",
                  color: "#fff",
                  borderRadius: 6,
                  padding: "2px 8px",
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                -{product.discount}%
              </span>
            )}
          </div>
        )}

        {/* Chart */}
        {loading && (
          <div
            style={{ display: "flex", justifyContent: "center", padding: 32 }}
          >
            <Spinner />
          </div>
        )}
        {error && <ErrorMessage message={error} />}
        {!loading && !error && chartData.length === 0 && (
          <div style={{ textAlign: "center", color: "#aaa", padding: 32 }}>
            尚無價格歷史資料
          </div>
        )}
        {!loading && !error && chartData.length > 0 && (
          <div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 600,
                color: "#555",
                marginBottom: 10,
              }}
            >
              價格趨勢
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart
                data={chartData}
                margin={{ top: 4, right: 8, left: 0, bottom: 4 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: "#aaa" }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: "#aaa" }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(v: number) => `NT$${v.toLocaleString()}`}
                  width={72}
                />
                <Tooltip
                  formatter={(value) => [
                    typeof value === "number"
                      ? `NT$ ${value.toLocaleString()}`
                      : String(value),
                    "特價",
                  ]}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="#e53e3e"
                  strokeWidth={2}
                  dot={{ r: 4, fill: "#e53e3e" }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* External link */}
        <div style={{ marginTop: 20, textAlign: "right" }}>
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "#1a1a2e",
              fontSize: 13,
              fontWeight: 600,
              textDecoration: "none",
              border: "1px solid #1a1a2e",
              borderRadius: 8,
              padding: "6px 14px",
            }}
          >
            前往商品頁
          </a>
        </div>
      </div>
    </div>
  );
}
