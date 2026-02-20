import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  PieChart,
  Pie,
  Cell,
} from "recharts"

import BadgePerformance from "./BadgePerformance"
import InfoBotao from "./InfoDicaBotao"
import ToolDica from "./InfoDica"

export default function PoliticoGraficos({ performance }) {
  if (!performance) return null

  const dadosScore = [
    {
      name: "Performance do Político",
      valor: performance.score_final,
    },
    {
      name: "Performance Média dos Parlamentares",
      valor: performance.media_global,
    },
  ]

  const detalhes = performance.detalhes || {
    nota_assiduidade: 0,
    nota_economia: 0,
    nota_producao: 0,
  }

  const dadosRadar = [
    { subject: "Assiduidade", A: detalhes.nota_assiduidade },
    { subject: "Economia", A: detalhes.nota_economia },
    { subject: "Produção", A: detalhes.nota_producao },
  ]

  const dadosCota = [
    { name: "Utilizado", value: performance.info.cota_utilizada_pct },
    { name: "Restante", value: 100 - performance.info.cota_utilizada_pct },
  ]

  const COLORS = ["#1E88E5", "#E0E0E0"]

  return (
    <div style={{ marginTop: "3rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
        <h2>📊 Performance Parlamentar</h2>
        <ToolDica content="O score é calculado com base em assiduidade, economia e produção parlamentar. Clique para saber mais.">
          <InfoBotao onClick={() => {}} />
        </ToolDica>
      </div>
      <BadgePerformance score={performance.score_final} />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))",
          gap: "2rem",
          marginTop: "2rem",
        }}
      >
        {/* ===== SCORE VS MÉDIA ===== */}
        <div>
          <h3>Score Comparativo</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dadosScore}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="name"
                interval={0}
                tickFormatter={(value) =>
                  value.length > 20 ? value.substring(0, 17) + "..." : value
                }
                angle={-10}
                textAnchor="end"
                height={60}
                tick={{ fontSize: 12 }}
              />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="valor" fill="#1E88E5" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* ===== RADAR ===== */}
        <div>
          <h3>Composição do Score</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadarChart data={dadosRadar}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <Radar
                name="Score"
                dataKey="A"
                stroke="#43A047"
                fill="#43A047"
                fillOpacity={0.6}
              />
              <Tooltip
                formatter={(value) => [`${value}`, "Nota"]}
                labelFormatter={(label) => `Critério: ${label}`}
              />
            </RadarChart>
          </ResponsiveContainer>

        </div>

        {/* ===== USO DA COTA ===== */}
        <div>
          <h3>Uso da Cota Parlamentar</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={dadosCota}
                dataKey="value"
                nameKey="name"
                outerRadius={100}
              >
                {dadosCota.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => `${v}%`} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
