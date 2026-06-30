export function Spinner({ size = 36 }: { size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        border: `${Math.max(3, size / 10)}px solid #ebebeb`,
        borderTop: `${Math.max(3, size / 10)}px solid #1a1a2e`,
        borderRadius: "50%",
        animation: "spin 0.8s linear infinite",
      }}
    />
  );
}
