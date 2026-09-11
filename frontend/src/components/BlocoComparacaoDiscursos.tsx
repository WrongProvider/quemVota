import { useState } from "react"
import {
  MessageSquare,
  ArrowLeftRight,
  CheckCircle2,
  Calendar,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from "lucide-react"
import type { ComparacaoDiscursosResponse, ParDiscursoComparado } from "../api/politicos.api"

interface BlocoComparacaoDiscursosProps {
  readonly comparacao?: ComparacaoDiscursosResponse | null
  readonly loading: boolean
  readonly nomeA: string
  readonly nomeB: string
}

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

function CardParDiscurso({
  par,
  nomeA,
  nomeB,
}: {
  readonly par: ParDiscursoComparado
  readonly nomeA: string
  readonly nomeB: string
}) {
  const [expandido, setExpandido] = useState(false)
  const isConvergente = par.tipo_relacao === "convergente"
  const simPercent = Math.round(par.similaridade_semantica * 100)

  return (
    <article
      data-testid="card-par-discurso"
      className="bg-white rounded-2xl border border-slate-200/90 p-4 sm:p-5 shadow-sm hover:shadow transition-shadow space-y-4"
    >
      {/* Cabeçalho do Par */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-100">
        <div className="flex flex-wrap items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 text-slate-700">
            <Sparkles size={13} className="text-amber-500" />
            {par.tema_ou_materia}
          </span>
          <span
            className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${
              isConvergente
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200/60"
                : "bg-amber-50 text-amber-800 border border-amber-200/60"
            }`}
          >
            {isConvergente ? (
              <>
                <CheckCircle2 size={12} className="text-emerald-600" />
                Discurso Parecido
              </>
            ) : (
              <>
                <ArrowLeftRight size={12} className="text-amber-600" />
                Discurso Divergente
              </>
            )}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="font-medium text-slate-600">{simPercent}% similaridade</span>
        </div>
      </div>

      {/* Motivo factual da classificação */}
      <div className="px-3 py-2 rounded-xl bg-slate-50/80 border border-slate-100 text-xs text-slate-600">
        <span className="font-semibold text-slate-700">Fundamentação: </span>
        {par.motivo_classificacao}
      </div>

      {/* Comparação dos dois discursos (Lado a Lado no Desktop, Empilhado no Mobile) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Discurso Parlamentar 1 */}
        <div className="flex flex-col p-3.5 rounded-xl bg-blue-50/40 border border-blue-100/70 space-y-2.5">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500 flex-shrink-0" />
              <p className="text-xs font-bold text-slate-800 truncate">{nomeA}</p>
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 flex-shrink-0">
              <Calendar size={11} />
              {formatarData(par.discurso_politico1.data_hora_inicio)}
            </span>
          </div>

          {par.discurso_politico1.tipo_discurso && (
            <span className="self-start text-[11px] font-medium px-2 py-0.5 rounded-md bg-blue-100/70 text-blue-700">
              {par.discurso_politico1.tipo_discurso}
            </span>
          )}

          <p className="text-xs text-slate-700 leading-relaxed">
            {expandido || !par.discurso_politico1.sumario || par.discurso_politico1.sumario.length <= 180
              ? par.discurso_politico1.sumario || "Pronunciamento registrado em plenário."
              : `${par.discurso_politico1.sumario.slice(0, 180)}...`}
          </p>

          {par.discurso_politico1.url_texto && (
            <a
              href={par.discurso_politico1.url_texto}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] text-blue-600 hover:text-blue-800 font-medium pt-1 mt-auto"
            >
              Íntegra na Câmara
              <ExternalLink size={10} />
            </a>
          )}
        </div>

        {/* Discurso Parlamentar 2 */}
        <div className="flex flex-col p-3.5 rounded-xl bg-violet-50/40 border border-violet-100/70 space-y-2.5">
          <div className="flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="w-2.5 h-2.5 rounded-full bg-violet-500 flex-shrink-0" />
              <p className="text-xs font-bold text-slate-800 truncate">{nomeB}</p>
            </div>
            <span className="inline-flex items-center gap-1 text-[11px] text-slate-500 flex-shrink-0">
              <Calendar size={11} />
              {formatarData(par.discurso_politico2.data_hora_inicio)}
            </span>
          </div>

          {par.discurso_politico2.tipo_discurso && (
            <span className="self-start text-[11px] font-medium px-2 py-0.5 rounded-md bg-violet-100/70 text-violet-700">
              {par.discurso_politico2.tipo_discurso}
            </span>
          )}

          <p className="text-xs text-slate-700 leading-relaxed">
            {expandido || !par.discurso_politico2.sumario || par.discurso_politico2.sumario.length <= 180
              ? par.discurso_politico2.sumario || "Pronunciamento registrado em plenário."
              : `${par.discurso_politico2.sumario.slice(0, 180)}...`}
          </p>

          {par.discurso_politico2.url_texto && (
            <a
              href={par.discurso_politico2.url_texto}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-[11px] text-violet-600 hover:text-violet-800 font-medium pt-1 mt-auto"
            >
              Íntegra na Câmara
              <ExternalLink size={10} />
            </a>
          )}
        </div>
      </div>

      {/* Botão de expansão para sumários longos */}
      {((par.discurso_politico1.sumario && par.discurso_politico1.sumario.length > 180) ||
        (par.discurso_politico2.sumario && par.discurso_politico2.sumario.length > 180)) && (
        <div className="flex justify-center pt-1">
          <button
            type="button"
            onClick={() => setExpandido(!expandido)}
            className="inline-flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-slate-800 py-1 px-3 rounded-lg hover:bg-slate-100 transition-colors min-h-[44px]"
          >
            {expandido ? (
              <>
                <ChevronUp size={14} />
                Recolher sumários
              </>
            ) : (
              <>
                <ChevronDown size={14} />
                Ler sumários completos
              </>
            )}
          </button>
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

  const lista =
    abaAtiva === "divergentes"
      ? comparacao.discursos_divergentes
      : comparacao.discursos_convergentes

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
              Pronunciamentos sobre os mesmos temas e matérias legislativas (BAAI/bge-m3 + pgvector)
            </p>
          </div>
        </div>

        {/* Badge Informativo */}
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200 shadow-sm self-start sm:self-auto">
          <Sparkles size={13} className="text-violet-500" />
          {comparacao.total_pares} pares correlacionados
        </span>
      </div>

      {/* Segmented Control Touch-Friendly */}
      <div className="flex bg-slate-100/80 p-1 rounded-xl border border-slate-200/80">
        <button
          type="button"
          data-testid="tab-discursos-divergentes"
          onClick={() => setAbaAtiva("divergentes")}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold transition-all min-h-[44px] ${
            abaAtiva === "divergentes"
              ? "bg-white text-amber-900 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
          }`}
        >
          <ArrowLeftRight size={14} className={abaAtiva === "divergentes" ? "text-amber-600" : "text-slate-400"} />
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
          onClick={() => setAbaAtiva("convergentes")}
          className={`flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg text-xs font-semibold transition-all min-h-[44px] ${
            abaAtiva === "convergentes"
              ? "bg-white text-emerald-900 shadow-sm border border-slate-200/60"
              : "text-slate-600 hover:text-slate-900 hover:bg-white/50"
          }`}
        >
          <CheckCircle2 size={14} className={abaAtiva === "convergentes" ? "text-emerald-600" : "text-slate-400"} />
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

      {/* Lista de Discursos Comparados */}
      {lista.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-xs text-slate-500">
          Nenhum discurso registrado nesta categoria para o par de parlamentares.
        </div>
      ) : (
        <div className="space-y-3">
          {lista.map((par) => (
            <CardParDiscurso
              key={`${par.discurso_politico1.id}-${par.discurso_politico2.id}`}
              par={par}
              nomeA={nomeA}
              nomeB={nomeB}
            />
          ))}
        </div>
      )}
    </section>
  )
}
