import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  FileText, 
  Award,
  Building2,
  Users,
  Filter,
  Search
} from "lucide-react"

// Hook customizado para buscar rankings
function useRanking(endpoint: string, params: Record<string, any> = {}) {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      
      try {
        const queryString = new URLSearchParams(
          Object.entries(params).reduce((acc, [key, value]) => {
            if (value !== null && value !== undefined && value !== "") {
              acc[key] = String(value)
            }
            return acc
          }, {} as Record<string, string>)
        ).toString()
        
        const url = `http://localhost:8000/api/ranking${endpoint}${queryString ? `?${queryString}` : ""}`
        const response = await fetch(url)
        
        if (!response.ok) throw new Error("Erro ao buscar dados")
        
        const result = await response.json()
        setData(result)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro desconhecido")
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [endpoint, JSON.stringify(params)])

  return { data, loading, error }
}

export default function Rankings() {
  const [activeTab, setActiveTab] = useState<"performance" | "gastos" | "economia" | "empresas" | "discursos">("performance")
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedUF, setSelectedUF] = useState("")

  // Estados brasileiros
  const UFs = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA",
    "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN",
    "RO", "RR", "RS", "SC", "SE", "SP", "TO"
  ]

  return (
    <div style={{ 
      maxWidth: "1400px", 
      margin: "0 auto", 
      padding: "2rem",
      fontFamily: "system-ui, -apple-system, sans-serif"
    }}>
      {/* HEADER */}
      <div style={{ marginBottom: "2rem" }}>
        <h1 style={{ 
          fontSize: "2.5rem", 
          fontWeight: "bold", 
          marginBottom: "0.5rem",
          color: "#1E293B",
          display: "flex",
          alignItems: "center",
          gap: "0.75rem"
        }}>
          <Award size={40} color="#F59E0B" />
          Rankings Parlamentares
        </h1>
        <p style={{ fontSize: "1.1rem", color: "#64748B" }}>
          Confira os parlamentares em destaque nas principais métricas de desempenho
        </p>
      </div>

      {/* TABS DE NAVEGAÇÃO */}
      <div style={{
        display: "flex",
        gap: "0.5rem",
        marginBottom: "2rem",
        borderBottom: "2px solid #E2E8F0",
        overflowX: "auto",
        paddingBottom: "0.5rem"
      }}>
        <TabButton
          active={activeTab === "performance"}
          onClick={() => setActiveTab("performance")}
          icon={<TrendingUp size={20} />}
          label="Melhor Performance"
        />
        <TabButton
          active={activeTab === "gastos"}
          onClick={() => setActiveTab("gastos")}
          icon={<TrendingDown size={20} />}
          label="Maiores Gastos"
        />
        <TabButton
          active={activeTab === "economia"}
          onClick={() => setActiveTab("economia")}
          icon={<DollarSign size={20} />}
          label="Mais Econômicos"
        />
        <TabButton
          active={activeTab === "discursos"}
          onClick={() => setActiveTab("discursos")}
          icon={<FileText size={20} />}
          label="Mais Discursos"
        />
        <TabButton
          active={activeTab === "empresas"}
          onClick={() => setActiveTab("empresas")}
          icon={<Building2 size={20} />}
          label="Empresas Beneficiadas"
        />
      </div>

      {/* FILTROS (apenas para rankings de políticos) */}
      {activeTab !== "empresas" && (
        <div style={{
          display: "flex",
          gap: "1rem",
          marginBottom: "2rem",
          flexWrap: "wrap",
          alignItems: "center"
        }}>
          <div style={{ flex: "1", minWidth: "250px" }}>
            <div style={{ position: "relative" }}>
              <Search 
                size={20} 
                style={{ 
                  position: "absolute", 
                  left: "12px", 
                  top: "50%", 
                  transform: "translateY(-50%)",
                  color: "#94A3B8"
                }} 
              />
              <input
                type="text"
                placeholder="Buscar parlamentar..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: "100%",
                  padding: "0.75rem 1rem 0.75rem 2.75rem",
                  border: "2px solid #E2E8F0",
                  borderRadius: "8px",
                  fontSize: "1rem"
                }}
              />
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <Filter size={20} color="#64748B" />
            <select
              value={selectedUF}
              onChange={(e) => setSelectedUF(e.target.value)}
              style={{
                padding: "0.75rem 1rem",
                border: "2px solid #E2E8F0",
                borderRadius: "8px",
                fontSize: "1rem",
                backgroundColor: "white",
                cursor: "pointer"
              }}
            >
              <option value="">Todos os Estados</option>
              {UFs.map(uf => (
                <option key={uf} value={uf}>{uf}</option>
              ))}
            </select>
          </div>

          {(searchTerm || selectedUF) && (
            <button
              onClick={() => {
                setSearchTerm("")
                setSelectedUF("")
              }}
              style={{
                padding: "0.75rem 1.5rem",
                backgroundColor: "#F1F5F9",
                border: "none",
                borderRadius: "8px",
                cursor: "pointer",
                fontSize: "0.9rem",
                fontWeight: 500
              }}
            >
              Limpar Filtros
            </button>
          )}
        </div>
      )}

      {/* CONTEÚDO DOS RANKINGS */}
      <div>
        {activeTab === "performance" && <RankingPerformance />}
        {activeTab === "gastos" && <RankingGastos searchTerm={searchTerm} selectedUF={selectedUF} />}
        {activeTab === "economia" && <RankingEconomia searchTerm={searchTerm} selectedUF={selectedUF} />}
        {activeTab === "discursos" && <RankingDiscursos />}
        {activeTab === "empresas" && <RankingEmpresas />}
      </div>
    </div>
  )
}

