export function ErrorMessage({ message }: { message: string }) {
  return (
    <div
      style={{
        background: "#fff5f5",
        border: "1px solid #fc8181",
        borderRadius: 8,
        padding: "12px 16px",
        color: "#c53030",
        fontSize: 14,
      }}
    >
      {message}
    </div>
  );
}
