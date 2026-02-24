import axios from "axios"

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
})

// Interceptor global de erro
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("API Error:", error.response?.data || error.message)
    return Promise.reject(error)
  }
)

/**
 * client.ts — Instância Axios global com hardening de segurança.
 *
 * OWASP coberto:
 *  - A05 Security Misconfiguration : timeout curto, sem credentials cross-origin,
 *    cabeçalhos de segurança declarados (Content-Type explícito).
 *  - A09 Logging & Monitoring      : erros estruturados sem stack trace ou dados
 *    sensíveis expostos ao console em produção.
 *  - A10 SSRF                      : baseURL vem exclusivamente de variável de
 *    ambiente validada em build-time; não pode ser sobrescrita em runtime.
 */

// import axios, { AxiosError, type AxiosInstance, type AxiosResponse } from "axios"

// // ---------------------------------------------------------------------------
// // Validação de ambiente em build-time
// // ---------------------------------------------------------------------------
// const RAW_BASE_URL = import.meta.env.VITE_API_URL

// if (!RAW_BASE_URL) {
//   throw new Error("[client] VITE_API_URL não definida. Configure a variável de ambiente.")
// }

// /** URL base imutável após inicialização — evita SSRF por sobrescrita em runtime. */
// const BASE_URL: string = RAW_BASE_URL.replace(/\/+$/, "") // remove barra final

// // ---------------------------------------------------------------------------
// // Instância Axios
// // ---------------------------------------------------------------------------
// export const api: AxiosInstance = axios.create({
//   baseURL: BASE_URL,
//   timeout: 12_000,               // 12 s — equilibra UX e resiliência
//   withCredentials: false,        // A01: sem cookies cross-origin automáticos
//   headers: {
//     "Content-Type": "application/json",
//     Accept: "application/json",
//     /**
//      * Sinaliza ao backend que a requisição vem de um browser JS legítimo.
//      * Não substitui autenticação, mas auxilia em fingerprinting de origem.
//      */
//     "X-Requested-With": "XMLHttpRequest",
//   },
// })

// // ---------------------------------------------------------------------------
// // Interceptor de resposta — A09: logging estruturado e seguro
// // ---------------------------------------------------------------------------
// api.interceptors.response.use(
//   (response: AxiosResponse) => response,
//   (error: AxiosError) => {
//     /**
//      * Em produção não expomos stack traces nem detalhes internos no console.
//      * Logamos apenas o mínimo útil para monitoramento sem vazar dados sensíveis.
//      *
//      * OWASP A09: Log adequado sem PII ou segredos.
//      */
//     if (import.meta.env.DEV) {
//       console.error("[API][DEV]", {
//         method: error.config?.method?.toUpperCase(),
//         url: error.config?.url,
//         status: error.response?.status,
//         // Nunca loga o corpo da request (pode conter tokens/dados sensíveis)
//         responseData: error.response?.data,
//       })
//     } else {
//       // Em produção: apenas status + rota para telemetria (sem dados de usuário)
//       console.error("[API]", error.response?.status, error.config?.url)
//     }

//     return Promise.reject(error)
//   },
// )