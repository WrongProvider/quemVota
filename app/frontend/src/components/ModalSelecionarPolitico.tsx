import { useState, useEffect, useRef } from "react"
import { X, Search, Loader2, MapPin, Users } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { usePoliticos } from "../hooks/usePoliticos"
import { useDebounce } from "../hooks/useDebounce"
import { nomeParaSlug } from "../api/politicos.api"
import type { Politico } from "../api/politicos.api"

const PATH_FOTOS = "/fotos_politicos/"

interface Props {
  politicoAtualId: number
  politicoAtualSlug: string
  onClose: () => void
}

/**
 * Modal que permite buscar e selecionar um segundo político para comparação.
 * Usa usePoliticos + useDebounce — sem fetch manual, sem estado de loading próprio.
 * Ao selecionar, navega para /comparar/:slugAtual/:slugEscolhido
 */
export default function ModalSelecionarPolitico({
  politicoAtualId,
  politicoAtualSlug,
  onClose,
}: Props) {
  const navigate  = useNavigate()
  const inputRef  = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState("")
  const queryDebounced    = useDebounce(query, 400)

  // Só dispara a query quando o usuário digitou algo com pelo menos 2 chars
  const { data, isFetching } = usePoliticos(
    queryDebounced.trim().length >= 2
      ? { q: queryDebounced.trim(), limit: 8 }
      : undefined,
  )

  // Filtra o político atual da lista de resultados
  const resultados: Politico[] = (data ?? []).filter((p) => p.id !== politicoAtualId)

  // Foca o input ao abrir
  useEffect(() => {
    const t = setTimeout(() => inputRef.current?.focus(), 80)
    return () => clearTimeout(t)
  }, [])

  // Fecha com ESC
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose() }
    window.addEventListener("keydown", onKey)
    return () => window.removeEventListener("keydown", onKey)
  }, [onClose])

  const selecionarPolitico = (p: Politico) => {
    onClose()
    navigate(`/comparar/${politicoAtualSlug}/${nomeParaSlug(p.nome)}`)
  }

  const buscando = isFetching && queryDebounced.trim().length >= 2

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="pointer-events-auto w-full max-w-md bg-white rounded-2xl shadow-2xl border border-slate-100 overflow-hidden"
          style={{ animation: "modalPop 0.22s cubic-bezier(0.34, 1.56, 0.64, 1) both" }}
        >
          <style>{`
            @keyframes modalPop {
              from { opacity: 0; transform: scale(0.94) translateY(8px); }
              to   { opacity: 1; transform: scale(1) translateY(0); }
            }
          `}</style>

          {/* Header */}
          <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
            <div>
              <h2 className="font-semibold text-slate-800 text-base">
                Comparar com outro parlamentar
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">Busque pelo nome do político</p>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
            >
              <X size={16} />
            </button>
          </div>

          {/* Search input */}
          <div className="px-5 py-3 border-b border-slate-100">
            <div className="relative">
              <Search
                size={15}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
              />
              <input
                ref={inputRef}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ex: Nikolas Ferreira, Gleisi Hoffmann…"
                className="w-full pl-9 pr-9 py-2.5 text-sm text-slate-700 bg-slate-50 rounded-xl border border-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-400 transition placeholder:text-slate-400"
              />
              {buscando && (
                <Loader2
                  size={14}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-blue-400 animate-spin"
                />
              )}
            </div>
          </div>

          {/* Results */}
          <div className="max-h-72 overflow-y-auto">
            {/* Estado inicial */}
            {!query.trim() && (
              <div className="px-5 py-8 text-center">
                <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-3">
                  <Search size={18} className="text-blue-400" />
                </div>
                <p className="text-sm text-slate-400">Digite o nome para buscar</p>
              </div>
            )}

            {/* Query curta demais */}
            {query.trim().length > 0 && query.trim().length < 2 && (
              <div className="px-5 py-6 text-center">
                <p className="text-sm text-slate-400">Digite ao menos 2 caracteres…</p>
              </div>
            )}

            {/* Sem resultados */}
            {queryDebounced.trim().length >= 2 && !buscando && resultados.length === 0 && (
              <div className="px-5 py-8 text-center">
                <p className="text-sm text-slate-400">Nenhum parlamentar encontrado</p>
              </div>
            )}

            {/* Lista de resultados */}
            {resultados.map((p) => (
              <button
                key={p.id}
                onClick={() => selecionarPolitico(p)}
                className="w-full flex items-center gap-3 px-5 py-3 hover:bg-blue-50 transition-colors text-left border-b border-slate-50 last:border-0 group"
              >
                {/* Foto */}
                <div className="w-10 h-10 rounded-xl overflow-hidden flex-shrink-0 ring-1 ring-slate-100">
                  <img
                    src={`${PATH_FOTOS}${p.id}.jpg`}
                    alt={p.nome}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      ;(e.target as HTMLImageElement).src = `https://ui-avatars.com/api/?name=${encodeURIComponent(p.nome)}&background=e2e8f0&color=64748b&size=80`
                    }}
                  />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-800 truncate group-hover:text-blue-700 transition-colors">
                    {p.nome}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {p.sigla_partido && (
                      <span className="flex items-center gap-0.5 text-[11px] text-slate-400">
                        <Users size={10} />
                        {p.sigla_partido}
                      </span>
                    )}
                    {p.sigla_uf && (
                      <span className="flex items-center gap-0.5 text-[11px] text-slate-400">
                        <MapPin size={10} />
                        {p.sigla_uf}
                      </span>
                    )}
                  </div>
                </div>

                <span className="text-xs text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity font-medium flex-shrink-0 whitespace-nowrap">
                  Comparar →
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </>
  )
}