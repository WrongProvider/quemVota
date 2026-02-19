import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts"

export default function PoliticoGraficos({ stats }) {
  if (!stats) return null

  const dadosFinanceiros = [
    {
      name: "Total Gasto",
      valor: stats.total_gasto,
    },
    {
      name: "Média Mensal",
      valor: stats.media_mensal,
    },
  ]

  const dadosAtividade = [
    {
      name: "Votações",
      value: stats.total_votacoes,
    },
    {
      name: "Despesas",
      value: stats.total_despesas,
    },
  ]

  const COLORS = ["#1E88E5", "#43A047"]

  return (
    <div style={{ marginTop: "3rem" }}>
      <h2>📊 Análise Visual</h2>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(350px, 1fr))",
          gap: "2rem",
          marginTop: "2rem",
        }}
      >
        {/* ===== GRÁFICO DE BARRAS ===== */}
        <div>
          <h3>Gastos</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dadosFinanceiros}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip formatter={(value) =>
                `R$ ${Number(value).toLocaleString("pt-BR")}`
              } />
              <Bar dataKey="valor" fill="#1E88E5" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* ===== GRÁFICO DE PIZZA ===== */}
        <div>
          <h3>Atividade Parlamentar</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={dadosAtividade}
                dataKey="value"
                nameKey="name"
                outerRadius={100}
                label
              >
                {dadosAtividade.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