// ========== COMPONENTES DOS RANKINGS ==========

function RankingPerformance() {
  const { data, loading, error } = useRanking("/performance_politicos")

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  const top3 = data.slice(0, 3)
  const rest = data.slice(3, 50)

  return (
    <div>
      {/* PÓDIO TOP 3 */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
        gap: "1.5rem",
        marginBottom: "3rem"
      }}>
        {top3.map((politico, index) => (
          <PodiumCard 
            key={politico.id} 
            politico={politico} 
            position={index + 1}
          />
        ))}
      </div>

      {/* RANKING COMPLETO */}
      <h3 style={{ 
        fontSize: "1.5rem", 
        fontWeight: "bold", 
        marginBottom: "1.5rem",
        color: "#1E293B"
      }}>
        Top 50 Parlamentares
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {rest.map((politico, index) => (
          <RankingCard
            key={politico.id}
            position={index + 4}
            politico={politico}
            type="performance"
          />
        ))}
      </div>
    </div>
  )
}

function RankingGastos({ searchTerm, selectedUF }: { searchTerm: string, selectedUF: string }) {
  const { data, loading, error } = useRanking("/despesa_politico", {
    q: searchTerm,
    uf: selectedUF,
    limit: 50
  })

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  return (
    <div>
      <h3 style={{ 
        fontSize: "1.5rem", 
        fontWeight: "bold", 
        marginBottom: "1.5rem",
        color: "#1E293B"
      }}>
        Parlamentares com Maiores Gastos
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {data.map((item, index) => (
          <RankingCard
            key={item.politico_id}
            position={index + 1}
            politico={{
              id: item.politico_id,
              nome: item.nome,
              total_gasto: item.total_gasto
            }}
            type="gastos"
          />
        ))}
      </div>
    </div>
  )
}

function RankingEconomia({ searchTerm, selectedUF }: { searchTerm: string, selectedUF: string }) {
  const { data, loading, error } = useRanking("/despesa_politico", {
    q: searchTerm,
    uf: selectedUF,
    limit: 100
  })

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  // Ordena do menor gasto para o maior (mais econômicos primeiro)
  const sortedData = [...data].sort((a, b) => a.total_gasto - b.total_gasto).slice(0, 50)

  return (
    <div>
      <h3 style={{ 
        fontSize: "1.5rem", 
        fontWeight: "bold", 
        marginBottom: "1.5rem",
        color: "#1E293B"
      }}>
        Parlamentares Mais Econômicos
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {sortedData.map((item, index) => (
          <RankingCard
            key={item.politico_id}
            position={index + 1}
            politico={{
              id: item.politico_id,
              nome: item.nome,
              total_gasto: item.total_gasto
            }}
            type="economia"
          />
        ))}
      </div>
    </div>
  )
}

function RankingDiscursos() {
  const { data, loading, error } = useRanking("/discursos", { limit: 50 })

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  return (
    <div>
      <h3 style={{ 
        fontSize: "1.5rem", 
        fontWeight: "bold", 
        marginBottom: "1.5rem",
        color: "#1E293B"
      }}>
        Parlamentares com Mais Discursos
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {data.map((item, index) => (
          <DiscursoCard
            key={item.politico_id}
            position={index + 1}
            politico={item}
          />
        ))}
      </div>
    </div>
  )
}

