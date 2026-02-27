import { useState } from "react"
import { Link } from "react-router-dom"
import Header from "../components/Header"
import {
  CheckCircle2,
  Circle,
  Zap,
  Lock,
  Database,
  UserCircle,
  Brain,
  Landmark,
  Smartphone,
  Github,
  ArrowRight,
  Star,
  Clock,
  Sparkles,
} from "lucide-react"

// ─────────────────────────────────────────────────────────────────────────────
// Tipos e dados
// ─────────────────────────────────────────────────────────────────────────────

type Status = "done" | "inprogress" | "next" | "future"

interface RoadmapItem {
  fase: string
  status: Status
  icon: React.ReactNode
  title: string
  subtitle: string
  descricao: string
  detalhes: string[]
  tag?: string
}

const STATUS_CONFIG: Record<Status, {
  label: string
  dot: string
  badge: string
  badgeText: string
  ring: string
  lineBg: string
}> = {
  done: {
    label: "Concluído",
    dot: "bg-emerald-500 border-emerald-500",
    badge: "bg-emerald-50 text-emerald-700 border-emerald-200",
    badgeText: "Concluído",
    ring: "border-emerald-100",
    lineBg: "bg-emerald-200",
  },
  inprogress: {
    label: "Em progresso",
    dot: "bg-blue-500 border-blue-500 animate-pulse",
    badge: "bg-blue-50 text-blue-700 border-blue-200",
    badgeText: "Em progresso",
    ring: "border-blue-200",
    lineBg: "bg-blue-200",
  },
  next: {
    label: "A seguir",
    dot: "bg-white border-slate-400",
    badge: "bg-amber-50 text-amber-700 border-amber-200",
    badgeText: "A seguir",
    ring: "border-slate-200",
    lineBg: "bg-slate-200",
  },
  future: {
    label: "Futuro",
    dot: "bg-white border-slate-300",
    badge: "bg-slate-50 text-slate-500 border-slate-200",
    badgeText: "Planejado",
    ring: "border-slate-100",
    lineBg: "bg-slate-100",
  },
}

