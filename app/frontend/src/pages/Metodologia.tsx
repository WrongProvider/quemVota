import { AlertCircle, Database, TrendingUp, DollarSign, FileText, Users } from "lucide-react"
import Header from "../components/Header"

export default function Metodologia() {
  return (
    <>
      <Header /> 
      <div style={{ 
        maxWidth: "900px", 
        margin: "0 auto", 
        padding: "3rem 2rem",
        fontFamily: "system-ui, -apple-system, sans-serif"
      }}>
        {/* AVISO IMPORTANTE */}
        <div style={{
          backgroundColor: "#FEF3C7",
          border: "2px solid #F59E0B",
          borderRadius: "12px",
          padding: "1.5rem",
          marginBottom: "3rem",
          display: "flex",
          gap: "1rem",
          alignItems: "flex-start"
        }}>
          <AlertCircle size={24} color="#F59E0B" style={{ flexShrink: 0, marginTop: "2px" }} />
          <div>
            <h3 style={{ margin: 0, marginBottom: "0.5rem", color: "#92400E", fontSize: "1.1rem" }}>
              ⚠️ Projeto em Desenvolvimento
            </h3>
            <p style={{ margin: 0, color: "#78350F", lineHeight: "1.6" }}>
              Este projeto está em fase de desenvolvimento e o banco de dados ainda não foi totalmente ajustado 
              para replicar fielmente os dados da Câmara dos Deputados. <strong>Os dados e scores apresentados 
              podem não estar corretos</strong> e não devem ser interpretados como informação oficial ou definitiva. 
              Use apenas para fins educacionais e de demonstração.
            </p>
          </div>
        </div>

        {/* HEADER */}
        <div style={{ marginBottom: "3rem" }}>
          <h1 style={{ 
            fontSize: "2.5rem", 
            fontWeight: "bold", 
            marginBottom: "1rem",
            color: "#1E293B" 
          }}>
            📊 Metodologia de Cálculo
          </h1>
          <p style={{ 
            fontSize: "1.1rem", 
            color: "#64748B", 
            lineHeight: "1.8" 
          }}>
            Entenda como calculamos o score de performance parlamentar com base em três pilares principais: 
            assiduidade, economia e produção legislativa.
          </p>
        </div>

        {/* FONTES DE DADOS */}
        <Section 
          icon={<Database size={24} color="#1E88E5" />}
          title="Fontes de Dados"
        >
          <p style={{ marginBottom: "1rem" }}>
            Todos os dados utilizados são provenientes de fontes públicas e oficiais:
          </p>
          <ul style={{ lineHeight: "1.8", color: "#475569" }}>
            <li>
              <strong>API Pública da Câmara dos Deputados:</strong>{" "}
              <a 
                href="https://dadosabertos.camara.leg.br/swagger/api.html" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: "#1E88E5", textDecoration: "none" }}
              >
                dadosabertos.camara.leg.br
              </a>
            </li>
            <li>
              <strong>Webservice de Dados Abertos Legislativos:</strong>{" "}
              <a 
                href="https://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo/webservices/proposicoes-1" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{ color: "#1E88E5", textDecoration: "none" }}
              >
                Proposições e Autoria
              </a>
            </li>
          </ul>
        </Section>

        {/* SCORE FINAL */}
        <Section 
          icon={<TrendingUp size={24} color="#10B981" />}
          title="Score Final de Performance"
        >
          <p style={{ marginBottom: "1.5rem" }}>
            O score final é calculado através de uma <strong>média ponderada</strong> de três critérios, 
            variando de 0 a 100 pontos:
          </p>

          <FormulaBox>
            <code style={{ fontSize: "1.1rem" }}>
              Score Final = (Assiduidade × 0.15) + (Economia × 0.40) + (Produção × 0.45)
            </code>
          </FormulaBox>

          <div style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(3, 1fr)", 
            gap: "1rem",
            marginTop: "1.5rem" 
          }}>
            <WeightCard label="Assiduidade" weight="15%" color="#3B82F6" />
            <WeightCard label="Economia" weight="40%" color="#10B981" />
            <WeightCard label="Produção" weight="45%" color="#8B5CF6" />
          </div>
        </Section>

        {/* CRITÉRIO 1: ASSIDUIDADE */}
        <Section 
          icon={<Users size={24} color="#3B82F6" />}
          title="1. Assiduidade (Peso: 15%)"
        >
          <p style={{ marginBottom: "1rem" }}>
            Mede a presença do parlamentar nas sessões de votação da Câmara. 
            Uma alta taxa de presença indica comprometimento com as atividades legislativas.
          </p>

          <FormulaBox>
            <code>Nota Assiduidade = (Presenças ÷ Total de Sessões) × 100</code>
          </FormulaBox>

          <ExampleBox>
            <strong>Exemplo:</strong><br />
            Parlamentar presente em 150 de 177 sessões:<br />
            <code>(150 ÷ 177) × 100 = 84,75 pontos</code>
          </ExampleBox>
        </Section>

        {/* CRITÉRIO 2: ECONOMIA */}
        <Section 
          icon={<DollarSign size={24} color="#10B981" />}
          title="2. Economia (Peso: 40%)"
        >
          <p style={{ marginBottom: "1rem" }}>
            Avalia o uso responsável da cota parlamentar (CEAP - Cota para Exercício da Atividade Parlamentar). 
            Cada estado possui um limite mensal diferente.
          </p>

          <FormulaBox>
            <div style={{ marginBottom: "0.5rem" }}>
              <code>Cota Total do Período = Cota Mensal × Meses de Mandato</code>
            </div>
            <div style={{ marginBottom: "0.5rem" }}>
              <code>Economia = (Cota Total - Gasto Total) ÷ Cota Total</code>
            </div>
            <div>
              <code>Nota Economia = Economia × 100</code>
            </div>
          </FormulaBox>

          <ExampleBox>
            <strong>Exemplo (Amapá - R$ 40.000/mês):</strong><br />
            Mandato de 12 meses, gastou R$ 489.064,11<br />
            Cota total: <code>R$ 40.000 × 12 = R$ 480.000</code><br />
            Neste caso: gastou mais que a cota → <code>Nota = 0 pontos</code><br /><br />
            <em style={{ color: "#64748B" }}>
              * Se o gasto for menor que a cota, a nota aumenta proporcionalmente
            </em>
          </ExampleBox>

          <div style={{
            marginTop: "1.5rem",
            padding: "1rem",
            backgroundColor: "#F1F5F9",
            borderRadius: "8px"
          }}>
            <p style={{ margin: 0, fontSize: "0.95rem", color: "#475569" }}>
              💡 <strong>Nota:</strong> As cotas variam por UF devido a diferenças de distância de Brasília 
              e custo de vida. Estados mais distantes possuem cotas maiores para cobrir deslocamentos.
            </p>
          </div>
        </Section>

        {/* CRITÉRIO 3: PRODUÇÃO */}
        <Section 
          icon={<FileText size={24} color="#8B5CF6" />}
          title="3. Produção Legislativa (Peso: 45%)"
        >
          <p style={{ marginBottom: "1rem" }}>
            Avalia a quantidade e relevância das proposições legislativas apresentadas pelo parlamentar. 
            Diferentes tipos de proposição recebem pontuações diferentes, e ser <strong>autor principal</strong> vale mais.
          </p>

          <div style={{ marginBottom: "1.5rem" }}>
            <h4 style={{ marginBottom: "0.75rem", color: "#1E293B" }}>
              Sistema de Pontuação por Tipo de Proposição:
            </h4>
            
            <ScoreTable>
              <thead>
                <tr>
                  <th>Tipo</th>
                  <th>Descrição</th>
                  <th>Autor Principal</th>
                  <th>Coautor</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Alta Relevância</strong></td>
                  <td>PEC, PL, PLC, PLP</td>
                  <td style={{ color: "#10B981", fontWeight: "bold" }}>1.0 ponto</td>
                  <td style={{ color: "#64748B" }}>0.2 pontos</td>
                </tr>
                <tr>
                  <td><strong>Média Relevância</strong></td>
                  <td>PDC, PRC, MPV</td>
                  <td style={{ color: "#F59E0B", fontWeight: "bold" }}>0.5 pontos</td>
                  <td style={{ color: "#64748B" }}>0.1 pontos</td>
                </tr>
                <tr>
                  <td><strong>Baixa Relevância</strong></td>
                  <td>Outros tipos</td>
                  <td style={{ color: "#6B7280", fontWeight: "bold" }}>0.05 pontos</td>
                  <td style={{ color: "#9CA3AF" }}>0.01 pontos</td>
                </tr>
              </tbody>
            </ScoreTable>
          </div>

          <FormulaBox>
            <div style={{ marginBottom: "0.5rem" }}>
              <code>Meta de Produção = Meses de Mandato × 2 proposições/mês</code>
            </div>
            <div>
              <code>Nota Produção = min((Total de Proposições ÷ Meta) × 100, 100)</code>
            </div>
          </FormulaBox>

          <ExampleBox>
            <strong>Exemplo:</strong><br />
            Mandato de 12 meses, apresentou:<br />
            • 3 PLs como autor principal = 3.0 pontos<br />
            • 2 PECs como coautor = 0.4 pontos<br />
            • 5 PDCs como autor = 2.5 pontos<br />
            <strong>Total:</strong> 5.9 pontos (≈ 6 proposições)<br /><br />
            Meta: <code>12 × 2 = 24 proposições</code><br />
            Nota: <code>(6 ÷ 24) × 100 = 25 pontos</code>
          </ExampleBox>

          <div style={{
            marginTop: "1.5rem",
            padding: "1rem",
            backgroundColor: "#F1F5F9",
            borderRadius: "8px"
          }}>
            <p style={{ margin: 0, fontSize: "0.95rem", color: "#475569" }}>
              📌 <strong>Legenda dos tipos:</strong><br />
              <strong>PEC</strong> = Proposta de Emenda Constitucional | 
              <strong> PL</strong> = Projeto de Lei | 
              <strong> PLC</strong> = Projeto de Lei Complementar | 
              <strong> PLP</strong> = Projeto de Lei do Plano Plurianual |
              <strong> PDC</strong> = Projeto de Decreto Legislativo | 
              <strong> PRC</strong> = Projeto de Resolução | 
              <strong> MPV</strong> = Medida Provisória
            </p>
          </div>
        </Section>

        {/* CLASSIFICAÇÃO */}
        <Section 
          icon={<TrendingUp size={24} color="#F59E0B" />}
          title="Classificação do Score"
        >
          <p style={{ marginBottom: "1.5rem" }}>
            Com base no score final, os parlamentares são classificados em:
          </p>

          <div style={{ display: "grid", gap: "1rem" }}>
            <ClassificationCard 
              label="Excelente" 
              range="80 - 100" 
              color="#10B981" 
              bgColor="#D1FAE5"
            />
            <ClassificationCard 
              label="Bom" 
              range="60 - 79" 
              color="#3B82F6" 
              bgColor="#DBEAFE"
            />
            <ClassificationCard 
              label="Regular" 
              range="40 - 59" 
              color="#F59E0B" 
              bgColor="#FEF3C7"
            />
            <ClassificationCard 
              label="Crítico" 
              range="0 - 39" 
              color="#EF4444" 
              bgColor="#FEE2E2"
            />
          </div>
        </Section>

        {/* LIMITAÇÕES */}
        <Section 
          icon={<AlertCircle size={24} color="#64748B" />}
          title="Limitações e Considerações"
        >
          <ul style={{ lineHeight: "1.8", color: "#475569" }}>
            <li>
              <strong>Dados em desenvolvimento:</strong> O banco de dados ainda está sendo ajustado 
              e pode apresentar inconsistências.
            </li>
            <li>
              <strong>Contexto político:</strong> O score não captura nuances como qualidade das proposições, 
              impacto social ou contexto político de ausências justificadas.
            </li>
            <li>
              <strong>Atualização:</strong> Os dados são atualizados periodicamente conforme disponibilidade 
              da API da Câmara.
            </li>
            <li>
              <strong>Uso educacional:</strong> Esta ferramenta tem fins educacionais e de transparência, 
              não substituindo análises políticas profundas.
            </li>
          </ul>
        </Section>

        {/* RODAPÉ */}
        <div style={{
          marginTop: "4rem",
          paddingTop: "2rem",
          borderTop: "2px solid #E2E8F0",
          textAlign: "center",
          color: "#64748B"
        }}>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>
            Dúvidas ou sugestões? Entre em contato através do nosso repositório no GitHub.
          </p>
        </div>
      </div>
    </>
  )
}

