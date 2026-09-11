import { useState, useMemo } from "react"
import {
  MessageSquare,
  ArrowLeftRight,
  CheckCircle2,
  Calendar,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Tag,
  Layers,
} from "lucide-react"
import type { ComparacaoDiscursosResponse, ParDiscursoComparado } from "../api/politicos.api"

interface BlocoComparacaoDiscursosProps {
  readonly comparacao?: ComparacaoDiscursosResponse | null
  readonly loading: boolean
  readonly nomeA: string
  readonly nomeB: string
}

const ITENS_POR_PAGINA_INICIAL = 4

function formatarData(dataStr: string): string {
  try {
    const d = new Date(dataStr)
    return d.toLocaleDateString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    })
  } catch {
    return dataStr
  }
}

function CardDebateDiscurso({
  par,
  nomeA,
  nomeB,
  expandido,
  onToggle,
}: {
  readonly par: ParDiscursoComparado
  readonly nomeA: string
  readonly nomeB: string
  readonly expandido: boolean
  readonly onToggle: () => void
}) {
  const isConvergente = par.tipo_relacao === "convergente"
  const simPercent = Math.round(par.similaridade_semantica * 100)

  return (
    <article
      data-testid="card-par-discurso"
      className={`bg-white rounded-2xl border transition-all duration-200 shadow-sm overflow-hidden ${
        expandido
          ? "border-slate-300 ring-2 ring-slate-100 shadow-md"
          : "border-slate-200/90 hover:border-slate-300 hover:shadow"
      }`}
    >
      {/* Cabeçalho Compacto Clicável (Anti-Fatigue) */}
      <button
        type="button"
        onClick={onToggle}
        data-testid="btn-toggle-par-discurso"
        className="w-full text-left p-4 sm:p-4.5 flex flex-col gap-2.5 transition-colors hover:bg-slate-50/70 focus:outline-none min-h-[44px]"
        aria-expanded={expandido}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0 space-y-1">
            {/* Linha 1: Categoria e Status */}
            <div className="flex flex-wrap items-center gap-2">
              {par.categoria && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-700">
                  <Tag size={10} className="text-slate-500" />
                  {par.categoria}
                </span>
              )}
              <span
                className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                  isConvergente
                    ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                    : "bg-amber-50 text-amber-800 border border-amber-200/60"
                }`}
              >
                {isConvergente ? (
                  <>
                    <CheckCircle2 size={11} className="text-emerald-600" />
                    Discurso Parecido
                  </>
                ) : (
                  <>
                    <ArrowLeftRight size={11} className="text-amber-600" />
                    Discurso Divergente
                  </>
                )}
              </span>
              <span className="text-[11px] font-medium text-slate-500 hidden sm:inline">
                {simPercent}% similaridade
              </span>
            </div>

            {/* Linha 2: Título do Tema / Proposição */}
            <h4 className="text-sm font-bold text-slate-800 leading-snug line-clamp-2">
              {par.tema_ou_materia}
            </h4>

            {/* Linha 3: Resumo rápido das posturas */}
            <p className="text-xs text-slate-500 flex flex-wrap items-center gap-x-2 gap-y-0.5 pt-0.5">
              <span className="font-medium text-slate-700">
                {nomeA}:{" "}
                <span className="text-slate-500 font-normal">
                  {par.discurso_politico1.tipo_discurso || "Pronunciamento"}
                </span>
              </span>
              <span className="text-slate-300">•</span>
              <span className="font-medium text-slate-700">
                {nomeB}:{" "}
                <span className="text-slate-500 font-normal">
                  {par.discurso_politico2.tipo_discurso || "Pronunciamento"}
                </span>
              </span>
            </p>
          </div>

          {/* Botão Indicador de Expansão */}
          <div className="flex items-center gap-1.5 flex-shrink-0 pt-1">
            <span className="text-xs font-semibold text-blue-600 hidden md:inline">
              {expandido ? "Recolher" : "Ver debate"}
            </span>
            <div
              className={`w-8 h-8 rounded-xl flex items-center justify-center transition-colors ${
                expandido ? "bg-blue-50 text-blue-600" : "bg-slate-100 text-slate-500"
              }`}
            >
              {expandido ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>
          </div>
        </div>
      </button>

      {/* Conteúdo Expandido com Detalhes dos Dois Discursos */}
      {expandido && (
        <div className="border-t border-slate-100 p-4 sm:p-5 bg-slate-50/40 space-y-4 animate-in fade-in duration-200">
          {/* Fundamentação factual da classificação */}
          <div className="px-3.5 py-2.5 rounded-xl bg-white border border-slate-200/80 text-xs text-slate-600 shadow-2xs">
            <span className="font-bold text-slate-800">Fundamentação factual: </span>
            {par.motivo_classificacao}
          </div>

          {/* Comparação dos dois discursos (Lado a Lado no Desktop, Empilhado no Mobile) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 sm:gap-4">
            {/* Discurso Parlamentar 1 */}
            <div className="flex flex-col p-4 rounded-xl bg-blue-50/60 border border-blue-100/80 space-y-2.5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-500 flex-shrink-0" />
                  <p className="text-xs font-bold text-slate-900 truncate">{nomeA}</p>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 flex-shrink-0">
                  <Calendar size={11} />
                  {formatarData(par.discurso_politico1.data_hora_inicio)}
                </span>
              </div>

              {par.discurso_politico1.tipo_discurso && (
                <span className="self-start text-[11px] font-semibold px-2 py-0.5 rounded-md bg-blue-100 text-blue-800">
                  {par.discurso_politico1.tipo_discurso}
                </span>
              )}

              <p className="text-xs text-slate-700 leading-relaxed">
                {par.discurso_politico1.sumario || "Pronunciamento registrado oficialmente em plenário."}
              </p>

              {par.discurso_politico1.url_texto && (
                <a
                  href={par.discurso_politico1.url_texto}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 font-semibold pt-1 mt-auto"
                >
                  Íntegra do discurso na Câmara
                  <ExternalLink size={11} />
                </a>
              )}
            </div>

            {/* Discurso Parlamentar 2 */}
            <div className="flex flex-col p-4 rounded-xl bg-violet-50/60 border border-violet-100/80 space-y-2.5">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <span className="w-2.5 h-2.5 rounded-full bg-violet-500 flex-shrink-0" />
                  <p className="text-xs font-bold text-slate-900 truncate">{nomeB}</p>
                </div>
                <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 flex-shrink-0">
                  <Calendar size={11} />
                  {formatarData(par.discurso_politico2.data_hora_inicio)}
                </span>
              </div>

              {par.discurso_politico2.tipo_discurso && (
                <span className="self-start text-[11px] font-semibold px-2 py-0.5 rounded-md bg-violet-100 text-violet-800">
                  {par.discurso_politico2.tipo_discurso}
                </span>
              )}

              <p className="text-xs text-slate-700 leading-relaxed">
                {par.discurso_politico2.sumario || "Pronunciamento registrado oficialmente em plenário."}
              </p>

              {par.discurso_politico2.url_texto && (
                <a
                  href={par.discurso_politico2.url_texto}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-[11px] text-violet-600 hover:text-violet-800 font-semibold pt-1 mt-auto"
                >
                  Íntegra do discurso na Câmara
                  <ExternalLink size={11} />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </article>
  )
}

export function BlocoComparacaoDiscursos({
  comparacao,
  loading,
  nomeA,
  nomeB,
}: BlocoComparacaoDiscursosProps) {
  const [abaAtiva, setAbaAtiva] = useState<"divergentes" | "convergentes">("divergentes")
  const [categoriaSelecionada, setCategoriaSelecionada] = useState<string | null>(null)
  const [expandidos, setExpandidos] = useState<Record<string, boolean>>({})
  const [limiteExibicao, setLimiteExibicao] = useState(ITENS_POR_PAGINA_INICIAL)

  // Lista base pelo tipo de relação
  const listaBase = useMemo(() => {
    if (!comparacao) return []
    return abaAtiva === "divergentes"
      ? comparacao.discursos_divergentes
      : comparacao.discursos_convergentes
  }, [comparacao, abaAtiva])

  // Contagem dinâmica de categorias para a aba ativa
  const categoriasContagem = useMemo(() => {
    const cont: Record<string, number> = {}
    for (const item of listaBase) {
      const cat = item.categoria || "Atividade em Plenário"
      cont[cat] = (cont[cat] || 0) + 1
    }
    return cont
  }, [listaBase])

  const categoriasDisponiveis = useMemo(() => {
    return Object.keys(categoriasContagem).sort()
  }, [categoriasContagem])

  // Filtra por categoria se houver filtro selecionado
  const listaFiltrada = useMemo(() => {
    if (!categoriaSelecionada) return listaBase
    return listaBase.filter(
      (item) => (item.categoria || "Atividade em Plenário") === categoriaSelecionada
    )
  }, [listaBase, categoriaSelecionada])

  // Lista visível limitada para evitar scroll fatigue
  const listaVisivel = useMemo(() => {
    return listaFiltrada.slice(0, limiteExibicao)
  }, [listaFiltrada, limiteExibicao])

  const toggleExpandir = (chave: string) => {
    setExpandidos((prev) => ({
      ...prev,
      [chave]: !prev[chave],
    }))
  }

  if (loading && !comparacao) {
    return (
      <section
        data-testid="bloco-comparacao-discursos-loading"
        className="section-fade bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm"
      >
        <div className="w-8 h-8 border-[3px] border-slate-200 border-t-blue-500 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-500 font-medium">
          Cruzando pronunciamentos e similaridade semântica dos discursos...
        </p>
      </section>
    )
  }

  if (!comparacao || comparacao.total_pares === 0) {
    return (
      <section
        data-testid="bloco-comparacao-discursos-vazio"
        className="section-fade bg-white rounded-2xl border border-slate-200 p-8 text-center shadow-sm"
      >
        <MessageSquare size={28} className="text-slate-300 mx-auto mb-2" />
        <h3 className="text-sm font-semibold text-slate-700">
          Sem discursos comuns correlacionados
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
          Não foram identificados pronunciamentos oficiais com sobreposição semântica suficiente
          entre ambos os parlamentares no período analisado.
        </p>
      </section>
    )
  }

  return (
    <section
      data-testid="bloco-comparacao-discursos"
      className="section-fade space-y-4"
    >
      {/* Cabeçalho da seção */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-violet-50 flex items-center justify-center text-violet-600">
            <MessageSquare size={18} />
          </div>
          <div>
            <h2 className="display-font text-xl font-bold text-slate-800">
              Confronto de Discursos na Tribuna
            </h2>
            <p className="text-xs text-slate-400">
              Pronunciamentos correlacionados por tema (BAAI/bge-m3 + pgvector)
            </p>
          </div>
        </div>

        {/* Badge Informativo */}
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200 shadow-sm self-start sm:self-auto">
          <Sparkles size={13} className="text-violet-500" />
          {comparacao.total_pares} debates correlacionados
        </span>
      </div>

      {/* Segmented Control Touch-Friendly */}
      <div className="flex bg-slate-100/80 p-1 rounded-xl border border-slate-200/80">
        <button
          type="button"
          data-testid="tab-discursos-divergentes"
          onClick={() => {
            setAbaAtiva("divergentes")
            setCategoriaSelecionada(null)
            setLimiteExibicao(ITENS_POR_PAGINA_INICIAL)
          }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold transition-all min-h-[44px] ${
            abaAtiva === "divergentes"
              ? "bg-white text-amber-900 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
          }`}
        >
          <ArrowLeftRight
            size={14}
            className={abaAtiva === "divergentes" ? "text-amber-600" : "text-slate-400"}
          />
          <span>Discursos Divergentes</span>
          <span
            className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
              abaAtiva === "divergentes"
                ? "bg-amber-100 text-amber-800"
                : "bg-slate-200 text-slate-600"
            }`}
          >
            {comparacao.total_divergentes}
          </span>
        </button>

        <button
          type="button"
          data-testid="tab-discursos-convergentes"
          onClick={() => {
            setAbaAtiva("convergentes")
            setCategoriaSelecionada(null)
            setLimiteExibicao(ITENS_POR_PAGINA_INICIAL)
          }}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold transition-all min-h-[44px] ${
            abaAtiva === "convergentes"
              ? "bg-white text-emerald-900 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
          }`}
        >
          <CheckCircle2
            size={14}
            className={abaAtiva === "convergentes" ? "text-emerald-600" : "text-slate-400"}
          />
          <span>Discursos Parecidos</span>
          <span
            className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
              abaAtiva === "convergentes"
                ? "bg-emerald-100 text-emerald-800"
                : "bg-slate-200 text-slate-600"
            }`}
          >
            {comparacao.total_convergentes}
          </span>
        </button>
      </div>

      {/* Filtros de Categoria (Pílulas com Rolagem Touch no Mobile) */}
      {categoriasDisponiveis.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/90 p-3.5 sm:p-4 shadow-sm space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
            <Layers size={14} className="text-violet-500" />
            <span>Filtrar por Categoria Temática:</span>
          </div>

          <div
            data-testid="carrossel-categorias-discursos"
            className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none -mx-1 px-1 touch-pan-x flex-nowrap sm:flex-wrap"
          >
            <button
              type="button"
              data-testid="pill-categoria-todas"
              onClick={() => {
                setCategoriaSelecionada(null)
                setLimiteExibicao(ITENS_POR_PAGINA_INICIAL)
              }}
              className={`flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border min-h-[38px] ${
                categoriaSelecionada === null
                  ? "bg-violet-600 text-white border-violet-600 shadow-sm"
                  : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
              }`}
            >
              <span>Todas</span>
              <span
                className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                  categoriaSelecionada === null
                    ? "bg-white/20 text-white"
                    : "bg-slate-200 text-slate-600"
                }`}
              >
                {listaBase.length}
              </span>
            </button>

            {categoriasDisponiveis.map((cat) => {
              const isSel = categoriaSelecionada === cat
              const count = categoriasContagem[cat] || 0
              return (
                <button
                  key={cat}
                  type="button"
                  data-testid={`pill-categoria-${cat}`}
                  onClick={() => {
                    setCategoriaSelecionada(isSel ? null : cat)
                    setLimiteExibicao(ITENS_POR_PAGINA_INICIAL)
                  }}
                  className={`flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all border min-h-[38px] ${
                    isSel
                      ? "bg-violet-600 text-white border-violet-600 shadow-sm"
                      : "bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  <span>{cat}</span>
                  <span
                    className={`px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      isSel ? "bg-white/20 text-white" : "bg-slate-200 text-slate-600"
                    }`}
                  >
                    {count}
                  </span>
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* Lista de Discursos Compactos (Anti-Scroll Fatigue) */}
      {listaFiltrada.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-xs text-slate-500 shadow-sm">
          Nenhum discurso encontrado nesta categoria.
        </div>
      ) : (
        <div className="space-y-2.5">
          {listaVisivel.map((par) => {
            const key = `${par.discurso_politico1.id}-${par.discurso_politico2.id}`
            return (
              <CardDebateDiscurso
                key={key}
                par={par}
                nomeA={nomeA}
                nomeB={nomeB}
                expandido={Boolean(expandidos[key])}
                onToggle={() => toggleExpandir(key)}
              />
            )
          })}

          {/* Botões Anti-Fatigue: Mostrar mais / Recolher */}
          {listaFiltrada.length > ITENS_POR_PAGINA_INICIAL && (
            <div className="flex items-center justify-center gap-3 pt-2">
              {limiteExibicao < listaFiltrada.length ? (
                <button
                  type="button"
                  data-testid="btn-mostrar-mais-discursos"
                  onClick={() => setLimiteExibicao((prev) => prev + 6)}
                  className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-white border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 hover:border-slate-300 shadow-sm transition-all min-h-[44px]"
                >
                  <ChevronDown size={15} />
                  <span>
                    Ver mais debates ({listaFiltrada.length - limiteExibicao} restantes)
                  </span>
                </button>
              ) : (
                <button
                  type="button"
                  data-testid="btn-recolher-discursos"
                  onClick={() => setLimiteExibicao(ITENS_POR_PAGINA_INICIAL)}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100 text-xs font-semibold text-slate-600 hover:bg-slate-200 transition-colors min-h-[44px]"
                >
                  <ChevronUp size={15} />
                  <span>Recolher debates</span>
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