function RankingEmpresas() {
  const { data, loading, error } = useRanking("/lucro_empresas", { limit: 50 })

  if (loading) return <LoadingState />
  if (error) return <ErrorState message={error} />

  return (
    <div>
      <h3 style={{ 
        fontSize: "1.5rem", 
        fontWeight: "bold", 
        marginBottom: "1.5rem",
        color: "#1E293B"
      }}>
        Empresas Mais Beneficiadas
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {data.map((empresa, index) => (
          <EmpresaCard
            key={empresa.cnpj || index}
            position={index + 1}
            empresa={empresa}
          />
        ))}
      </div>
    </div>
  )
}

// ========== COMPONENTES DE CARD ==========

function PodiumCard({ politico, position }: { politico: any, position: number }) {
  const medals = ["🥇", "🥈", "🥉"]
  const colors = ["#F59E0B", "#94A3B8", "#CD7F32"]

  return (
    <Link
      to={`/politicos/${politico.id}`}
      style={{
        textDecoration: "none",
        display: "block"
      }}
    >
      <div style={{
        backgroundColor: "white",
        border: `3px solid ${colors[position - 1]}`,
        borderRadius: "12px",
        padding: "1.5rem",
        textAlign: "center",
        transition: "transform 0.2s, box-shadow 0.2s",
        cursor: "pointer"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-4px)"
        e.currentTarget.style.boxShadow = "0 10px 25px rgba(0,0,0,0.1)"
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)"
        e.currentTarget.style.boxShadow = "none"
      }}
      >
        <div style={{ fontSize: "3rem", marginBottom: "0.5rem" }}>
          {medals[position - 1]}
        </div>
        
        {politico.foto && (
          <img
            src={politico.foto}
            alt={politico.nome}
            style={{
              width: "100px",
              height: "100px",
              borderRadius: "50%",
              objectFit: "cover",
              margin: "0 auto 1rem",
              border: "3px solid #E2E8F0"
            }}
          />
        )}

        <h3 style={{ 
          fontSize: "1.25rem", 
          fontWeight: "bold", 
          marginBottom: "0.5rem",
          color: "#1E293B"
        }}>
          {politico.nome}
        </h3>

        <div style={{ 
          fontSize: "0.9rem", 
          color: "#64748B",
          marginBottom: "1rem" 
        }}>
          {politico.partido} • {politico.uf}
        </div>

        <div style={{
          backgroundColor: colors[position - 1],
          color: "white",
          padding: "0.75rem",
          borderRadius: "8px",
          fontWeight: "bold",
          fontSize: "1.5rem"
        }}>
          {politico.score} pts
        </div>

        <div style={{
          marginTop: "1rem",
          display: "grid",
          gridTemplateColumns: "repeat(3, 1fr)",
          gap: "0.5rem",
          fontSize: "0.85rem"
        }}>
          <div>
            <div style={{ color: "#64748B" }}>Assiduidade</div>
            <div style={{ fontWeight: "bold", color: "#3B82F6" }}>
              {politico.notas.assiduidade}
            </div>
          </div>
          <div>
            <div style={{ color: "#64748B" }}>Economia</div>
            <div style={{ fontWeight: "bold", color: "#10B981" }}>
              {politico.notas.economia}
            </div>
          </div>
          <div>
            <div style={{ color: "#64748B" }}>Produção</div>
            <div style={{ fontWeight: "bold", color: "#8B5CF6" }}>
              {politico.notas.producao}
            </div>
          </div>
        </div>
      </div>
    </Link>
  )
}

