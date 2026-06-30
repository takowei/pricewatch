import { useState } from "react";
import type { ProductResponse } from "../types";

const BRAND_COLOR: Record<string, string> = {
  uniqlo: "#FF0000",
  net: "#0052A5",
};

function fmt(n: number) {
  return `NT$ ${n.toLocaleString()}`;
}

interface Props {
  product: ProductResponse;
  onClick: () => void;
}

export function ProductCard({ product, onClick }: Props) {
  const [imgErr, setImgErr] = useState(false);
  const brandColor = BRAND_COLOR[product.brand.toLowerCase()] ?? "#555";

  const salePrice = product.current_sale_price;
  const origPrice = product.original_price;
  const discount = product.discount;

  return (
    <div
      onClick={onClick}
      style={{
        background: "#fff",
        borderRadius: 12,
        overflow: "hidden",
        boxShadow: "0 1px 4px rgba(0,0,0,.08)",
        display: "flex",
        flexDirection: "column",
        cursor: "pointer",
        position: "relative",
        transition: "box-shadow 0.2s",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLDivElement).style.boxShadow =
          "0 4px 16px rgba(0,0,0,.14)";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLDivElement).style.boxShadow =
          "0 1px 4px rgba(0,0,0,.08)";
      }}
    >
      {/* Discount badge */}
      {discount !== null && (
        <div
          style={{
            position: "absolute",
            top: 10,
            left: 10,
            background: "#e53e3e",
            color: "#fff",
            borderRadius: 6,
            padding: "2px 8px",
            fontSize: 12,
            fontWeight: 700,
            zIndex: 1,
          }}
        >
          -{discount}%
        </div>
      )}

      {/* Image */}
      <div
        style={{
          width: "100%",
          aspectRatio: "1 / 1",
          background: "#f0f0f0",
          overflow: "hidden",
        }}
      >
        {imgErr || !product.image_url ? (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: brandColor,
              fontWeight: 700,
              fontSize: 18,
            }}
          >
            {product.brand.toUpperCase()}
          </div>
        ) : (
          <img
            src={product.image_url}
            alt={product.name}
            loading="lazy"
            referrerPolicy="no-referrer"
            onError={() => setImgErr(true)}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </div>

      {/* Body */}
      <div
        style={{
          padding: "12px 14px",
          display: "flex",
          flexDirection: "column",
          gap: 6,
          flex: 1,
        }}
      >
        {/* Brand + category */}
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              background: brandColor,
              color: "#fff",
              fontSize: 10,
              fontWeight: 700,
              borderRadius: 4,
              padding: "1px 6px",
            }}
          >
            {product.brand.toUpperCase()}
          </span>
          <span
            style={{
              fontSize: 11,
              color: "#888",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {product.category}
          </span>
        </div>

        {/* Name */}
        <div
          style={{
            fontWeight: 600,
            fontSize: 14,
            lineHeight: 1.4,
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
          }}
        >
          {product.name}
        </div>

        {/* Price */}
        <div
          style={{
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            flexWrap: "wrap",
          }}
        >
          {origPrice !== null && (
            <span
              style={{
                textDecoration: "line-through",
                color: "#aaa",
                fontSize: 12,
              }}
            >
              {fmt(origPrice)}
            </span>
          )}
          {salePrice !== null && (
            <span style={{ color: "#e53e3e", fontWeight: 700, fontSize: 16 }}>
              {fmt(salePrice)}
            </span>
          )}
        </div>
        {origPrice !== null && salePrice !== null && origPrice > salePrice && (
          <div style={{ fontSize: 11, color: "#38a169" }}>
            省下 {fmt(origPrice - salePrice)}
          </div>
        )}
      </div>
    </div>
  );
}