// ========== COMPONENTES AUXILIARES ==========

function Section({ icon, title, children }: { icon: React.ReactNode, title: string, children: React.ReactNode }) {
  return (
    <section style={{ marginBottom: "3rem" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.5rem" }}>
        {icon}
        <h2 style={{ fontSize: "1.75rem", fontWeight: "bold", margin: 0, color: "#1E293B" }}>
          {title}
        </h2>
      </div>
      <div style={{ fontSize: "1rem", lineHeight: "1.8", color: "#475569" }}>
        {children}
      </div>
    </section>
  )
}

function FormulaBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      backgroundColor: "#F8FAFC",
      border: "2px solid #E2E8F0",
      borderRadius: "8px",
      padding: "1.25rem",
      fontFamily: "monospace",
      fontSize: "0.95rem",
      overflowX: "auto",
      marginBottom: "1rem"
    }}>
      {children}
    </div>
  )
}

function ExampleBox({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      backgroundColor: "#EFF6FF",
      border: "2px solid #BFDBFE",
      borderRadius: "8px",
      padding: "1rem",
      marginTop: "1rem",
      fontSize: "0.95rem",
      lineHeight: "1.6"
    }}>
      {children}
    </div>
  )
}

function WeightCard({ label, weight, color }: { label: string, weight: string, color: string }) {
  return (
    <div style={{
      backgroundColor: "#F8FAFC",
      border: `3px solid ${color}`,
      borderRadius: "8px",
      padding: "1rem",
      textAlign: "center"
    }}>
      <div style={{ fontSize: "2rem", fontWeight: "bold", color, marginBottom: "0.25rem" }}>
        {weight}
      </div>
      <div style={{ fontSize: "0.9rem", color: "#64748B", fontWeight: 500 }}>
        {label}
      </div>
    </div>
  )
}

function ScoreTable({ children }: { children: React.ReactNode }) {
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{
        width: "100%",
        borderCollapse: "collapse",
        fontSize: "0.95rem"
      }}>
        <style>{`
          table th {
            backgroundColor: #F1F5F9;
            padding: 0.75rem;
            textAlign: left;
            fontWeight: 600;
            color: #1E293B;
            borderBottom: 2px solid #E2E8F0;
          }
          table td {
            padding: 0.75rem;
            borderBottom: 1px solid #E2E8F0;
          }
          table tr:last-child td {
            borderBottom: none;
          }
        `}</style>
        {children}
      </table>
    </div>
  )
}

function ClassificationCard({ label, range, color, bgColor }: { 
  label: string, 
  range: string, 
  color: string, 
  bgColor: string 
}) {
  return (
    <div style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      backgroundColor: bgColor,
      border: `2px solid ${color}`,
      borderRadius: "8px",
      padding: "1rem 1.5rem"
    }}>
      <span style={{ fontSize: "1.1rem", fontWeight: "600", color }}>
        {label}
      </span>
      <span style={{ fontSize: "1rem", fontWeight: "500", color }}>
        {range} pontos
      </span>
    </div>
  )
}
