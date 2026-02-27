/**
 * ProjetosVotacoes.tsx — Página de busca de Proposições e Votações.
 *
 * Duas abas:
 *   "Projetos"  → lista proposições com filtros (q, tipo, ano)
 *   "Votações"  → lista votações com filtros (ano, resultado, tipo)
 *
 * Ao clicar em uma proposição → painel lateral com detalhe + tramitação
 * Ao clicar em uma votação    → painel lateral com detalhe + orientações
 */

import { useState, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Search,
  FileText,
  Vote,
  ChevronRight,
  X,
  Loader2,
  CheckCircle2,
  XCircle,
  MinusCircle,
  ExternalLink,
  Users,
  Calendar,
  Tag,
  ArrowRight,
  Clock,
  Building,
} from "lucide-react"
import {
  useProposicoes,
  useProposicao,
  useVotacoesDaProposicao,
  useVotacoes,
  useVotacao,
} from "../hooks/useProposicoes"
import type {
  ProposicaoResponse,
  VotacaoResponse,
  ProposicoesFiltros,
  VotacoesFiltros,
} from "../api/proposicoes.api"

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

const TIPOS_PROPOSICAO = ["PL", "PEC", "MPV", "PDC", "PRC", "PLP", "PLC"]

const ANOS = Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i)

function formatarData(iso: string | null | undefined): string {
  if (!iso) return "—"
  return new Date(iso).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
}

function truncar(texto: string | null | undefined, max = 160): string {
  if (!texto) return "—"
  return texto.length > max ? texto.slice(0, max) + "…" : texto
}

// ─────────────────────────────────────────────────────────────────────────────
// Badge de tipo de proposição
// ─────────────────────────────────────────────────────────────────────────────

const TIPO_COLORS: Record<string, string> = {
  PEC: "bg-purple-50 text-purple-700 border-purple-200",
  PL:  "bg-blue-50 text-blue-700 border-blue-200",
  MPV: "bg-amber-50 text-amber-700 border-amber-200",
  PDC: "bg-slate-50 text-slate-600 border-slate-200",
  PRC: "bg-slate-50 text-slate-600 border-slate-200",
  PLP: "bg-emerald-50 text-emerald-700 border-emerald-200",
  PLC: "bg-emerald-50 text-emerald-700 border-emerald-200",
}

function TipoBadge({ sigla }: { sigla: string | null | undefined }) {
  if (!sigla) return null
  const cls = TIPO_COLORS[sigla] ?? "bg-slate-50 text-slate-600 border-slate-200"
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-md border text-[11px] font-semibold ${cls}`}>
      {sigla}
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Badge de resultado da votação
// ─────────────────────────────────────────────────────────────────────────────

function ResultadoBadge({ aprovacao }: { aprovacao: 1 | 0 | -1 | null }) {
  if (aprovacao === 1) return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 border border-emerald-200 text-emerald-700 text-[11px] font-semibold">
      <CheckCircle2 size={11} /> Aprovada
    </span>
  )
  if (aprovacao === 0) return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-red-50 border border-red-200 text-red-600 text-[11px] font-semibold">
      <XCircle size={11} /> Rejeitada
    </span>
  )
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200 text-slate-500 text-[11px] font-semibold">
      <MinusCircle size={11} /> Indefinido
    </span>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Estado vazio / erro / loading
// ─────────────────────────────────────────────────────────────────────────────

function EstadoVazio({ mensagem }: { mensagem: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center text-slate-400">
      <FileText size={36} className="mb-3 opacity-30" />
      <p className="text-sm">{mensagem}</p>
    </div>
  )
}

function EstadoLoading() {
  return (
    <div className="flex items-center justify-center py-20 gap-3 text-slate-400">
      <Loader2 size={20} className="animate-spin" />
      <span className="text-sm">Carregando...</span>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de Proposição (listagem)
// ─────────────────────────────────────────────────────────────────────────────

function CardProposicao({
  proposicao,
  selecionada,
  onClick,
}: {
  proposicao: ProposicaoResponse
  selecionada: boolean
  onClick: () => void
}) {
  const autorPrincipal = proposicao.autores.find((a) => a.proponente) ?? proposicao.autores[0]

  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-5 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors group ${
        selecionada ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
      }`}
    >
      {/* Linha 1: tipo + número + ano + data */}
      <div className="flex items-center gap-2 mb-2">
        <TipoBadge sigla={proposicao.sigla_tipo} />
        <span className="text-xs font-mono text-slate-500">
          {proposicao.numero}/{proposicao.ano}
        </span>
        {proposicao.data_apresentacao && (
          <span className="ml-auto text-[11px] text-slate-400 flex-shrink-0">
            {formatarData(proposicao.data_apresentacao)}
          </span>
        )}
      </div>

      {/* Ementa */}
      <p className="text-sm text-slate-700 leading-snug mb-2">
        {truncar(proposicao.ementa)}
      </p>

      {/* Linha 3: autor + temas */}
      <div className="flex items-center gap-3 flex-wrap">
        {autorPrincipal && (
          <span className="inline-flex items-center gap-1 text-[11px] text-slate-500">
            <Users size={10} />
            {autorPrincipal.nome}
          </span>
        )}
        {proposicao.temas.slice(0, 2).map((t) => (
          <span key={t.id} className="inline-flex items-center gap-1 text-[11px] text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded">
            <Tag size={9} /> {t.tema}
          </span>
        ))}
        <ChevronRight
          size={14}
          className={`ml-auto text-slate-300 group-hover:text-blue-500 transition-colors flex-shrink-0 ${selecionada ? "text-blue-500" : ""}`}
        />
      </div>
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Painel de detalhe de Proposição
// ─────────────────────────────────────────────────────────────────────────────