const FASES: RoadmapItem[] = [
  {
    fase: "Fase 1",
    status: "done",
    icon: <Database size={18} />,
    title: "Coleta e estruturação de dados",
    subtitle: "A base de tudo",
    descricao:
      "Coleta automatizada de todas as bases disponíveis na API pública da Câmara dos Deputados — deputados, votações, proposições, presenças e despesas — com pipeline de atualização diária.",
    detalhes: [
      "Integração com a API de Dados Abertos da Câmara",
      "Coleta de todos os deputados federais ativos",
      "Histórico de votações nominais e simbólicas",
      "Despesas da cota parlamentar (CEAP)",
      "Tramitação e autoria de proposições",
      "Score de performance parlamentar (assiduidade, economia, produção)",
    ],
  },
  {
    fase: "Fase 2",
    status: "done",
    icon: <CheckCircle2 size={18} />,
    title: "Plataforma web pública",
    subtitle: "Transparência para qualquer cidadão",
    descricao:
      "Lançamento do site com visualizações acessíveis de todos os dados coletados — perfis detalhados de parlamentares, rankings, projetos de lei e votações.",
    detalhes: [
      "Página de perfil individual de cada deputado",
      "Histórico de gastos com gráficos interativos",
      "Rankings por performance, economia e produção",
      "Busca de proposições legislativas",
      "Detalhamento de votações com orientação dos partidos",
      "Design responsivo para mobile e desktop",
    ],
  },
  {
    fase: "Fase 3",
    status: "inprogress",
    icon: <Database size={18} />,
    title: "Base de dados completa",
    subtitle: "Mais dados, mais profundidade",
    tag: "Você está aqui",
    descricao:
      "Expansão da cobertura de dados para incluir todo o histórico disponível na Câmara, dados do Senado, partidos, bancadas temáticas e dados eleitorais do TSE.",
    detalhes: [
      "Histórico completo de mandatos anteriores",
      "Dados do Senado Federal via API pública",
      "Informações de campanha eleitoral (TSE)",
      "Composição de bancadas temáticas e frentes parlamentares",
      "Histórico de filiações partidárias",
      "Cobertura de parlamentares estaduais (MVP)",
    ],
  },
  {
    fase: "Fase 4",
    status: "next",
    icon: <UserCircle size={18} />,
    title: "Contas de usuário",
    subtitle: "Sua visão personalizada do Congresso",
    descricao:
      "Criação de perfis para que cidadãos possam salvar seus parlamentares de interesse, configurar alertas de votações e acompanhar temas legislativos específicos.",
    detalhes: [
      "Cadastro e autenticação de usuários",
      "Favoritar parlamentares e receber resumos periódicos",
      "Alertas por e-mail quando um deputado favoritado votar",
      "Painel personalizado com os temas que mais importam para você",
      "Histórico de consultas e comparações salvas",
      "Exportação de dados em CSV/PDF",
    ],
  },
  {
    fase: "Fase 5",
    status: "future",
    icon: <Brain size={18} />,
    title: "Análise com IA",
    subtitle: "Inteligência sobre cada mandato",
    descricao:
      "Modelo treinado sobre o histórico completo de cada parlamentar para gerar análises automáticas de viés ideológico, consistência de votos, pontos fortes e fracos do mandato.",
    detalhes: [
      "Mapa de posicionamento ideológico baseado em padrões de votação",
      "Análise de consistência: o que o deputado prometeu vs. o que votou",
      "Vieses temáticos identificados automaticamente (agro, ambiental, econômico...)",
      "Pontos fortes e fracos do mandato em linguagem acessível",
      "Comparação automática com a média da bancada e do partido",
      "Resumo do mandato gerado por IA com base em dados reais",
    ],
    tag: "Alta complexidade",
  },
  {
    fase: "Fase 6",
    status: "future",
    icon: <Landmark size={18} />,
    title: "Executivo e Judiciário",
    subtitle: "O poder além do Congresso",
    descricao:
      "Expansão do escopo para cobrir os outros poderes: ministérios, TCU, STF, STJ e agências reguladoras — usando APIs públicas e dados de transparência ativa.",
    detalhes: [
      "Painel de ministros e secretarias federais",
      "Gastos do executivo federal por órgão e ministério",
      "Decisões relevantes do STF com explicação em linguagem simples",
      "Relatórios do TCU sobre irregularidades e condenações",
      "Agências reguladoras: composição e histórico de decisões",
      "Cruzamento entre votações do Congresso e decisões do executivo",
    ],
    tag: "Dependência de dados abertos",
  },
  {
    fase: "Fase 7",
    status: "future",
    icon: <Smartphone size={18} />,
    title: "Aplicativo móvel",
    subtitle: "O Congresso no seu bolso",
    descricao:
      "App nativo para iOS e Android com notificações em tempo real, acesso offline a perfis favoritos e interface otimizada para consumo rápido de informação.",
    detalhes: [
      "App para iOS (App Store) e Android (Play Store)",
      "Notificações push para votações importantes",
      "Acesso offline a perfis de parlamentares favoritos",
      "Widget de resumo diário para tela inicial",
      "Compartilhamento de dados com um toque",
      "Modo escuro nativo",
    ],
  },
]

// ─────────────────────────────────────────────────────────────────────────────
// Componentes auxiliares
// ─────────────────────────────────────────────────────────────────────────────

function StatusIcon({ status }: { status: Status }) {
  if (status === "done") return <CheckCircle2 size={14} className="text-emerald-600" />
  if (status === "inprogress") return <Zap size={14} className="text-blue-600" />
  if (status === "next") return <Clock size={14} className="text-amber-600" />
  return <Lock size={14} className="text-slate-400" />
}

