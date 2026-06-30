import { useEffect, useState } from "react";
import { products as productsApi } from "../lib/api";
import type { ProductResponse } from "../types";
import { ProductCard } from "../components/ProductCard";
import { PriceHistoryModal } from "../components/PriceHistoryModal";
import { Spinner } from "../components/Spinner";
import { ErrorMessage } from "../components/ErrorMessage";

const SORT_OPTIONS = [
  { value: "discount", label: "折扣最高" },
  { value: "price_asc", label: "價格低 → 高" },
  { value: "price_desc", label: "價格高 → 低" },
];

function sortProducts(
  items: ProductResponse[],
  sort: string,
): ProductResponse[] {
  const copy = [...items];
  if (sort === "discount") {
    return copy.sort(
      (a, b) =>
        (b.discount ?? 0) - (a.discount ?? 0) ||
        (b.original_price ?? 0) -
          (b.current_sale_price ?? 0) -
          ((a.original_price ?? 0) - (a.current_sale_price ?? 0)),
    );
  }
  if (sort === "price_asc") {
    return copy.sort(
      (a, b) =>
        (a.current_sale_price ?? 0) - (b.current_sale_price ?? 0) ||
        (b.discount ?? 0) - (a.discount ?? 0),
    );
  }
  if (sort === "price_desc") {
    return copy.sort(
      (a, b) =>
        (b.current_sale_price ?? 0) - (a.current_sale_price ?? 0) ||
        (b.discount ?? 0) - (a.discount ?? 0),
    );
  }
  return copy;
}

export function ProductsPage() {
  const [allProducts, setAllProducts] = useState<ProductResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ProductResponse | null>(null);

  // filter + sort state
  const [brandTab, setBrandTab] = useState("all");
  const [keyword, setKeyword] = useState("");
  const [sort, setSort] = useState("discount");

  useEffect(() => {
    setLoading(true);
    setError(null);
    productsApi
      .list({ limit: 200 })
      .then((data) => {
        setAllProducts(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "載入失敗");
        setLoading(false);
      });
  }, []);

  // derive brand list from data
  const brands = [
    "all",
    ...Array.from(new Set(allProducts.map((p) => p.brand))).sort(),
  ];

  // filter
  let filtered = allProducts;
  if (brandTab !== "all")
    filtered = filtered.filter((p) => p.brand === brandTab);
  if (keyword.trim()) {
    const q = keyword.trim().toLowerCase();
    filtered = filtered.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q),
    );
  }
  filtered = sortProducts(filtered, sort);

  const tabStyle = (active: boolean): React.CSSProperties => ({
    padding: "10px 18px",
    border: "none",
    borderBottom: active ? "2px solid #1a1a2e" : "2px solid transparent",
    background: "none",
    cursor: "pointer",
    fontWeight: active ? 700 : 400,
    fontSize: 14,
    color: active ? "#1a1a2e" : "#777",
  });

  return (
    <div>
      {/* Sticky filter bar */}
      <div
        style={{
          background: "#fff",
          borderBottom: "1px solid #ebebeb",
          position: "sticky",
          top: 56,
          zIndex: 90,
        }}
      >
        <div style={{ maxWidth: 1280, margin: "0 auto", padding: "0 20px" }}>
          {/* Top row: title + search + sort */}
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              padding: "12px 0 0",
              flexWrap: "wrap",
              gap: 10,
            }}
          >
            <div style={{ fontWeight: 700, fontSize: 16, color: "#1a1a2e" }}>
              特價商品{" "}
              {!loading && (
                <span style={{ fontWeight: 400, fontSize: 13, color: "#aaa" }}>
                  ({filtered.length} 件)
                </span>
              )}
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              <input
                type="text"
                placeholder="搜尋商品或類別…"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                style={{
                  padding: "7px 12px",
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  fontSize: 13,
                  outline: "none",
                  width: 200,
                }}
              />
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value)}
                style={{
                  padding: "7px 12px",
                  border: "1px solid #ddd",
                  borderRadius: 8,
                  background: "#fff",
                  fontSize: 13,
                  cursor: "pointer",
                }}
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Brand tabs */}
          <div style={{ display: "flex", gap: 0, marginTop: 4 }}>
            {brands.map((b) => {
              const count =
                b === "all"
                  ? allProducts.length
                  : allProducts.filter((p) => p.brand === b).length;
              return (
                <button
                  key={b}
                  style={tabStyle(brandTab === b)}
                  onClick={() => setBrandTab(b)}
                >
                  {b === "all" ? "全部" : b.toUpperCase()}
                  <span style={{ marginLeft: 4, fontSize: 11, color: "#aaa" }}>
                    ({count})
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main content */}
      <div
        style={{
          maxWidth: 1280,
          margin: "0 auto",
          padding: "20px 20px 60px",
        }}
      >
        {loading && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 16,
              padding: "80px 0",
            }}
          >
            <Spinner size={40} />
            <span style={{ color: "#888" }}>載入商品中…</span>
          </div>
        )}

        {error && <ErrorMessage message={error} />}

        {!loading && !error && filtered.length === 0 && (
          <div
            style={{ textAlign: "center", padding: "80px 0", color: "#aaa" }}
          >
            <div style={{ fontSize: 40, marginBottom: 12 }}>?</div>
            <div style={{ fontSize: 16 }}>找不到符合條件的商品</div>
            <div style={{ fontSize: 13, marginTop: 6 }}>
              試著調整搜尋條件或篩選
            </div>
          </div>
        )}

        {!loading && !error && filtered.length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(230px, 1fr))",
              gap: 20,
            }}
          >
            {filtered.map((p) => (
              <ProductCard
                key={p.id}
                product={p}
                onClick={() => setSelected(p)}
              />
            ))}
          </div>
        )}
      </div>

      {selected && (
        <PriceHistoryModal
          product={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
