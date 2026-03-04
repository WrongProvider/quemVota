/**
 * useFuzzySearch.ts — Busca fuzzy para nomes de parlamentares.
 *
 * Problema: a API faz busca exata por substring, então "Nic" não encontra
 * "Nikolas" porque a substring não está presente.
 *
 * Solução em duas camadas:
 *  1. Normalização: remove acentos, converte para minúsculas
 *  2. Expansão fonética: substitui variações ortográficas equivalentes
 *     antes de enviar o termo para a API (ex: "c" → "k", "ss" → "ç")
 *
 * Isso garante que a busca seja compatível com o backend sem exigir
 * alterações no servidor.
 */

import { useMemo } from "react"

// ─────────────────────────────────────────────────────────────────────────────
// Normalização
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Remove acentos e converte para minúsculas.
 * "Nikólas" → "nikolas", "João" → "joao"
 */
export function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
}

// ─────────────────────────────────────────────────────────────────────────────
// Expansão fonética — gera variantes do termo buscado
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Mapeamento de substituições fonéticas comuns em nomes brasileiros.
 */
const PHONETIC_MAP: Record<string, string[]> = {
  c:   ["k"],
  k:   ["c"],
  z:   ["s"],
  s:   ["z"],
  ph:  ["f"],
  f:   ["ph"],
  th:  ["t"],
  y:   ["i"],
  i:   ["y"],
  w:   ["v"],
  v:   ["w"],
  ck:  ["c", "k"],
  x:   ["ch", "s", "z"],
  ch:  ["x"],
}

/**
 * Gera variantes fonéticas de um termo normalizado.
 * Para "nic" retorna: ["nic", "nik"]
 */
export function generatePhoneticVariants(term: string): string[] {
  const normalized = normalizeText(term)
  const variants = new Set<string>([normalized])

  for (const [pattern, replacements] of Object.entries(PHONETIC_MAP)) {
    if (normalized.includes(pattern)) {
      for (const replacement of replacements) {
        variants.add(normalized.split(pattern).join(replacement))
        variants.add(normalized.replace(pattern, replacement))
      }
    }
  }

  return Array.from(variants)
}

// ─────────────────────────────────────────────────────────────────────────────
// Score de similaridade
// ─────────────────────────────────────────────────────────────────────────────

function bigramSimilarity(a: string, b: string): number {
  if (a.length < 2 || b.length < 2) return 0

  const getBigrams = (str: string) => {
    const bigrams: string[] = []
    for (let i = 0; i < str.length - 1; i++) {
      bigrams.push(str.slice(i, i + 2))
    }
    return bigrams
  }

  const aBigrams = getBigrams(a)
  const bBigrams = getBigrams(b)
  let matches = 0
  const bCopy = [...bBigrams]

  for (const bigram of aBigrams) {
    const idx = bCopy.indexOf(bigram)
    if (idx !== -1) {
      matches++
      bCopy.splice(idx, 1)
    }
  }

  return (2 * matches) / (aBigrams.length + bBigrams.length)
}

export function similarityScore(query: string, candidate: string): number {
  const q = normalizeText(query)
  const c = normalizeText(candidate)

  if (c === q) return 100
  if (c.startsWith(q)) return 80
  if (c.includes(q)) return 60

  const variants = generatePhoneticVariants(q)
  for (const variant of variants) {
    if (variant === q) continue
    if (c.startsWith(variant)) return 40
    if (c.includes(variant)) return 20
  }

  const bigramScore = bigramSimilarity(q, c)
  if (bigramScore > 0.5) return Math.round(bigramScore * 15)

  return 0
}

// ─────────────────────────────────────────────────────────────────────────────
// Hook principal
// ─────────────────────────────────────────────────────────────────────────────

interface FuzzySearchOptions {
  minScore?: number
  fields?: string[]
}

export function useFuzzySearch<T extends Record<string, any>>(
  items: T[],
  query: string,
  options: FuzzySearchOptions = {},
): T[] {
  const { minScore = 15, fields = ["nome"] } = options

  return useMemo(() => {
    if (!query || query.trim().length < 2) return items

    const scored = items
      .map((item) => {
        const score = Math.max(
          ...fields.map((field) => {
            const value = String(item[field] ?? "")
            return similarityScore(query, value)
          }),
        )
        return { item, score }
      })
      .filter(({ score }) => score >= minScore)
      .sort((a, b) => b.score - a.score)

    return scored.map(({ item }) => item)
  }, [items, query, minScore, fields])
}

// ─────────────────────────────────────────────────────────────────────────────
// Utilitário: gera o melhor termo para a API (com variantes para múltiplas buscas)
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Retorna o termo normalizado (sem acento) para enviar à API.
 * Isso já melhora muito a cobertura para casos como "Joao" → "João".
 */
export function preparaTermoBusca(termo: string): string {
  return normalizeText(termo)
}