function FaseCard({ item, index }: { item: RoadmapItem; index: number }) {
  const [expanded, setExpanded] = useState(item.status === "done" || item.status === "inprogress")
  const cfg = STATUS_CONFIG[item.status]

  return (
    <div className="flex gap-5 sm:gap-7 relative">

      {/* Coluna esquerda: dot + linha */}
      <div className="flex flex-col items-center flex-shrink-0">
        {/* Dot */}
        <div className={`w-4 h-4 rounded-full border-2 mt-1 z-10 flex-shrink-0 ${cfg.dot}`} />
        {/* Linha vertical (não aparece no último) */}
        {index < FASES.length - 1 && (
          <div className={`flex-1 w-px mt-2 mb-0 min-h-8 ${cfg.lineBg}`} />
        )}
      </div>

      {/* Card */}
      <div className={`flex-1 mb-8 rounded-2xl border bg-white shadow-sm overflow-hidden transition-all duration-200 ${cfg.ring}`}>

        {/* Header do card */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="w-full text-left px-5 py-4 cursor-pointer bg-transparent border-0 hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3 flex-1 min-w-0">
              {/* Número da fase */}
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 border ${
                item.status === "done"
                  ? "bg-emerald-50 text-emerald-600 border-emerald-100"
                  : item.status === "inprogress"
                  ? "bg-blue-50 text-blue-600 border-blue-100"
                  : "bg-slate-50 text-slate-400 border-slate-100"
              }`}>
                {item.icon}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap mb-0.5">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    {item.fase}
                  </span>
                  <span className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full border ${cfg.badge}`}>
                    <StatusIcon status={item.status} />
                    {cfg.badgeText}
                  </span>
                  {item.tag && (
                    <span className="text-[10px] font-medium text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full border border-slate-200">
                      {item.tag}
                    </span>
                  )}
                </div>
                <h3
                  style={{ fontFamily: "'Fraunces', serif" }}
                  className={`text-base font-bold leading-snug ${
                    item.status === "future" ? "text-slate-500" : "text-slate-800"
                  }`}
                >
                  {item.title}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{item.subtitle}</p>
              </div>
            </div>

            {/* Chevron */}
            <div className={`text-slate-300 flex-shrink-0 mt-1 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </div>
          </div>

          {/* Descrição sempre visível */}
          <p className="text-sm text-slate-500 leading-relaxed mt-3 text-left">
            {item.descricao}
          </p>
        </button>

        {/* Detalhes expandidos */}
        {expanded && (
          <div className="px-5 pb-5 pt-1 border-t border-slate-100">
            <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3 mt-3">
              O que inclui
            </p>
            <ul className="space-y-2">
              {item.detalhes.map((d, i) => (
                <li key={i} className="flex items-start gap-2.5 text-sm text-slate-600">
                  <span className={`flex-shrink-0 mt-[3px] ${
                    item.status === "done"
                      ? "text-emerald-500"
                      : item.status === "inprogress"
                      ? "text-blue-400"
                      : "text-slate-300"
                  }`}>
                    {item.status === "done"
                      ? <CheckCircle2 size={13} />
                      : item.status === "inprogress"
                      ? <Circle size={13} />
                      : <Circle size={13} />
                    }
                  </span>
                  {d}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Barra de progresso geral
// ─────────────────────────────────────────────────────────────────────────────

function ProgressoGeral() {
  const done = FASES.filter((f) => f.status === "done").length
  const inprogress = FASES.filter((f) => f.status === "inprogress").length
  const total = FASES.length
  const pct = Math.round(((done + inprogress * 0.5) / total) * 100)

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 mb-10">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-sm font-semibold text-slate-800">Progresso geral</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {done} fases concluídas · {inprogress} em andamento · {total - done - inprogress} planejadas
          </p>
        </div>
        <span
          style={{ fontFamily: "'Fraunces', serif" }}
          className="text-3xl font-bold text-slate-800"
        >
          {pct}%
        </span>
      </div>

      {/* Barra segmentada */}
      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden bg-slate-100">
        {FASES.map((f, i) => (
          <div
            key={i}
            className={`flex-1 rounded-sm transition-all ${
              f.status === "done"
                ? "bg-emerald-500"
                : f.status === "inprogress"
                ? "bg-blue-400"
                : "bg-slate-100"
            }`}
          />
        ))}
      </div>

      <div className="flex items-center gap-4 mt-3">
        {[
          { color: "bg-emerald-500", label: "Concluído" },
          { color: "bg-blue-400", label: "Em andamento" },
          { color: "bg-slate-200", label: "Planejado" },
        ].map((l) => (
          <div key={l.label} className="flex items-center gap-1.5">
            <div className={`w-2 h-2 rounded-full ${l.color}`} />
            <span className="text-[11px] text-slate-400">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Roadmap() {
  return (
    <>
      <Header />
      <div className="min-h-screen bg-gray-50 pt-16">

        {/* Header da página */}
        <div className="bg-white border-b border-slate-200">
          <div className="max-w-3xl mx-auto px-6 py-12">
            <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-3">
              Institucional
            </p>
            <h1
              style={{ fontFamily: "'Fraunces', serif" }}
              className="text-4xl font-bold text-slate-900 mb-4 leading-tight"
            >
              Roadmap do projeto
            </h1>
            <p className="text-base text-slate-500 leading-relaxed max-w-xl">
              Onde estamos, para onde vamos e o que estamos construindo.
              Transparência sobre o futuro do quemvota — porque democracia começa pela honestidade.
            </p>
          </div>
        </div>

        <div className="max-w-3xl mx-auto px-6 py-10">

          {/* Barra de progresso */}
          <ProgressoGeral />

          {/* Aviso de contribuição */}
          <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-5 py-4 mb-10">
            <Sparkles size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-amber-800">Roadmap público e colaborativo</p>
              <p className="text-xs text-amber-700 mt-0.5 leading-relaxed">
                Este é um projeto open source. Qualquer pessoa pode sugerir funcionalidades, reportar
                bugs ou contribuir com código. Discuta prioridades no{" "}
                <a
                  href="https://github.com/WrongProvider/quemVota"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium underline hover:text-amber-900"
                >
                  GitHub
                </a>
                .
              </p>
            </div>
          </div>

          {/* Timeline das fases */}
          <div>
            {FASES.map((item, i) => (
              <FaseCard key={i} item={item} index={i} />
            ))}
          </div>

          {/* CTA final */}
          <div className="mt-4 bg-[#1a1a1a] rounded-2xl p-8">
            <div className="flex items-start gap-4 flex-col sm:flex-row">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Star size={16} className="text-amber-400" />
                  <span className="text-xs font-semibold text-amber-400 uppercase tracking-wider">
                    Código aberto
                  </span>
                </div>
                <h3
                  style={{ fontFamily: "'Fraunces', serif" }}
                  className="text-xl font-bold text-white mb-2"
                >
                  Quer acelerar alguma dessas fases?
                </h3>
                <p className="text-slate-400 text-sm leading-relaxed">
                  Contribuições são bem-vindas — seja código, design, dados ou só uma boa ideia.
                  O quemvota é construído por quem acredita que informação muda democracia.
                </p>
              </div>
              <div className="flex flex-col gap-2 flex-shrink-0">
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-white text-slate-900 text-sm font-medium rounded-xl no-underline hover:bg-slate-100 transition-colors"
                >
                  <Github size={15} /> Contribuir
                </a>
                <Link
                  to="/sobre"
                  className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-white/10 hover:bg-white/20 text-white text-sm font-medium rounded-xl no-underline transition-colors"
                >
                  Sobre o projeto <ArrowRight size={14} />
                </Link>
              </div>
            </div>
          </div>

        </div>

        {/* Rodapé */}
        <div className="border-t border-slate-200 bg-white py-6 text-center mt-10">
          <p className="text-xs text-slate-400">
            Dados públicos da{" "}
            <a href="https://dadosabertos.camara.leg.br" target="_blank" rel="noreferrer" className="text-slate-500 hover:text-blue-600 transition-colors">
              Câmara dos Deputados
            </a>
            {" "}· quemvota.com.br
          </p>
        </div>
      </div>
    </>
  )
}