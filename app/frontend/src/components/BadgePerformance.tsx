type BadgePerformanceProps = {
  score?: number
}

function classificarPerformance(score: number) {
  if (score >= 85)
    return { label: "🏆 Excelente", color: "#2e7d32" }

  if (score >= 70)
    return { label: "🟢 Muito Bom", color: "#43A047" }

  if (score >= 55)
    return { label: "🟡 Regular", color: "#f9a825" }

  if (score >= 40)
    return { label: "🟠 Baixo", color: "#ef6c00" }

  return { label: "🔴 Crítico", color: "#d32f2f" }
}

export default function BadgePerformance({ score = 0 }: BadgePerformanceProps) {
  const scoreNormalizado = Math.max(0, Math.min(100, score))
  const { label, color } = classificarPerformance(scoreNormalizado)

  return (
    <div
      style={{
        display: "inline-block",
        padding: "0.6rem 1.2rem",
        borderRadius: "999px",
        backgroundColor: color,
        color: "white",
        fontWeight: 600,
        fontSize: "0.9rem",
        marginTop: "1rem",
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
        transition: "all 0.3s ease",
      }}
    >
      {label} — {scoreNormalizado.toFixed(1)}
    </div>
  )
}