function PainelProposicao({
  id,
  onClose,
}: {
  id: number
  onClose: () => void
}) {
  const { data: prop, isLoading } = useProposicao(id)
  const { data: votacoes = [] } = useVotacoesDaProposicao(id)

  return (
    <motion.div
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 40, opacity: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="flex flex-col h-full overflow-hidden"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-start justify-between gap-3 flex-shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          {prop && <TipoBadge sigla={prop.sigla_tipo} />}
          {prop && (
            <span className="text-sm font-mono text-slate-500 font-medium">
              {prop.numero}/{prop.ano}
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors flex-shrink-0"
        >
          <X size={16} />
        </button>
      </div>

      {/* Conteúdo com scroll */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
        {isLoading ? (
          <EstadoLoading />
        ) : !prop ? (
          <EstadoVazio mensagem="Proposição não encontrada." />
        ) : (
          <>
            {/* Ementa */}
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Ementa</p>
              <p className="text-sm text-slate-700 leading-relaxed">{prop.ementa ?? "—"}</p>
              {prop.ementa_detalhada && prop.ementa_detalhada !== prop.ementa && (
                <p className="text-xs text-slate-500 mt-2 leading-relaxed">{prop.ementa_detalhada}</p>
              )}
            </div>

            {/* Autores */}
            {prop.autores.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  Autores
                </p>
                <div className="space-y-1.5">
                  {prop.autores.map((a, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-sm text-slate-700">{a.nome}</span>
                      {a.proponente && (
                        <span className="text-[10px] bg-blue-50 text-blue-600 border border-blue-100 px-1.5 py-0.5 rounded font-medium">
                          Proponente
                        </span>
                      )}
                      {a.tipo && (
                        <span className="text-[10px] text-slate-400">{a.tipo}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Temas */}
            {prop.temas.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  Temas
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {prop.temas.map((t) => (
                    <span key={t.id} className="text-[11px] bg-slate-100 text-slate-600 px-2 py-1 rounded-md">
                      {t.tema}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Votações da proposição */}
            {votacoes.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">
                  Votações ({votacoes.length})
                </p>
                <div className="space-y-2">
                  {votacoes.map((v) => (
                    <div
                      key={v.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100"
                    >
                      <div>
                        <p className="text-xs text-slate-600 font-medium">{formatarData(v.data)}</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">{v.tipo_votacao ?? "—"}</p>
                      </div>
                      <ResultadoBadge aprovacao={v.aprovacao} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tramitação */}
            {prop.tramitacoes.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
                  Tramitação ({prop.tramitacoes.length} etapas)
                </p>
                <div className="relative">
                  {/* Linha vertical da timeline */}
                  <div className="absolute left-[7px] top-2 bottom-2 w-px bg-slate-200" />

                  <div className="space-y-4">
                    {[...prop.tramitacoes].reverse().map((t, i) => (
                      <div key={t.id} className="flex gap-3 relative">
                        {/* Ponto da timeline */}
                        <div className={`w-3.5 h-3.5 rounded-full border-2 flex-shrink-0 mt-0.5 z-10 ${
                          i === 0
                            ? "bg-blue-500 border-blue-500"
                            : "bg-white border-slate-300"
                        }`} />
                        <div className="flex-1 pb-1">
                          {/* Órgão + data */}
                          <div className="flex items-center gap-2 mb-1 flex-wrap">
                            {t.sigla_orgao && (
                              <span className="text-[11px] font-semibold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                                {t.sigla_orgao}
                              </span>
                            )}
                            <span className="text-[11px] text-slate-400 flex items-center gap-1">
                              <Clock size={9} /> {formatarData(t.data_hora)}
                            </span>
                          </div>
                          {/* Situação */}
                          {t.descricao_situacao && (
                            <p className="text-xs font-medium text-slate-700">{t.descricao_situacao}</p>
                          )}
                          {/* Despacho */}
                          {t.despacho && (
                            <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                              {truncar(t.despacho, 120)}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Link externo */}
            {prop.url_inteiro_teor && (
              <a
                href={prop.url_inteiro_teor}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                <ExternalLink size={12} /> Ver inteiro teor
              </a>
            )}
          </>
        )}
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Card de Votação (listagem)
// ─────────────────────────────────────────────────────────────────────────────

function CardVotacao({
  votacao,
  selecionada,
  onClick,
}: {
  votacao: VotacaoResponse
  selecionada: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`w-full text-left px-5 py-4 border-b border-slate-100 hover:bg-slate-50 transition-colors group ${
        selecionada ? "bg-blue-50 border-l-2 border-l-blue-500" : ""
      }`}
    >
      {/* Linha 1: tipo + data + resultado */}
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        {votacao.proposicao_sigla && <TipoBadge sigla={votacao.proposicao_sigla} />}
        {votacao.proposicao_numero && (
          <span className="text-xs font-mono text-slate-500">
            {votacao.proposicao_numero}/{votacao.proposicao_ano}
          </span>
        )}
        <span className="ml-auto flex items-center gap-2 flex-shrink-0">
          <ResultadoBadge aprovacao={votacao.aprovacao} />
        </span>
      </div>

      {/* Ementa da proposição */}
      <p className="text-sm text-slate-700 leading-snug mb-2">
        {truncar(votacao.proposicao_ementa ?? votacao.descricao)}
      </p>

      {/* Linha 3: data + órgão */}
      <div className="flex items-center gap-3 text-[11px] text-slate-400">
        <span className="flex items-center gap-1">
          <Calendar size={10} /> {formatarData(votacao.data)}
        </span>
        {votacao.sigla_orgao && (
          <span className="flex items-center gap-1">
            <Building size={10} /> {votacao.sigla_orgao}
          </span>
        )}
        <ChevronRight
          size={14}
          className={`ml-auto text-slate-300 group-hover:text-blue-500 transition-colors flex-shrink-0 ${selecionada ? "text-blue-500" : ""}`}
        />
      </div>
    </button>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Painel de detalhe de Votação
// ─────────────────────────────────────────────────────────────────────────────

const VOTO_COLORS: Record<string, string> = {
  "Sim":        "text-emerald-700 bg-emerald-50 border-emerald-200",
  "Não":        "text-red-600 bg-red-50 border-red-200",
  "Libera":     "text-amber-700 bg-amber-50 border-amber-200",
  "Obstrução":  "text-slate-600 bg-slate-50 border-slate-200",
  "Abstenção":  "text-slate-500 bg-slate-50 border-slate-200",
}

function PainelVotacao({
  id,
  onClose,
}: {
  id: number
  onClose: () => void
}) {
  const { data: votacao, isLoading } = useVotacao(id)

  return (
    <motion.div
      initial={{ x: 40, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      exit={{ x: 40, opacity: 0 }}
      transition={{ duration: 0.22, ease: "easeOut" }}
      className="flex flex-col h-full overflow-hidden"
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-3 flex-shrink-0">
        <div className="flex items-center gap-2 flex-wrap">
          {votacao && <TipoBadge sigla={votacao.proposicao_sigla} />}
          {votacao?.proposicao_numero && (
            <span className="text-sm font-mono text-slate-500">
              {votacao.proposicao_numero}/{votacao.proposicao_ano}
            </span>
          )}
          {votacao && <ResultadoBadge aprovacao={votacao.aprovacao} />}
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors flex-shrink-0"
        >
          <X size={16} />
        </button>
      </div>

      {/* Conteúdo com scroll */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
        {isLoading ? (
          <EstadoLoading />
        ) : !votacao ? (
          <EstadoVazio mensagem="Votação não encontrada." />
        ) : (
          <>
            {/* Ementa */}
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">Proposição</p>
              <p className="text-sm text-slate-700 leading-relaxed">
                {votacao.proposicao_ementa ?? votacao.descricao ?? "—"}
              </p>
            </div>

            {/* Meta */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Data</p>
                <p className="text-sm font-medium text-slate-700">{formatarData(votacao.data)}</p>
              </div>
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Tipo</p>
                <p className="text-sm font-medium text-slate-700">{votacao.tipo_votacao ?? "—"}</p>
              </div>
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Órgão</p>
                <p className="text-sm font-medium text-slate-700">{votacao.sigla_orgao ?? "—"}</p>
              </div>
              <div className="bg-slate-50 rounded-xl p-3 border border-slate-100">
                <p className="text-[10px] text-slate-400 uppercase tracking-wide mb-1">Resultado</p>
                <ResultadoBadge aprovacao={votacao.aprovacao} />
              </div>
            </div>

            {/* Orientações por partido */}
            {votacao.orientacoes.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">
                  Orientação dos partidos ({votacao.orientacoes.length})
                </p>
                <div className="space-y-1.5">
                  {votacao.orientacoes.map((o, i) => {
                    const cls = VOTO_COLORS[o.orientacao_voto ?? ""] ?? "text-slate-600 bg-slate-50 border-slate-200"
                    return (
                      <div
                        key={i}
                        className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-50 border border-slate-100"
                      >
                        <span className="text-sm font-semibold text-slate-700">
                          {o.sigla_partido_bloco ?? "—"}
                        </span>
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${cls}`}>
                          {o.orientacao_voto ?? "—"}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Filtros — Proposições
// ─────────────────────────────────────────────────────────────────────────────

function FiltrosProposicoes({
  filtros,
  onChange,
}: {
  filtros: ProposicoesFiltros
  onChange: (f: ProposicoesFiltros) => void
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Busca por texto */}
      <div className="relative flex-1 min-w-[200px]">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Buscar na ementa..."
          value={filtros.q ?? ""}
          onChange={(e) => onChange({ ...filtros, q: e.target.value || undefined, offset: 0 })}
          className="w-full pl-9 pr-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all"
        />
      </div>

      {/* Tipo */}
      <select
        value={filtros.sigla_tipo ?? ""}
        onChange={(e) => onChange({ ...filtros, sigla_tipo: e.target.value || undefined, offset: 0 })}
        className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
      >
        <option value="">Todos os tipos</option>
        {TIPOS_PROPOSICAO.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      {/* Ano */}
      <select
        value={filtros.ano ?? ""}
        onChange={(e) => onChange({ ...filtros, ano: e.target.value ? Number(e.target.value) : undefined, offset: 0 })}
        className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
      >
        <option value="">Todos os anos</option>
        {ANOS.map((a) => (
          <option key={a} value={a}>{a}</option>
        ))}
      </select>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Filtros — Votações
// ─────────────────────────────────────────────────────────────────────────────

function FiltrosVotacoes({
  filtros,
  onChange,
}: {
  filtros: VotacoesFiltros
  onChange: (f: VotacoesFiltros) => void
}) {
  return (
    <div className="flex items-center gap-2 flex-wrap">
      {/* Tipo */}
      <select
        value={filtros.sigla_tipo ?? ""}
        onChange={(e) => onChange({ ...filtros, sigla_tipo: e.target.value || undefined, offset: 0 })}
        className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
      >
        <option value="">Todos os tipos</option>
        {TIPOS_PROPOSICAO.map((t) => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      {/* Ano */}
      <select
        value={filtros.ano ?? ""}
        onChange={(e) => onChange({ ...filtros, ano: e.target.value ? Number(e.target.value) : undefined, offset: 0 })}
        className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
      >
        <option value="">Todos os anos</option>
        {ANOS.map((a) => (
          <option key={a} value={a}>{a}</option>
        ))}
      </select>

      {/* Resultado */}
      <select
        value={filtros.aprovacao ?? ""}
        onChange={(e) => {
          const v = e.target.value
          onChange({
            ...filtros,
            aprovacao: v === "" ? undefined : (Number(v) as 1 | 0 | -1),
            offset: 0,
          })
        }}
        className="text-sm border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-400 transition-all text-slate-600"
      >
        <option value="">Todos os resultados</option>
        <option value="1">Aprovadas</option>
        <option value="0">Rejeitadas</option>
        <option value="-1">Indefinido</option>
      </select>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Paginação
// ─────────────────────────────────────────────────────────────────────────────

function Paginacao({
  offset,
  limit,
  total,
  onChange,
}: {
  offset: number
  limit: number
  total: number
  onChange: (offset: number) => void
}) {
  const pagina = Math.floor(offset / limit) + 1
  const temAnterior = offset > 0
  const temProxima = total === limit // se retornou limite cheio, provavelmente tem mais

  if (!temAnterior && !temProxima) return null

  return (
    <div className="flex items-center justify-between px-5 py-3 border-t border-slate-100 bg-slate-50/50">
      <button
        disabled={!temAnterior}
        onClick={() => onChange(Math.max(0, offset - limit))}
        className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1"
      >
        ← Anterior
      </button>
      <span className="text-xs text-slate-400">Página {pagina}</span>
      <button
        disabled={!temProxima}
        onClick={() => onChange(offset + limit)}
        className="text-xs text-slate-500 hover:text-slate-700 disabled:opacity-30 disabled:cursor-not-allowed font-medium flex items-center gap-1"
      >
        Próxima <ArrowRight size={12} />
      </button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Componente principal
// ─────────────────────────────────────────────────────────────────────────────

type Aba = "projetos" | "votacoes"

export default function ProjetosVotacoes() {
  const [aba, setAba] = useState<Aba>("projetos")

  // Estado de filtros — cada aba tem o seu
  const [filtrosProposicoes, setFiltrosProposicoes] = useState<ProposicoesFiltros>({ limit: 20, offset: 0 })
  const [filtrosVotacoes, setFiltrosVotacoes] = useState<VotacoesFiltros>({ limit: 20, offset: 0 })

  // Item selecionado para o painel lateral
  const [proposicaoSelecionada, setProposicaoSelecionada] = useState<number | null>(null)
  const [votacaoSelecionada, setVotacaoSelecionada] = useState<number | null>(null)

  // Fecha painel ao trocar de aba
  const handleAba = useCallback((novaAba: Aba) => {
    setAba(novaAba)
    setProposicaoSelecionada(null)
    setVotacaoSelecionada(null)
  }, [])

  // Queries
  const { data: proposicoes = [], isLoading: loadingProposicoes } = useProposicoes(filtrosProposicoes)
  const { data: votacoes = [], isLoading: loadingVotacoes } = useVotacoes(filtrosVotacoes)

  const painelAberto = proposicaoSelecionada !== null || votacaoSelecionada !== null

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }} className="min-h-screen bg-gray-50">

      {/* ── Cabeçalho da página ── */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <p className="text-xs font-semibold tracking-widest uppercase text-blue-600 mb-2">
            Legislativo
          </p>
          <h1
            style={{ fontFamily: "'Fraunces', serif" }}
            className="text-3xl font-bold text-slate-900 mb-1"
          >
            Projetos e Votações
          </h1>
          <p className="text-slate-500 text-sm">
            Pesquise proposições em tramitação e votações realizadas na Câmara dos Deputados.
          </p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className={`flex gap-6 transition-all duration-300 ${painelAberto ? "" : ""}`}>

          {/* ── Coluna principal ── */}
          <div className="flex-1 min-w-0">
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">

              {/* Abas */}
              <div className="flex border-b border-slate-200">
                <button
                  onClick={() => handleAba("projetos")}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-semibold transition-colors border-b-2 -mb-px ${
                    aba === "projetos"
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-slate-500 hover:text-slate-700"
                  }`}
                >
                  <FileText size={15} /> Projetos
                </button>
                <button
                  onClick={() => handleAba("votacoes")}
                  className={`flex items-center gap-2 px-6 py-4 text-sm font-semibold transition-colors border-b-2 -mb-px ${
                    aba === "votacoes"
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-slate-500 hover:text-slate-700"
                  }`}
                >
                  <Vote size={15} /> Votações
                </button>
              </div>

              {/* Filtros */}
              <div className="px-5 py-4 border-b border-slate-100 bg-slate-50/50">
                {aba === "projetos" ? (
                  <FiltrosProposicoes filtros={filtrosProposicoes} onChange={setFiltrosProposicoes} />
                ) : (
                  <FiltrosVotacoes filtros={filtrosVotacoes} onChange={setFiltrosVotacoes} />
                )}
              </div>

              {/* Lista */}
              <AnimatePresence mode="wait">
                <motion.div
                  key={aba}
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={{ duration: 0.15 }}
                >
                  {aba === "projetos" ? (
                    loadingProposicoes ? (
                      <EstadoLoading />
                    ) : proposicoes.length === 0 ? (
                      <EstadoVazio mensagem="Nenhuma proposição encontrada com os filtros selecionados." />
                    ) : (
                      <>
                        {proposicoes.map((p) => (
                          <CardProposicao
                            key={p.id}
                            proposicao={p}
                            selecionada={proposicaoSelecionada === p.id}
                            onClick={() => setProposicaoSelecionada(
                              proposicaoSelecionada === p.id ? null : p.id
                            )}
                          />
                        ))}
                        <Paginacao
                          offset={filtrosProposicoes.offset ?? 0}
                          limit={filtrosProposicoes.limit ?? 20}
                          total={proposicoes.length}
                          onChange={(o) => setFiltrosProposicoes((f) => ({ ...f, offset: o }))}
                        />
                      </>
                    )
                  ) : (
                    loadingVotacoes ? (
                      <EstadoLoading />
                    ) : votacoes.length === 0 ? (
                      <EstadoVazio mensagem="Nenhuma votação encontrada com os filtros selecionados." />
                    ) : (
                      <>
                        {votacoes.map((v) => (
                          <CardVotacao
                            key={v.id}
                            votacao={v}
                            selecionada={votacaoSelecionada === v.id}
                            onClick={() => setVotacaoSelecionada(
                              votacaoSelecionada === v.id ? null : v.id
                            )}
                          />
                        ))}
                        <Paginacao
                          offset={filtrosVotacoes.offset ?? 0}
                          limit={filtrosVotacoes.limit ?? 20}
                          total={votacoes.length}
                          onChange={(o) => setFiltrosVotacoes((f) => ({ ...f, offset: o }))}
                        />
                      </>
                    )
                  )}
                </motion.div>
              </AnimatePresence>
            </div>
          </div>

          {/* ── Painel lateral de detalhe ── */}
          <AnimatePresence>
            {painelAberto && (
              <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 420, opacity: 1 }}
                exit={{ width: 0, opacity: 0 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                className="flex-shrink-0 overflow-hidden"
              >
                <div className="w-[420px] bg-white rounded-2xl border border-slate-200 shadow-sm h-[calc(100vh-180px)] sticky top-6">
                  <AnimatePresence mode="wait">
                    {aba === "projetos" && proposicaoSelecionada !== null && (
                      <PainelProposicao
                        key={proposicaoSelecionada}
                        id={proposicaoSelecionada}
                        onClose={() => setProposicaoSelecionada(null)}
                      />
                    )}
                    {aba === "votacoes" && votacaoSelecionada !== null && (
                      <PainelVotacao
                        key={votacaoSelecionada}
                        id={votacaoSelecionada}
                        onClose={() => setVotacaoSelecionada(null)}
                      />
                    )}
                  </AnimatePresence>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}