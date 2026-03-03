import {
  AlertCircle,
  Database,
  TrendingUp,
  DollarSign,
  FileText,
  Users,
  ChevronDown,
} from "lucide-react"
import { useState } from "react"
import { Link } from "react-router-dom"
import Header from "../components/Header"

// ─────────────────────────────────────────────────────────────────────────────
// Acordeão reutilizável (mesmo padrão do FAQ)
// ─────────────────────────────────────────────────────────────────────────────

function Acordeao({
  title,
  icon,
  children,
  defaultOpen = false,
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
  defaultOpen?: boolean
}) {
  const [open, setOpen] = useState(defaultOpen)

  return (
    <div
      className={`bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden transition-colors ${
        open ? "bg-slate-50/50" : ""
      }`}
    >
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between gap-4 px-6 py-5 text-left hover:bg-slate-50 transition-colors cursor-pointer border-0 bg-transparent"
      >
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-slate-50 border border-slate-100 flex items-center justify-center flex-shrink-0">
            {icon}
          </div>
          <span
            style={{ fontFamily: "'Fraunces', serif" }}
            className="text-base font-bold text-slate-800"
          >
            {title}
          </span>
        </div>
        <ChevronDown
          size={16}
          className={`text-slate-400 flex-shrink-0 transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {open && (
        <div className="px-6 pb-6 border-t border-slate-100 pt-5 text-sm text-slate-600 leading-relaxed space-y-4">
          {children}
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Blocos visuais internos
// ─────────────────────────────────────────────────────────────────────────────

function FormulaBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 font-mono text-sm overflow-x-auto">
      {children}
    </div>
  )
}

function ExampleBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm leading-relaxed">
      {children}
    </div>
  )
}

function WeightCards() {
  const weights = [
    { label: "Assiduidade", weight: "15%", color: "bg-blue-50 border-blue-200 text-blue-600" },
    { label: "Economia",    weight: "40%", color: "bg-emerald-50 border-emerald-200 text-emerald-600" },
    { label: "Produção",    weight: "45%", color: "bg-purple-50 border-purple-200 text-purple-600" },
  ]

  return (
    <div className="grid grid-cols-3 gap-3 mt-2">
      {weights.map((w) => (
        <div key={w.label} className={`rounded-xl border-2 p-4 text-center ${w.color}`}>
          <div className="text-2xl font-bold mb-1">{w.weight}</div>
          <div className="text-xs font-medium opacity-75">{w.label}</div>
        </div>
      ))}
    </div>
  )
}

function ScoreTable() {
  const rows = [
    { relevancia: "Alta",  tipos: "PEC, PL, PLC, PLP",  principal: "1.0 pt",  coautor: "0.2 pt",  cor: "text-emerald-600" },
    { relevancia: "Média", tipos: "PDC, PRC, MPV",        principal: "0.5 pt",  coautor: "0.1 pt",  cor: "text-amber-600" },
    { relevancia: "Baixa", tipos: "Outros tipos",          principal: "0.05 pt", coautor: "0.01 pt", cor: "text-slate-500" },
  ]

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200">
            <th className="text-left text-[11px] text-slate-400 font-semibold uppercase tracking-wide px-4 py-3">Relevância</th>
            <th className="text-left text-[11px] text-slate-400 font-semibold uppercase tracking-wide px-4 py-3">Tipos</th>
            <th className="text-left text-[11px] text-slate-400 font-semibold uppercase tracking-wide px-4 py-3">Autor Principal</th>
            <th className="text-left text-[11px] text-slate-400 font-semibold uppercase tracking-wide px-4 py-3">Coautor</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.relevancia} className="border-b border-slate-100 last:border-0">
              <td className={`px-4 py-3 font-semibold ${r.cor}`}>{r.relevancia}</td>
              <td className="px-4 py-3 text-slate-600 font-mono text-xs">{r.tipos}</td>
              <td className={`px-4 py-3 font-bold ${r.cor}`}>{r.principal}</td>
              <td className="px-4 py-3 text-slate-400">{r.coautor}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function ClassificacaoCards() {
  const items = [
    { label: "Excelente", range: "80 – 100 pts", color: "bg-emerald-50 border-emerald-200 text-emerald-700" },
    { label: "Bom",       range: "60 – 79 pts",  color: "bg-blue-50 border-blue-200 text-blue-700" },
    { label: "Regular",   range: "40 – 59 pts",  color: "bg-amber-50 border-amber-200 text-amber-700" },
    { label: "Crítico",   range: "0 – 39 pts",   color: "bg-red-50 border-red-200 text-red-600" },
  ]

  return (
    <div className="grid gap-2">
      {items.map((i) => (
        <div
          key={i.label}
          className={`flex items-center justify-between border-2 rounded-xl px-5 py-3 ${i.color}`}
        >
          <span className="font-semibold text-sm">{i.label}</span>
          <span className="text-sm font-medium">{i.range}</span>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página
// ─────────────────────────────────────────────────────────────────────────────

export default function Metodologia() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50 pt-16">

        {/* ── Header da página ── */}
        <div className="bg-white border-b border-slate-200">
          <div className="max-w-4xl mx-auto px-6 py-12">
            <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
              Institucional
            </p>
            <h1
              style={{ fontFamily: "'Fraunces', serif" }}
              className="text-4xl font-bold text-slate-900 mb-4 leading-tight"
            >
              Metodologia de Cálculo
            </h1>
            <p className="text-base text-slate-500 leading-relaxed max-w-2xl">
              Entenda como calculamos o score de performance parlamentar com base em três pilares:{" "}
              <strong className="text-slate-700">assiduidade</strong>,{" "}
              <strong className="text-slate-700">economia</strong> e{" "}
              <strong className="text-slate-700">produção legislativa</strong>.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-10 space-y-4">

          {/* ── Score Final ── */}
          <Acordeao
            title="Score Final de Performance"
            icon={<TrendingUp size={18} className="text-emerald-600" />}
            defaultOpen
          >
            <p>
              O score final é uma <strong>média ponderada</strong> de três critérios, variando de 0 a
              100 pontos:
            </p>
            <FormulaBox>
              Score Final = (Assiduidade × 0,15) + (Economia × 0,40) + (Produção × 0,45)
            </FormulaBox>
            <WeightCards />
          </Acordeao>

          {/* ── Fontes de Dados ── */}
          <Acordeao
            title="Fontes de Dados"
            icon={<Database size={18} className="text-blue-600" />}
          >
            <p>Todos os dados utilizados são provenientes de fontes públicas e oficiais:</p>
            <ul className="space-y-2 mt-1">
              <li className="flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">•</span>
                <span>
                  <strong>API Pública da Câmara dos Deputados:</strong>{" "}
                  <a
                    href="https://dadosabertos.camara.leg.br/swagger/api.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    dadosabertos.camara.leg.br
                  </a>
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400 mt-0.5">•</span>
                <span>
                  <strong>Webservice de Dados Abertos Legislativos:</strong>{" "}
                  <a
                    href="https://www2.camara.leg.br/transparencia/dados-abertos/dados-abertos-legislativo/webservices/proposicoes-1"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    Proposições e Autoria
                  </a>
                </span>
              </li>
            </ul>
          </Acordeao>

          {/* ── Assiduidade ── */}
          <Acordeao
            title="1. Assiduidade — Peso: 15%"
            icon={<Users size={18} className="text-blue-500" />}
          >
            <p>
              Mede a presença do parlamentar nas sessões de votação da Câmara. Uma alta taxa de
              presença indica comprometimento com as atividades legislativas.
            </p>
            <FormulaBox>
              Nota Assiduidade = (Presenças ÷ Total de Sessões) × 100
            </FormulaBox>
            <ExampleBox>
              <strong>Exemplo:</strong> Parlamentar presente em 150 de 177 sessões
              <br />
              (150 ÷ 177) × 100 = <strong>84,75 pontos</strong>
            </ExampleBox>
          </Acordeao>

          {/* ── Economia ── */}
          <Acordeao
            title="2. Economia — Peso: 40%"
            icon={<DollarSign size={18} className="text-emerald-500" />}
          >
            <p>
              Avalia o uso responsável da cota parlamentar (CEAP). Cada estado possui um limite
              mensal diferente, calculado com base na distância de Brasília e custo de vida.
            </p>
            <FormulaBox>
              <div className="space-y-1">
                <div>Cota Total do Período = Cota Mensal × Meses de Mandato</div>
                <div>Economia = (Cota Total − Gasto Total) ÷ Cota Total</div>
                <div>Nota Economia = Economia × 100</div>
              </div>
            </FormulaBox>
            <ExampleBox>
              <strong>Exemplo (Amapá — R$ 40.000/mês):</strong>
              <br />
              Mandato de 12 meses, gastou R$ 489.064,11
              <br />
              Cota total: R$ 40.000 × 12 = R$ 480.000
              <br />
              Neste caso: gastou mais que a cota → <strong>Nota = 0 pontos</strong>
              <br />
              <span className="text-slate-500 text-xs">
                * Se o gasto for menor que a cota, a nota aumenta proporcionalmente.
              </span>
            </ExampleBox>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-500">
              💡 As cotas variam por UF — estados mais distantes possuem cotas maiores para cobrir
              deslocamentos.
            </div>
          </Acordeao>

          {/* ── Produção Legislativa ── */}
          <Acordeao
            title="3. Produção Legislativa — Peso: 45%"
            icon={<FileText size={18} className="text-purple-500" />}
          >
            <p>
              Avalia a quantidade e relevância das proposições legislativas apresentadas. Diferentes
              tipos recebem pontuações distintas, e ser <strong>autor principal</strong> vale mais do
              que coautor.
            </p>
            <ScoreTable />
            <FormulaBox>
              <div className="space-y-1">
                <div>Meta de Produção = Meses de Mandato × 2 proposições/mês</div>
                <div>Nota Produção = min((Total Ponderado ÷ Meta) × 100, 100)</div>
              </div>
            </FormulaBox>
            <ExampleBox>
              <strong>Exemplo:</strong> Mandato de 12 meses
              <br />
              3 PLs como autor principal = 3,0 pts · 2 PECs como coautor = 0,4 pts · 5 PDCs como
              autor = 2,5 pts
              <br />
              <strong>Total: 5,9 pts ≈ 6 proposições</strong>
              <br />
              Meta: 12 × 2 = 24 · Nota: (6 ÷ 24) × 100 = <strong>25 pontos</strong>
            </ExampleBox>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs text-slate-500 leading-relaxed">
              📌 <strong>Siglas:</strong> PEC = Proposta de Emenda Constitucional · PL = Projeto de
              Lei · PLC = Projeto de Lei Complementar · PLP = Projeto de Lei do Plano Plurianual ·
              PDC = Projeto de Decreto Legislativo · PRC = Projeto de Resolução · MPV = Medida
              Provisória
            </div>
          </Acordeao>

          {/* ── Classificação ── */}
          <Acordeao
            title="Classificação do Score"
            icon={<TrendingUp size={18} className="text-amber-500" />}
          >
            <p>Com base no score final, os parlamentares são classificados em quatro faixas:</p>
            <ClassificacaoCards />
          </Acordeao>

          {/* ── Limitações ── */}
          <Acordeao
            title="Limitações e Considerações"
            icon={<AlertCircle size={18} className="text-slate-400" />}
          >
            <ul className="space-y-3">
              {[
                {
                  titulo: "Dados em desenvolvimento",
                  texto:
                    "O banco de dados ainda está sendo ajustado e pode apresentar inconsistências.",
                },
                {
                  titulo: "Contexto político",
                  texto:
                    "O score não captura nuances como qualidade das proposições, impacto social ou contexto de ausências justificadas.",
                },
                {
                  titulo: "Atualização periódica",
                  texto:
                    "Os dados são atualizados conforme a disponibilidade da API da Câmara.",
                },
                {
                  titulo: "Uso educacional",
                  texto:
                    "Esta ferramenta tem fins educacionais e de transparência, não substituindo análises políticas profundas.",
                },
              ].map((item) => (
                <li key={item.titulo} className="flex items-start gap-2.5">
                  <span className="text-slate-300 mt-0.5 flex-shrink-0">•</span>
                  <span>
                    <strong className="text-slate-700">{item.titulo}:</strong> {item.texto}
                  </span>
                </li>
              ))}
            </ul>
          </Acordeao>

          {/* ── CTA final ── */}
          <div className="bg-blue-50 border border-blue-100 rounded-2xl p-7 flex flex-col sm:flex-row items-center gap-5">
            <div className="flex-1">
              <p className="text-sm font-semibold text-slate-800 mb-1">Ficou com dúvidas?</p>
              <p className="text-sm text-slate-500 leading-relaxed">
                Consulte as perguntas frequentes ou veja o código-fonte da metodologia no GitHub.
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
              <Link
                to="/faq"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-white border border-slate-200 text-slate-700 text-xs font-medium rounded-xl no-underline hover:border-slate-300 transition-colors"
              >
                Ver FAQ
              </Link>
              <a
                href="https://github.com/WrongProvider/quemVota"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium rounded-xl no-underline transition-colors"
              >
                GitHub
              </a>
            </div>
          </div>

        </div>

        {/* ── Rodapé ── */}
        <div className="border-t border-slate-200 bg-white py-6 text-center mt-6">
          <p className="text-xs text-slate-400">
            Dados públicos da{" "}
            <a
              href="https://dadosabertos.camara.leg.br"
              target="_blank"
              rel="noreferrer"
              className="text-slate-500 hover:text-blue-600 transition-colors"
            >
              Câmara dos Deputados
            </a>{" "}
            · quemvota.com.br
          </p>
        </div>
      </div>
    </>
  )
}