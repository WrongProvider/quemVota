import {
  Database,
  Users,
  DollarSign,
  FileText,
  ChevronDown,
  Scale,
  Sparkles,
} from "lucide-react"
import { useState } from "react"
import Header from "../components/Header"
import { useSeo } from "../hooks/useSeo"

// ─────────────────────────────────────────────────────────────────────────────
// Acordeão reutilizável
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

function HighlightBox({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 text-sm leading-relaxed text-blue-950">
      {children}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página Metodologia
// ─────────────────────────────────────────────────────────────────────────────

export default function Metodologia() {
  useSeo({
    title: "Metodologia e Neutralidade Factual | quemvota",
    description:
      "Conheça os princípios de neutralidade descritiva, agregação de dados abertos oficiais da Câmara dos Deputados e classificação temática do QuemVota.",
    url: "https://www.quemvota.com.br/metodologia",
    keywords: "metodologia, neutralidade factual, dados abertos, câmara dos deputados, transparencia publica, quemvota",
  })

  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50 pt-16">

        {/* ── Header da página ── */}
        <div className="bg-white border-b border-slate-200">
          <div className="max-w-4xl mx-auto px-6 py-12">
            <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
              Institucional & Princípios
            </p>
            <h1
              style={{ fontFamily: "'Fraunces', serif" }}
              className="text-4xl font-bold text-slate-900 mb-4 leading-tight"
            >
              Metodologia e Neutralidade Factual
            </h1>
            <p className="text-base text-slate-500 leading-relaxed max-w-2xl">
              O <strong className="text-slate-700">QuemVota</strong> é uma plataforma de transparência pública baseada
              no princípio da <strong className="text-slate-700">neutralidade descritiva</strong>: apresentamos exclusivamente
              fatos observáveis e auditáveis, sem atribuir notas, rótulos ou juízos morais de valor aos parlamentares.
            </p>
          </div>
        </div>

        <div className="max-w-4xl mx-auto px-6 py-10 space-y-4">

          {/* ── 1. Princípio da Neutralidade Factual Absoluta ── */}
          <Acordeao
            title="1. Por que não atribuímos scores ou notas aos políticos?"
            icon={<Scale size={18} className="text-blue-600" />}
            defaultOpen
          >
            <p>
              Muitas plataformas criam fórmulas com pesos arbitrários para eleger os "melhores" ou "piores" deputados.
              No QuemVota, entendemos que <strong>qualquer índice unificado embute premissas ideológicas subjetivas</strong>:
            </p>
            <ul className="space-y-2.5 my-2">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>
                  <strong>Economia de cota vs. representação:</strong> Penalizar gastos indiscriminadamente prejudica
                  parlamentares de estados distantes de Brasília (como Norte e Nordeste) que necessitam de transporte
                  aéreo contínuo para manter contato com suas bases, ou mandatos que investem em assessoria técnica especializada.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-1">•</span>
                <span>
                  <strong>Volume bruto vs. impacto legislativo:</strong> Medir deputados pela quantidade de projetos apresentados
                  estimula a chamada "inflação legislativa" (apresentação massiva de projetos protocolares ou datas comemorativas),
                  enquanto desvaloriza atuações técnicas em comissões ou relatorias complexas.
                </span>
              </li>
            </ul>
            <HighlightBox>
              <strong>Nossa diretriz:</strong> Apresentar os dados primários, desagregados e contextuais. O cidadão é o único
              juiz legítimo de quem o representa bem.
            </HighlightBox>
          </Acordeao>

          {/* ── 2. Fontes de Dados Oficiais ── */}
          <Acordeao
            title="2. Fontes de Dados Oficiais e Auditabilidade"
            icon={<Database size={18} className="text-emerald-600" />}
          >
            <p>
              Todas as informações disponibilizadas pelo QuemVota são extraídas de dados abertos oficiais da Câmara dos Deputados:
            </p>
            <ul className="space-y-2 mt-2">
              <li className="flex items-start gap-2">
                <span className="text-emerald-500 mt-0.5">•</span>
                <span>
                  <strong>API de Dados Abertos da Câmara:</strong>{" "}
                  <a
                    href="https://dadosabertos.camara.leg.br/swagger/api.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    dadosabertos.camara.leg.br
                  </a>{" "}
                  — Votações nominais, presenças em sessões deliberativas, autoria de matérias e discursos.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-emerald-500 mt-0.5">•</span>
                <span>
                  <strong>Despesas da Cota Parlamentar (CEAP) e Gabinete:</strong> Registros mensais de prestação de contas com fornecedores, valores líquidos e notas fiscais declaradas.
                </span>
              </li>
            </ul>
          </Acordeao>

          {/* ── 3. Execução Orçamentária ── */}
          <Acordeao
            title="3. Transparência de Recursos Públicos (CEAP e Gabinete)"
            icon={<DollarSign size={18} className="text-amber-600" />}
          >
            <p>
              Acompanhamos a execução dos recursos orçamentários disponibilizados para cada gabinete:
            </p>
            <ul className="space-y-2 mt-2">
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>
                  <strong>Cota Parlamentar (CEAP):</strong> Verba indenizatória que cobre passagens aéreas, telefonia,
                  combustível, hospedagem e consultorias. O limite varia por unidade federativa, refletindo as regras
                  oficiais da Mesa Diretora da Câmara.
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-amber-500 mt-0.5">•</span>
                <span>
                  <strong>Verba de Gabinete:</strong> Destinada à contratação e remuneração de secretários parlamentares
                  e assessores de apoio em Brasília e no estado de origem.
                </span>
              </li>
            </ul>
          </Acordeao>

          {/* ── 4. Assiduidade Oficial ── */}
          <Acordeao
            title="4. Assiduidade nas Sessões Deliberativas"
            icon={<Users size={18} className="text-violet-600" />}
          >
            <p>
              A taxa de assiduidade reflete a presença oficial do parlamentar nas sessões de plenário em que houve deliberação
              ou votação nominal:
            </p>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 font-mono text-xs">
              Taxa de Assiduidade (%) = (Presenças Registradas ÷ Total de Sessões Deliberativas) × 100
            </div>
            <p className="text-xs text-slate-500">
              Registros de licença médica, missões oficiais autorizadas ou ausências justificadas são preservados conforme os relatórios da Câmara.
            </p>
          </Acordeao>

          {/* ── 5. Inteligência Artificial e Classificação Temática ── */}
          <Acordeao
            title="5. Classificação Temática por Inteligência Artificial"
            icon={<Sparkles size={18} className="text-indigo-600" />}
          >
            <p>
              Utilizamos modelos de processamento de linguagem natural (modelo semântico aberto <code>BAAI/bge-m3</code>) para:
            </p>
            <ul className="space-y-2 mt-2">
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">•</span>
                <span>
                  <strong>Identificação de Temas de Atuação:</strong> Analisar ementas e textos de proposições para classificar sua área de atuação (ex: Saúde, Educação, Segurança, Economia, Direitos Humanos).
                </span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-indigo-500 mt-0.5">•</span>
                <span>
                  <strong>Agrupamento e Busca Semântica:</strong> Encontrar projetos semelhantes e temas conexos via cálculo de distância vetorial por cosseno.
                </span>
              </li>
            </ul>
            <p className="text-xs text-slate-500">
              Os modelos de IA são empregados exclusivamente para categorização descritiva de conteúdo, nunca para emitir avaliações morais ou juízos sobre a qualidade das leis.
            </p>
          </Acordeao>

          {/* ── 6. Atividade Legislativa e Votações ── */}
          <Acordeao
            title="6. Votações Nominais e Posicionamento Parlamentar"
            icon={<FileText size={18} className="text-slate-600" />}
          >
            <p>
              O ponto central do QuemVota é permitir que o eleitor consulte o histórico completo de votos do parlamentar em matérias de grande relevância:
            </p>
            <ul className="space-y-2 mt-2">
              <li className="flex items-start gap-2">
                <span className="text-slate-400 mt-0.5">•</span>
                <span>Voto registrado em plenário: <strong>Sim</strong>, <strong>Não</strong>, <strong>Abstenção</strong> ou <strong>Obstrução</strong>.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-slate-400 mt-0.5">•</span>
                <span>Confronto direto com a orientação de bancada para mensuração da fidelidade partidária.</span>
              </li>
            </ul>
          </Acordeao>

        </div>
      </div>
    </>
  )
}