/**
 * Utilitários de formatação para exibição pública de dados no QuemVota.
 * Garante rigor na apresentação de moedas (duas casas decimais obrigatórias)
 * e números inteiros com separadores de milhar pt-BR.
 */

const formatadorBRL = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

const formatadorInt = new Intl.NumberFormat("pt-BR", {
  maximumFractionDigits: 0,
})

/**
 * Formata um valor numérico para o padrão monetário brasileiro (R$ 1.345.324,70).
 */
export function formatarMoedaBRL(valor: number | null | undefined): string {
  if (valor == null || isNaN(valor)) return "R$ 0,00"
  return formatadorBRL.format(valor)
}

/**
 * Formata números com separador de milhar brasileiro (ex: 1.814).
 */
export function formatarNumero(valor: number | null | undefined): string {
  if (valor == null || isNaN(valor)) return "0"
  return formatadorInt.format(valor)
}

/**
 * Formata percentuais factuais (ex: 15% ou 96,4%).
 */
export function formatarPercentual(valor: number | null | undefined, decimais = 0): string {
  if (valor == null || isNaN(valor)) return "—"
  return `${valor.toLocaleString("pt-BR", {
    minimumFractionDigits: decimais,
    maximumFractionDigits: decimais,
  })}%`
}
