import { useState, useMemo } from "react"
import { Link } from "react-router-dom"
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  FileText,
  Award,
  Building2,
  Search,
  Filter,
  ChevronRight,
  ChevronLeft,
  Loader2,
  MapPin,
  Calendar,
  Info,
} from "lucide-react"
import {
  useRankingPerformance,
  useRankingDespesas,
  useRankingDiscursos,
  useRankingLucroEmpresas,
} from "../hooks/useRankings"
import Header from "../components/Header"
import {
  DespesaRankingService,
  FormatService,
  FilterService,
  PerformanceRankingService,
} from "../services/rankings.service"
import type { PerformanceParams } from "../api/rankings.api"

const PATH_FOTOS = "/fotos_politicos/"

// Primeiro ano disponível no ranking (leg. 54 = eleitos 2010, exercício 2011)
const ANO_INICIO = 2011

// ─────────────────────────────────────────────────────────────────────────────
// Tipos de abas
// ─────────────────────────────────────────────────────────────────────────────

type ActiveTab = "performance" | "gastos" | "economia" | "empresas" | "discursos"

const TABS: { id: ActiveTab; label: string; icon: React.ReactNode }[] = [
  { id: "performance", label: "Melhor Performance", icon: <TrendingUp size={15} /> },
  { id: "gastos",      label: "Maiores Gastos",     icon: <TrendingDown size={15} /> },
  { id: "economia",    label: "Mais Econômicos",    icon: <DollarSign size={15} /> },
  { id: "discursos",   label: "Mais Discursos",     icon: <FileText size={15} /> },
  { id: "empresas",    label: "Empresas",           icon: <Building2 size={15} /> },
]

// ─────────────────────────────────────────────────────────────────────────────
// Estados de loading / vazio / erro
// ─────────────────────────────────────────────────────────────────────────────

function EstadoLoading() {
  return (
    <div className="flex items-center justify-center py-20 gap-3 text-slate-400">
      <Loader2 size={20} className="animate-spin" />
      <span className="text-sm">Carregando ranking...</span>
    </div>
  )
}

function EstadoVazio({ mensagem }: { mensagem: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
      <Award size={36} className="mb-3 opacity-30" />
      <p className="text-sm">{mensagem}</p>
    </div>
  )
}

