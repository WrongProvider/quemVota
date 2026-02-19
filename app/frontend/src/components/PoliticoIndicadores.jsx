function calcularEficiencia(stats) {
  if (!stats.total_votacoes || !stats.total_gasto) return 0

  const custoPorVotacao = stats.total_gasto / stats.total_votacoes

  // escala ajustável
  const score = 100000 / custoPorVotacao

  return Math.min(Math.round(score), 100)
}

export function IndicadorEficiencia({ stats }) {
  const score = calcularEficiencia(stats)

  let cor = "#d32f2f"

  if (score > 80) cor = "#2e7d32"
  else if (score > 50) cor = "#f9a825"

  return (
    <div style={{ marginTop: "2rem" }}>
      <h3>Índice de Eficiência</h3>

      <div
        style={{
          background: "#eee",
          borderRadius: "8px",
          overflow: "hidden",
          height: "20px",
          marginTop: "1rem",
        }}
      >
        <div
          style={{
            width: `${score}%`,
            background: cor,
            height: "100%",
            transition: "0.4s ease",
          }}
        />
      </div>

      <p style={{ marginTop: "0.5rem" }}>
        Score: <strong>{score}/100</strong>
      </p>
    </div>
  )
}
