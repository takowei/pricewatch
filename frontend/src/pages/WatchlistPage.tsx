import { useEffect, useState, type FormEvent } from "react";
import { watchlist as watchlistApi } from "../lib/api";
import type { WatchlistResponse } from "../types";
import { Spinner } from "../components/Spinner";
import { ErrorMessage } from "../components/ErrorMessage";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("zh-TW", {
    year: "numeric",
    month: "numeric",
    day: "numeric",
  });
}

export function WatchlistPage() {
  const [items, setItems] = useState<WatchlistResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // create form
  const [keyword, setKeyword] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // edit state: item id → draft values
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editKeyword, setEditKeyword] = useState("");
  const [editMaxPrice, setEditMaxPrice] = useState("");
  const [editActive, setEditActive] = useState(true);
  const [saving, setSaving] = useState(false);

  function load() {
    setLoading(true);
    setError(null);
    watchlistApi
      .list()
      .then((data) => {
        setItems(data);
        setLoading(false);
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "載入失敗");
        setLoading(false);
      });
  }

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: FormEvent) {
    e.preventDefault();
    setCreateError(null);
    setCreating(true);
    try {
      const item = await watchlistApi.create({
        keyword: keyword.trim(),
        max_price: maxPrice ? Number(maxPrice) : null,
      });
      setItems((prev) => [item, ...prev]);
      setKeyword("");
      setMaxPrice("");
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : "新增失敗");
    } finally {
      setCreating(false);
    }
  }

  function startEdit(item: WatchlistResponse) {
    setEditingId(item.id);
    setEditKeyword(item.keyword);
    setEditMaxPrice(item.max_price !== null ? String(item.max_price) : "");
    setEditActive(item.is_active);
  }

  async function handleSave(id: number) {
    setSaving(true);
    try {
      const updated = await watchlistApi.update(id, {
        keyword: editKeyword.trim(),
        max_price: editMaxPrice ? Number(editMaxPrice) : null,
        is_active: editActive,
      });
      setItems((prev) => prev.map((it) => (it.id === id ? updated : it)));
      setEditingId(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "更新失敗");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm("確定要刪除這個關注嗎？")) return;
    try {
      await watchlistApi.remove(id);
      setItems((prev) => prev.filter((it) => it.id !== id));
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "刪除失敗");
    }
  }

  const inputStyle: React.CSSProperties = {
    padding: "8px 12px",
    border: "1px solid #ddd",
    borderRadius: 8,
    fontSize: 14,
    outline: "none",
  };

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "32px 20px 60px" }}>
      <h1 style={{ fontSize: 22, fontWeight: 800, marginBottom: 24 }}>
        我的關注
      </h1>

      {/* Add form */}
      <div
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: 20,
          boxShadow: "0 1px 4px rgba(0,0,0,.08)",
          marginBottom: 28,
        }}
      >
        <div
          style={{
            fontSize: 14,
            fontWeight: 700,
            marginBottom: 14,
            color: "#1a1a2e",
          }}
        >
          新增關注
        </div>
        {createError && (
          <div style={{ marginBottom: 12 }}>
            <ErrorMessage message={createError} />
          </div>
        )}
        <form onSubmit={handleCreate}>
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <input
              required
              type="text"
              placeholder="關鍵字（如：帽 T、牛仔褲）"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              style={{ ...inputStyle, flex: "2 1 160px" }}
            />
            <input
              type="number"
              min={0}
              placeholder="目標價（NT$，留空=只要特價）"
              value={maxPrice}
              onChange={(e) => setMaxPrice(e.target.value)}
              style={{ ...inputStyle, flex: "1 1 140px" }}
            />
            <button
              type="submit"
              disabled={creating}
              style={{
                padding: "8px 18px",
                background: creating ? "#aaa" : "#1a1a2e",
                color: "#fff",
                border: "none",
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 700,
                cursor: creating ? "not-allowed" : "pointer",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              {creating && <Spinner size={14} />}
              新增
            </button>
          </div>
        </form>
      </div>

      {/* List */}
      {loading && (
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
          尚無關注項目，從上方新增吧！
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {items.map((item) => {
            const isEditing = editingId === item.id;
            return (
              <div
                key={item.id}
                style={{
                  background: "#fff",
                  borderRadius: 12,
                  padding: "16px 20px",
                  boxShadow: "0 1px 4px rgba(0,0,0,.08)",
                  display: "flex",
                  alignItems: isEditing ? "flex-start" : "center",
                  gap: 12,
                  flexWrap: "wrap",
                  opacity: item.is_active ? 1 : 0.55,
                }}
              >
                {isEditing ? (
                  /* Edit mode */
                  <div
                    style={{
                      flex: 1,
                      display: "flex",
                      flexDirection: "column",
                      gap: 10,
                    }}
                  >
                    <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                      <input
                        type="text"
                        value={editKeyword}
                        onChange={(e) => setEditKeyword(e.target.value)}
                        style={{ ...inputStyle, flex: "2 1 140px" }}
                      />
                      <input
                        type="number"
                        min={0}
                        placeholder="目標價（留空=只要特價）"
                        value={editMaxPrice}
                        onChange={(e) => setEditMaxPrice(e.target.value)}
                        style={{ ...inputStyle, flex: "1 1 120px" }}
                      />
                    </div>
                    <label
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: 8,
                        fontSize: 13,
                        color: "#555",
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={editActive}
                        onChange={(e) => setEditActive(e.target.checked)}
                      />
                      啟用中
                    </label>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        onClick={() => handleSave(item.id)}
                        disabled={saving}
                        style={{
                          padding: "6px 14px",
                          background: "#1a1a2e",
                          color: "#fff",
                          border: "none",
                          borderRadius: 7,
                          fontSize: 13,
                          fontWeight: 700,
                          cursor: saving ? "not-allowed" : "pointer",
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                        }}
                      >
                        {saving && <Spinner size={12} />}
                        儲存
                      </button>
                      <button
                        onClick={() => setEditingId(null)}
                        style={{
                          padding: "6px 14px",
                          background: "#fff",
                          color: "#555",
                          border: "1px solid #ddd",
                          borderRadius: 7,
                          fontSize: 13,
                          cursor: "pointer",
                        }}
                      >
                        取消
                      </button>
                    </div>
                  </div>
                ) : (
                  /* View mode */
                  <>
                    <div style={{ flex: 1 }}>
                      <div
                        style={{
                          fontWeight: 700,
                          fontSize: 15,
                          color: "#1a1a2e",
                        }}
                      >
                        {item.keyword}
                      </div>
                      <div
                        style={{ fontSize: 12, color: "#888", marginTop: 4 }}
                      >
                        目標價：
                        {item.max_price !== null
                          ? `NT$ ${item.max_price.toLocaleString()}`
                          : "只要特價即觸發"}
                        {" · "}
                        建立於 {formatDate(item.created_at)}
                      </div>
                    </div>
                    <span
                      style={{
                        fontSize: 11,
                        padding: "2px 8px",
                        borderRadius: 10,
                        background: item.is_active ? "#ebf8f0" : "#f0f0f0",
                        color: item.is_active ? "#38a169" : "#aaa",
                        fontWeight: 600,
                      }}
                    >
                      {item.is_active ? "啟用中" : "已停用"}
                    </span>
                    <div style={{ display: "flex", gap: 8 }}>
                      <button
                        onClick={() => startEdit(item)}
                        style={{
                          padding: "5px 12px",
                          background: "#fff",
                          border: "1px solid #ddd",
                          borderRadius: 7,
                          fontSize: 12,
                          cursor: "pointer",
                          color: "#555",
                        }}
                      >
                        編輯
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        style={{
                          padding: "5px 12px",
                          background: "#fff",
                          border: "1px solid #fc8181",
                          borderRadius: 7,
                          fontSize: 12,
                          cursor: "pointer",
                          color: "#e53e3e",
                        }}
                      >
                        刪除
                      </button>
                    </div>
                  </>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