function EstadoErro({ mensagem }: { mensagem: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="text-sm font-semibold text-slate-600">Erro ao carregar dados</p>
      <p className="text-xs text-slate-400 mt-1">{mensagem}</p>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Seletor de linha do tempo — padrão idêntico ao TimelineSelector
// de PoliticosDetalhe para consistência de estilo
// ─────────────────────────────────────────────────────────────────────────────

function TimelineSelector({
  anos,
  anoSelecionado,
  onChange,
}: {
  anos: number[]
  anoSelecionado: number | null
  onChange: (ano: number | null) => void
}) {
  if (!anos.length) return null

  const idx = anoSelecionado ? anos.indexOf(anoSelecionado) : -1

  const handlePrev = () => {
    if (idx > 0) onChange(anos[idx - 1])
    else if (idx === -1) onChange(anos[anos.length - 1])
  }

  const handleNext = () => {
    if (idx === -1) return
    if (idx < anos.length - 1) onChange(anos[idx + 1])
    else onChange(null)
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden mx-5 mt-5 mb-1">
      {/* Cabeçalho */}
      <div className="bg-slate-50 border-b border-slate-100 px-6 py-3 text-center">
        <p className="text-sm font-medium text-slate-500">
          {anoSelecionado ? (
            <>
              Exibindo dados de{" "}
              <strong className="text-slate-800">{anoSelecionado}</strong>
              {" "}— parlamentares comparados no mesmo período
            </>
          ) : (
            "Selecione um ano ou compare pela média de mandato"
          )}
        </p>
      </div>

      <div className="px-6 py-5">
        <div className="flex items-center gap-3">
          {/* ← anterior */}
          <button
            onClick={handlePrev}
            disabled={idx === 0}
            className="w-9 h-9 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            <ChevronLeft size={16} />
          </button>

          {/* Track */}
          <div className="flex-1 relative overflow-x-auto">
            <div className="absolute top-[18px] left-0 right-0 h-px bg-slate-200 -translate-y-1/2 z-0" />
            <div className="relative z-10 flex items-end gap-0 pb-1 min-w-max">
              {/* Botão "Todos" (∑) */}
              <div className="flex flex-col items-center mr-6 flex-shrink-0">
                <button
                  onClick={() => onChange(null)}
                  className={`w-9 h-9 rounded-lg border-2 text-xs font-bold transition-all ${
                    anoSelecionado === null
                      ? "bg-slate-700 border-slate-700 text-white shadow-md scale-110"
                      : "bg-white border-slate-300 text-slate-500 hover:border-slate-400"
                  }`}
                  title="Média de mandato (todos os anos)"
                >
                  ∑
                </button>
                <span className="text-[10px] text-slate-400 mt-1.5 whitespace-nowrap">Todos</span>
              </div>

              {/* Anos */}
              {anos.map((ano) => {
                const ativo = ano === anoSelecionado
                return (
                  <button
                    key={ano}
                    onClick={() => onChange(ativo ? null : ano)}
                    className="flex flex-col items-center gap-0 group mx-3 flex-shrink-0"
                  >
                    <div
                      className={`w-4 h-4 rounded-full border-2 transition-all ${
                        ativo
                          ? "bg-yellow-400 border-yellow-500 scale-150 shadow-md"
                          : "bg-white border-slate-300 group-hover:border-blue-400 group-hover:scale-125"
                      }`}
                    />
                    {ativo ? (
                      <span className="text-xs font-bold text-white bg-yellow-400 px-2 py-0.5 rounded-md shadow-sm mt-2 whitespace-nowrap">
                        {ano}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-500 group-hover:text-blue-600 transition-colors mt-2 whitespace-nowrap">
                        {ano}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </div>

          {/* → próximo */}
          <button
            onClick={handleNext}
            disabled={anoSelecionado === null}
            className="w-9 h-9 rounded-lg border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-50 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        <p className="text-center text-[11px] text-slate-400 mt-4">
          ⓘ Dados disponíveis a partir de {ANO_INICIO}. No ranking anual, apenas parlamentares com
          despesas registradas naquele período são incluídos.
        </p>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Badge de confiança do score
// ─────────────────────────────────────────────────────────────────────────────

function ConfiancaBadge({ confianca }: { confianca: "baixa" | "media" | "alta" }) {
  const map = {
    alta:  { label: "Alta",  cls: "bg-emerald-50 text-emerald-700 border-emerald-100" },
    media: { label: "Média", cls: "bg-amber-50 text-amber-700 border-amber-100"       },
    baixa: { label: "Baixa", cls: "bg-slate-100 text-slate-500 border-slate-200"      },
  }
  const { label, cls } = map[confianca] ?? map.baixa
  return (
    <span className={`text-[10px] font-semibold border px-1.5 py-0.5 rounded-full ${cls}`}>
      {label}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Pódio top 3
// ─────────────────────────────────────────────────────────────────────────────

function PodioCard({
  politico,
  position,
  anoSelecionado,
}: {
  politico: any
  position: number
  anoSelecionado: number | null
}) {
  const medals      = ["🥇", "🥈", "🥉"]
  const ringColors  = ["ring-yellow-400", "ring-slate-400", "ring-amber-600"]
  const badgeColors = [
    "bg-yellow-400 text-white",
    "bg-slate-400 text-white",
    "bg-amber-600 text-white",
  ]

  return (
    <Link to={`/politicos_detalhe/${politico.id}`} className="no-underline">
      <div className="group px-5 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors flex items-center gap-4">
        {/* Posição */}
        <div className="w-9 h-9 rounded-full bg-amber-50 border border-amber-100 flex items-center justify-center text-lg flex-shrink-0">
          {medals[position - 1]}
        </div>

        {/* Foto */}
        <div className={`w-12 h-12 rounded-xl overflow-hidden bg-slate-100 border-2 ring-2 ${ringColors[position - 1]} flex-shrink-0`}>
          <img
            src={`${PATH_FOTOS}${politico.id}.jpg`}
            alt={politico.nome}
            className="w-full h-full object-cover"
          />
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-slate-800 truncate">{politico.nome}</p>
          <div className="flex items-center gap-1.5 mt-1 flex-wrap">
            <span className="font-mono text-[11px] font-semibold text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
              {politico.partido}
            </span>
            <span className="font-mono inline-flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
              <MapPin size={9} /> {politico.uf}
            </span>
            {/* Badge de confiança apenas no modo média de mandato */}
            {!anoSelecionado && <ConfiancaBadge confianca={politico.confianca} />}
          </div>
        </div>

        {/* Score */}
        <div className="text-right flex-shrink-0">
          <div className={`inline-flex items-center justify-center px-3 py-1 rounded-lg text-sm font-bold ${badgeColors[position - 1]}`}>
            {politico.score.toFixed(1)}
          </div>
          <p className="text-[10px] text-slate-400 mt-0.5 text-center">
            {anoSelecionado ? anoSelecionado : "score médio"}
          </p>
        </div>

        <ChevronRight size={14} className="text-slate-300 group-hover:text-blue-400 transition-colors flex-shrink-0" />
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de ranking padrão
// ─────────────────────────────────────────────────────────────────────────────

function RankingRow({
  position,
  politico,
  type,
  anoSelecionado,
}: {
  position: number
  politico: any
  type: "performance" | "gastos" | "economia"
  anoSelecionado?: number | null
}) {
  const isTop3 = position <= 3

  return (
    <Link to={`/politicos_detalhe/${politico.id}`} className="no-underline">
      <div className="group px-5 py-3.5 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors flex items-center gap-4">
        {/* Posição */}
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
            isTop3
              ? "bg-amber-50 text-amber-600 border border-amber-200"
              : "bg-slate-100 text-slate-500"
          }`}
        >
          {position}
        </div>

        {/* Foto (apenas performance) */}
        {type === "performance" && (
          <div className="w-10 h-10 rounded-xl overflow-hidden bg-slate-100 border border-slate-200 flex-shrink-0">
            <img
              src={`${PATH_FOTOS}${politico.id}.jpg`}
              alt={politico.nome}
              className="w-full h-full object-cover"
            />
          </div>
        )}

        {/* Info */}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-slate-800 truncate">{politico.nome}</p>
          {type === "performance" && (
            <div className="flex items-center gap-1.5 mt-0.5 flex-wrap">
              <span className="font-mono text-[11px] text-slate-500">{politico.partido}</span>
              <span className="text-slate-300">·</span>
              <span className="font-mono text-[11px] text-slate-500">{politico.uf}</span>
              {!anoSelecionado && <ConfiancaBadge confianca={politico.confianca} />}
            </div>
          )}
        </div>

        {/* Valor */}
        <div className="text-right flex-shrink-0">
          {type === "performance" && (
            <div>
              <span className="font-mono text-sm font-bold text-blue-600">
                {politico.score.toFixed(1)}
              </span>
              <p className="text-[10px] text-slate-400 mt-0.5">
                {anoSelecionado ? anoSelecionado : "médio"}
              </p>
            </div>
          )}
          {(type === "gastos" || type === "economia") && (
            <span
              className={`font-mono text-sm font-bold ${
                type === "gastos" ? "text-red-500" : "text-emerald-600"
              }`}
            >
              {FormatService.formatarMoeda(politico.total_gasto)}
            </span>
          )}
        </div>

        <ChevronRight size={13} className="text-slate-300 group-hover:text-blue-400 transition-colors flex-shrink-0" />
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de discurso
// ─────────────────────────────────────────────────────────────────────────────

function DiscursoRow({ position, politico }: { position: number; politico: any }) {
  const isTop3 = position <= 3

  return (
    <Link to={`/politicos_detalhe/${politico.politico_id}`} className="no-underline">
      <div className="group px-5 py-4 border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors">
        <div className="flex items-start gap-4">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 mt-0.5 ${
              isTop3
                ? "bg-amber-50 text-amber-600 border border-amber-200"
                : "bg-slate-100 text-slate-500"
            }`}
          >
            {position}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-3 mb-2">
              <div>
                <p className="font-semibold text-sm text-slate-800">{politico.nome_politico}</p>
                <div className="flex items-center gap-1.5 mt-0.5">
                  <span className="font-mono text-[11px] text-slate-500">{politico.sigla_partido}</span>
                  <span className="text-slate-300">·</span>
                  <span className="font-mono text-[11px] text-slate-500">{politico.sigla_uf}</span>
                </div>
              </div>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold rounded-lg flex-shrink-0">
                <FileText size={11} /> {politico.total_discursos}
              </span>
            </div>

            {politico.temas_mais_discutidos?.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {politico.temas_mais_discutidos.slice(0, 5).map((tema: any, idx: number) => (
                  <span
                    key={idx}
                    className="text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md"
                  >
                    {tema.keyword}
                    <span className="text-slate-400 ml-1">({tema.frequencia})</span>
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </Link>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de empresa
// ─────────────────────────────────────────────────────────────────────────────

function EmpresaRow({ position, empresa }: { position: number; empresa: any }) {
  const isTop3 = position <= 3

  return (
    <div className="px-5 py-3.5 border-b border-slate-100 last:border-0 flex items-center gap-4">
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center font-mono font-bold text-xs flex-shrink-0 ${
          isTop3
            ? "bg-amber-50 text-amber-600 border border-amber-200"
            : "bg-slate-100 text-slate-500"
        }`}
      >
        {position}
      </div>

      <div className="w-9 h-9 bg-slate-100 rounded-xl flex items-center justify-center flex-shrink-0">
        <Building2 size={16} className="text-slate-500" />
      </div>

      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-slate-800 truncate">{empresa.nome_fornecedor}</p>
        {empresa.cnpj && (
          <p className="text-[11px] text-slate-400 font-mono mt-0.5">{empresa.cnpj}</p>
        )}
      </div>

      <span className="font-mono text-sm font-bold text-emerald-600 flex-shrink-0">
        {FormatService.formatarMoeda(empresa.total_recebido)}
      </span>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Aba Performance — linha do tempo integrada
// ─────────────────────────────────────────────────────────────────────────────

function RankingPerformance({
  searchTerm,
  selectedUF,
  selectedPartido,
}: {
  searchTerm: string
  selectedUF: string
  selectedPartido: string
}) {
  const [anoSelecionado, setAnoSelecionado] = useState<number | null>(null)

  const anosDisponiveis = useMemo(
    () => PerformanceRankingService.getAnosDisponiveis(ANO_INICIO),
    [],
  )

  const params: PerformanceParams = {
    ano:     anoSelecionado ?? undefined,
    q:       searchTerm      || undefined,
    uf:      selectedUF      || undefined,
    partido: selectedPartido || undefined,
  }

  const { data, isLoading, error } = useRankingPerformance(params)

  const ranking = data?.ranking ?? []
  const top3    = ranking.slice(0, 3)
  const rest    = ranking.slice(3, 50)

  return (
    <>
      {/* ── Seletor de ano (linha do tempo) ── */}
      <TimelineSelector
        anos={anosDisponiveis}
        anoSelecionado={anoSelecionado}
        onChange={setAnoSelecionado}
      />

      {/* ── Banner do filtro ativo ── */}
      {anoSelecionado && (
        <div className="flex items-center justify-between bg-blue-50 border border-blue-100 rounded-xl mx-5 mt-3 px-4 py-3">
          <p className="text-sm text-blue-700 font-medium flex items-center gap-1.5">
            <Calendar size={13} />
            Dados filtrados para o ano <strong>{anoSelecionado}</strong>
          </p>
          <button
            onClick={() => setAnoSelecionado(null)}
            className="text-xs text-blue-500 hover:text-blue-700 font-medium underline underline-offset-2 transition-colors"
          >
            Ver média de mandato
          </button>
        </div>
      )}

      {/* ── Aviso de cobertura histórica ── */}
      {data?.aviso && (
        <div className="mx-5 mt-3 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start gap-2.5">
          <Info size={13} className="text-slate-400 flex-shrink-0 mt-0.5" />
          <p className="text-[11px] text-slate-500 leading-relaxed">{data.aviso}</p>
        </div>
      )}

      {/* ── Legenda de confiança (apenas modo média de mandato) ── */}
      {!anoSelecionado && (
        <div className="mx-5 mt-3 mb-1 flex items-center gap-3 flex-wrap">
          <span className="text-[10px] text-slate-400 font-semibold uppercase tracking-wide">
            Confiança:
          </span>
          {(["alta", "media", "baixa"] as const).map((c) => (
            <ConfiancaBadge key={c} confianca={c} />
          ))}
          <span className="text-[10px] text-slate-400">
            Alta = 4+ anos · Média = 2-3 · Baixa = 1 ano de dados
          </span>
        </div>
      )}

      {/* ── Separador antes da lista ── */}
      <div className="mt-4 border-t border-slate-100" />

      {/* ── Lista ── */}
      {isLoading ? (
        <EstadoLoading />
      ) : error ? (
        <EstadoErro mensagem={error.message} />
      ) : !ranking.length ? (
        <EstadoVazio
          mensagem={
            anoSelecionado
              ? `Nenhum parlamentar com dados em ${anoSelecionado}.`
              : "Nenhum dado de performance disponível."
          }
        />
      ) : (
        <>
          {/* Pódio */}
          <div className="border-b border-slate-100">
            <div className="px-5 py-2.5 bg-amber-50/60 border-b border-amber-100">
              <p className="text-[11px] font-semibold text-amber-700 uppercase tracking-wide">
                🏆 Pódio — Top 3
                {anoSelecionado && (
                  <span className="ml-2 font-normal text-amber-600 normal-case tracking-normal">
                    · {anoSelecionado}
                  </span>
                )}
              </p>
            </div>
            {top3.map((p, i) => (
              <PodioCard key={p.id} politico={p} position={i + 1} anoSelecionado={anoSelecionado} />
            ))}
          </div>

          {/* Posições 4–50 */}
          {rest.map((p, i) => (
            <RankingRow
              key={p.id}
              position={i + 4}
              politico={p}
              type="performance"
              anoSelecionado={anoSelecionado}
            />
          ))}
        </>
      )}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Demais abas
// ─────────────────────────────────────────────────────────────────────────────

function RankingGastos({ searchTerm, selectedUF }: { searchTerm: string; selectedUF: string }) {
  const { data, isLoading, error } = useRankingDespesas({
    q: searchTerm || undefined,
    uf: selectedUF || undefined,
    limit: 100,
  })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!data?.length) return <EstadoVazio mensagem="Nenhum resultado encontrado." />

  const stats = DespesaRankingService.calcularEstatisticas(data)

  return (
    <>
      <div className="grid grid-cols-3 divide-x divide-slate-100 border-b border-slate-100">
        {[
          { label: "Maior gasto", value: FormatService.formatarMoeda(stats.maior), color: "text-red-500" },
          { label: "Média",       value: FormatService.formatarMoeda(stats.media), color: "text-amber-600" },
          { label: "Total geral", value: FormatService.formatarMoeda(stats.total), color: "text-purple-600" },
        ].map((s) => (
          <div key={s.label} className="px-5 py-3 text-center">
            <p className={`font-mono font-bold text-sm ${s.color}`}>{s.value}</p>
            <p className="text-[11px] text-slate-400 mt-0.5">{s.label}</p>
          </div>
        ))}
      </div>
      {data.map((p, i) => (
        <RankingRow
          key={p.politico_id}
          position={i + 1}
          politico={{ id: p.politico_id, nome: p.nome, total_gasto: p.total_gasto }}
          type="gastos"
        />
      ))}
    </>
  )
}

function RankingEconomia({ searchTerm, selectedUF }: { searchTerm: string; selectedUF: string }) {
  const { data: rawData, isLoading, error } = useRankingDespesas({
    q: searchTerm || undefined,
    uf: selectedUF || undefined,
    limit: 100,
  })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!rawData?.length) return <EstadoVazio mensagem="Nenhum resultado encontrado." />

  const data = [...rawData].sort((a, b) => a.total_gasto - b.total_gasto)

  return (
    <>
      <div className="px-5 py-3 bg-emerald-50/60 border-b border-emerald-100">
        <p className="text-[11px] font-semibold text-emerald-700 uppercase tracking-wide">
          💡 Ordenado do menor para o maior gasto total
        </p>
      </div>
      {data.map((p, i) => (
        <RankingRow
          key={p.politico_id}
          position={i + 1}
          politico={{ id: p.politico_id, nome: p.nome, total_gasto: p.total_gasto }}
          type="economia"
        />
      ))}
    </>
  )
}

function RankingDiscursos() {
  const { data, isLoading, error } = useRankingDiscursos({ limit: 100 })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!data?.length) return <EstadoVazio mensagem="Nenhum dado de discursos disponível." />

  return (
    <>
      {data.map((p, i) => (
        <DiscursoRow key={p.politico_id} position={i + 1} politico={p} />
      ))}
    </>
  )
}

function RankingEmpresas() {
  const { data, isLoading, error } = useRankingLucroEmpresas({ limit: 100 })

  if (isLoading) return <EstadoLoading />
  if (error) return <EstadoErro mensagem={error.message} />
  if (!data?.length) return <EstadoVazio mensagem="Nenhum dado de empresas disponível." />

  return (
    <>
      {data.map((e, i) => (
        <EmpresaRow key={e.cnpj} position={i + 1} empresa={e} />
      ))}
    </>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Página principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Rankings() {
  const [activeTab, setActiveTab]             = useState<ActiveTab>("performance")
  const [searchTerm, setSearchTerm]           = useState("")
  const [selectedUF, setSelectedUF]           = useState("")
  const [selectedPartido, setSelectedPartido] = useState("")

  const showFilters       = activeTab !== "empresas" && activeTab !== "discursos"
  const showPartidoFilter = activeTab === "performance"

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }} className="min-h-screen bg-gray-50">
      <Header />

      {/* ── Cabeçalho da página ── */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-8 pt-24">
          <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-2">
            Câmara dos Deputados
          </p>
          <h1
            style={{ fontFamily: "'Fraunces', serif" }}
            className="text-3xl font-bold text-slate-900 mb-1"
          >
            Rankings Parlamentares
          </h1>
          <p className="text-slate-500 text-sm">
            Confira os parlamentares em destaque nas principais métricas de desempenho.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6 pb-16">
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

          {/* ── Abas ── */}
          <div className="flex border-b border-slate-200 overflow-x-auto">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-4 text-sm font-semibold transition-colors border-b-2 -mb-px whitespace-nowrap flex-shrink-0 ${
                  activeTab === tab.id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* ── Filtros de nome / UF / partido ── */}
          {showFilters && (
            <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50 flex items-center gap-3 flex-wrap">
              <div className="relative flex-1 min-w-[180px]">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="Buscar parlamentar..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
                />
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                <Filter size={13} className="text-slate-400" />

                <select
                  value={selectedUF}
                  onChange={(e) => setSelectedUF(e.target.value)}
                  className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
                >
                  <option value="">Todos os estados</option>
                  {FilterService.UFs.map((uf) => (
                    <option key={uf} value={uf}>{uf}</option>
                  ))}
                </select>

                {/* Filtro de partido — somente na aba performance */}
                {showPartidoFilter && (
                  <input
                    type="text"
                    placeholder="Partido (ex: PT)"
                    value={selectedPartido}
                    onChange={(e) => setSelectedPartido(e.target.value.toUpperCase())}
                    maxLength={10}
                    className="w-32 px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600 font-mono uppercase"
                  />
                )}
              </div>

              {(searchTerm || selectedUF || selectedPartido) && (
                <button
                  onClick={() => {
                    setSearchTerm("")
                    setSelectedUF("")
                    setSelectedPartido("")
                  }}
                  className="text-xs text-slate-500 hover:text-red-500 font-medium transition-colors px-2 py-1 rounded-lg hover:bg-red-50"
                >
                  Limpar
                </button>
              )}
            </div>
          )}

          {/* ── Conteúdo da aba ── */}
          <div className="pb-4">
            {activeTab === "performance" && (
              <RankingPerformance
                searchTerm={searchTerm}
                selectedUF={selectedUF}
                selectedPartido={selectedPartido}
              />
            )}
            {activeTab === "gastos"    && <RankingGastos    searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "economia"  && <RankingEconomia  searchTerm={searchTerm} selectedUF={selectedUF} />}
            {activeTab === "discursos" && <RankingDiscursos />}
            {activeTab === "empresas"  && <RankingEmpresas />}
          </div>

        </div>
      </div>
    </div>
  )
}