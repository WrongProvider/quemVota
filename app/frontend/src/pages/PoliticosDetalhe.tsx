import { useParams } from "react-router-dom"
import { usePoliticoEstatisticas, usePoliticoDetalhe } from "../hooks/usePoliticos"
import PoliticoGraficos from "../components/PoliticoGraficos"
import { IndicadorEficiencia } from "../components/PoliticoIndicadores"
export default function PoliticoDetalhe() {
  const { id } = useParams()
  const politicoId = Number(id)
  const { data, isLoading, error } = usePoliticoDetalhe(politicoId)
  const { data: stats } = usePoliticoEstatisticas(politicoId)

  if (isLoading) return <p>Carregando...</p>
  if (error) return <p>Erro ao carregar político.</p>
  if (!data) return null

  return (
    <div style={{ padding: "2rem" }}>
      {/* ===== DADOS PRINCIPAIS ===== */}
      <div style={{ display: "flex", gap: "2rem", alignItems: "center" }}>
        <img
          src={data.url_foto}
          alt={data.nome}
          width={150}
        />

        <div>
          <h1>{data.nome}</h1>
          <p><strong>UF:</strong> {data.uf}</p>
          <p><strong>Partido:</strong> {data.partido_sigla}</p>
          <p><strong>Escolaridade:</strong> {data.escolaridade}</p>
          <p><strong>Situação:</strong> {data.situacao}</p>
          <p><strong>Condição Eleitoral:</strong> {data.condicao_eleitoral}</p>
          <p><strong>Email:</strong> {data.email_gabinete}</p>
          <p><strong>Telefone:</strong> {data.telefone_gabinete}</p>
        </div>
      </div>

      {/* ===== ESTATÍSTICAS ===== */}
      {stats && (
        <div style={{ marginTop: "3rem" }}>
          <h2>Estatísticas</h2>

          <div style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: "1rem",
            marginTop: "1rem"
          }}>
            <StatCard titulo="Total de Votações" valor={stats.total_votacoes} />
            <StatCard titulo="Total de Despesas" valor={stats.total_despesas} />
            <StatCard
              titulo="Total Gasto"
              valor={`R$ ${stats.total_gasto.toLocaleString("pt-BR")}`}
            />
            <StatCard
              titulo="Média Mensal"
              valor={`R$ ${stats.media_mensal.toLocaleString("pt-BR")}`}
            />
            <StatCard
              titulo="Primeiro Ano"
              valor={stats.primeiro_ano ?? "-"}
            />
            <StatCard
              titulo="Último Ano"
              valor={stats.ultimo_ano ?? "-"}
            />
          </div>
        </div>
      )}
      {stats && <PoliticoGraficos stats={stats} />}
      {stats && <IndicadorEficiencia stats={stats} />}

    </div>
  )
}

function StatCard({ titulo, valor }: { titulo: string; valor: any }) {
  return (
    <div
      style={{
        padding: "1rem",
        borderRadius: "8px",
        background: "#f5f5f5",
      }}
    >
      <p style={{ fontSize: "0.9rem", opacity: 0.7 }}>{titulo}</p>
      <h3>{valor}</h3>
    </div>
  )
}