function RankingCard({ position, politico, type }: { 
  position: number, 
  politico: any, 
  type: "performance" | "gastos" | "economia" 
}) {
  const getDisplayValue = () => {
    switch (type) {
      case "performance":
        return `${politico.score} pts`
      case "gastos":
      case "economia":
        return `R$ ${politico.total_gasto.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`
      default:
        return ""
    }
  }

  const getValueColor = () => {
    switch (type) {
      case "performance":
        return politico.score >= 70 ? "#10B981" : politico.score >= 50 ? "#F59E0B" : "#EF4444"
      case "gastos":
        return "#EF4444"
      case "economia":
        return "#10B981"
      default:
        return "#64748B"
    }
  }

  return (
    <Link
      to={`/politicos/${politico.id}`}
      style={{ textDecoration: "none" }}
    >
      <div style={{
        backgroundColor: "white",
        border: "2px solid #E2E8F0",
        borderRadius: "8px",
        padding: "1rem 1.5rem",
        display: "flex",
        alignItems: "center",
        gap: "1.5rem",
        transition: "all 0.2s",
        cursor: "pointer"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "#1E88E5"
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(30, 136, 229, 0.1)"
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "#E2E8F0"
        e.currentTarget.style.boxShadow = "none"
      }}
      >
        {/* POSIÇÃO */}
        <div style={{
          width: "50px",
          height: "50px",
          backgroundColor: position <= 3 ? "#FEF3C7" : "#F1F5F9",
          color: position <= 3 ? "#F59E0B" : "#64748B",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontWeight: "bold",
          fontSize: "1.25rem",
          flexShrink: 0
        }}>
          {position}
        </div>

        {/* FOTO (se disponível) */}
        {politico.foto && (
          <img
            src={politico.foto}
            alt={politico.nome}
            style={{
              width: "50px",
              height: "50px",
              borderRadius: "50%",
              objectFit: "cover",
              flexShrink: 0
            }}
          />
        )}

        {/* INFORMAÇÕES */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <h4 style={{ 
            fontSize: "1.1rem", 
            fontWeight: "600", 
            marginBottom: "0.25rem",
            color: "#1E293B",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap"
          }}>
            {politico.nome}
          </h4>
          {politico.partido && politico.uf && (
            <p style={{ 
              fontSize: "0.9rem", 
              color: "#64748B",
              margin: 0
            }}>
              {politico.partido} • {politico.uf}
            </p>
          )}
        </div>

        {/* VALOR */}
        <div style={{
          textAlign: "right",
          flexShrink: 0
        }}>
          <div style={{
            fontSize: "1.5rem",
            fontWeight: "bold",
            color: getValueColor()
          }}>
            {getDisplayValue()}
          </div>
        </div>
      </div>
    </Link>
  )
}

function DiscursoCard({ position, politico }: { position: number, politico: any }) {
  return (
    <Link
      to={`/politicos/${politico.politico_id}`}
      style={{ textDecoration: "none" }}
    >
      <div style={{
        backgroundColor: "white",
        border: "2px solid #E2E8F0",
        borderRadius: "8px",
        padding: "1.5rem",
        transition: "all 0.2s",
        cursor: "pointer"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "#1E88E5"
        e.currentTarget.style.boxShadow = "0 4px 12px rgba(30, 136, 229, 0.1)"
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "#E2E8F0"
        e.currentTarget.style.boxShadow = "none"
      }}
      >
        <div style={{ display: "flex", alignItems: "start", gap: "1.5rem" }}>
          {/* POSIÇÃO */}
          <div style={{
            width: "50px",
            height: "50px",
            backgroundColor: position <= 3 ? "#FEF3C7" : "#F1F5F9",
            color: position <= 3 ? "#F59E0B" : "#64748B",
            borderRadius: "50%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: "bold",
            fontSize: "1.25rem",
            flexShrink: 0
          }}>
            {position}
          </div>

          <div style={{ flex: 1 }}>
            {/* NOME E INFO */}
            <div style={{ marginBottom: "1rem" }}>
              <h4 style={{ 
                fontSize: "1.1rem", 
                fontWeight: "600", 
                marginBottom: "0.25rem",
                color: "#1E293B"
              }}>
                {politico.nome_politico}
              </h4>
              <p style={{ 
                fontSize: "0.9rem", 
                color: "#64748B",
                margin: 0
              }}>
                {politico.sigla_partido} • {politico.sigla_uf}
              </p>
            </div>

            {/* TOTAL DE DISCURSOS */}
            <div style={{
              display: "inline-block",
              backgroundColor: "#DBEAFE",
              color: "#1E40AF",
              padding: "0.5rem 1rem",
              borderRadius: "6px",
              fontWeight: "600",
              marginBottom: "1rem"
            }}>
              <FileText size={16} style={{ display: "inline", marginRight: "0.5rem" }} />
              {politico.total_discursos} discursos
            </div>

            {/* TEMAS MAIS DISCUTIDOS */}
            {politico.temas_mais_discutidos && politico.temas_mais_discutidos.length > 0 && (
              <div>
                <p style={{ 
                  fontSize: "0.85rem", 
                  color: "#64748B", 
                  marginBottom: "0.5rem",
                  fontWeight: 500
                }}>
                  Principais temas:
                </p>
                <div style={{ 
                  display: "flex", 
                  flexWrap: "wrap", 
                  gap: "0.5rem" 
                }}>
                  {politico.temas_mais_discutidos.slice(0, 5).map((tema: any, idx: number) => (
                    <span
                      key={idx}
                      style={{
                        backgroundColor: "#F1F5F9",
                        color: "#475569",
                        padding: "0.25rem 0.75rem",
                        borderRadius: "12px",
                        fontSize: "0.8rem",
                        fontWeight: 500
                      }}
                    >
                      {tema.keyword} ({tema.frequencia})
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

function EmpresaCard({ position, empresa }: { position: number, empresa: any }) {
  return (
    <div style={{
      backgroundColor: "white",
      border: "2px solid #E2E8F0",
      borderRadius: "8px",
      padding: "1rem 1.5rem",
      display: "flex",
      alignItems: "center",
      gap: "1.5rem"
    }}>
      {/* POSIÇÃO */}
      <div style={{
        width: "50px",
        height: "50px",
        backgroundColor: position <= 3 ? "#FEF3C7" : "#F1F5F9",
        color: position <= 3 ? "#F59E0B" : "#64748B",
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: "bold",
        fontSize: "1.25rem",
        flexShrink: 0
      }}>
        {position}
      </div>

      {/* ÍCONE EMPRESA */}
      <div style={{
        width: "50px",
        height: "50px",
        backgroundColor: "#DBEAFE",
        borderRadius: "50%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0
      }}>
        <Building2 size={24} color="#1E40AF" />
      </div>

      {/* INFORMAÇÕES */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <h4 style={{ 
          fontSize: "1.1rem", 
          fontWeight: "600", 
          marginBottom: "0.25rem",
          color: "#1E293B",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap"
        }}>
          {empresa.nome_fornecedor}
        </h4>
        {empresa.cnpj && (
          <p style={{ 
            fontSize: "0.85rem", 
            color: "#64748B",
            margin: 0,
            fontFamily: "monospace"
          }}>
            CNPJ: {empresa.cnpj}
          </p>
        )}
      </div>

      {/* VALOR */}
      <div style={{
        textAlign: "right",
        flexShrink: 0
      }}>
        <div style={{
          fontSize: "1.5rem",
          fontWeight: "bold",
          color: "#10B981"
        }}>
          R$ {empresa.total_recebido.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
        </div>
      </div>
    </div>
  )
}

// ========== COMPONENTES AUXILIARES ==========

function TabButton({ active, onClick, icon, label }: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
}) {
  return (
    <button
      onClick={onClick}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "0.5rem",
        padding: "0.75rem 1.5rem",
        border: "none",
        backgroundColor: active ? "#1E88E5" : "transparent",
        color: active ? "white" : "#64748B",
        borderRadius: "8px 8px 0 0",
        cursor: "pointer",
        fontWeight: active ? "600" : "500",
        fontSize: "0.95rem",
        transition: "all 0.2s",
        whiteSpace: "nowrap"
      }}
      onMouseEnter={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "#F1F5F9"
        }
      }}
      onMouseLeave={(e) => {
        if (!active) {
          e.currentTarget.style.backgroundColor = "transparent"
        }
      }}
    >
      {icon}
      {label}
    </button>
  )
}

function LoadingState() {
  return (
    <div style={{
      textAlign: "center",
      padding: "4rem 2rem",
      color: "#64748B"
    }}>
      <div style={{
        width: "50px",
        height: "50px",
        border: "4px solid #E2E8F0",
        borderTop: "4px solid #1E88E5",
        borderRadius: "50%",
        margin: "0 auto 1rem",
        animation: "spin 1s linear infinite"
      }} />
      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
      <p>Carregando rankings...</p>
    </div>
  )
}

function ErrorState({ message }: { message: string }) {
  return (
    <div style={{
      textAlign: "center",
      padding: "4rem 2rem",
      backgroundColor: "#FEE2E2",
      borderRadius: "8px",
      color: "#991B1B"
    }}>
      <p style={{ fontSize: "1.1rem", fontWeight: "600", marginBottom: "0.5rem" }}>
        Erro ao carregar dados
      </p>
      <p style={{ fontSize: "0.9rem" }}>{message}</p>
    </div>
  )
}
