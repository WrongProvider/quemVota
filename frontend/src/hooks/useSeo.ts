import { useEffect } from "react"

interface SeoOptions {
  title: string
  description: string
  url?: string
  image?: string
  type?: "website" | "profile" | "article"
  /** Palavras-chave adicionais (opcional) */
  keywords?: string
}

const BASE_URL = "https://www.quemvota.com.br"
const DEFAULT_IMAGE = `${BASE_URL}/og-default.png`
const SITE_NAME = "quemvota"

/**
 * Hook reutilizável para injetar meta tags SEO, Open Graph e Twitter Card
 * dinamicamente no <head> e restaurar o estado anterior ao desmontar.
 *
 * Uso:
 *   useSeo({ title: "Página X", description: "Descrição..." })
 */
export function useSeo({
  title,
  description,
  url,
  image = DEFAULT_IMAGE,
  type = "website",
  keywords,
}: SeoOptions) {
  useEffect(() => {
    const fullTitle = title.includes("quemvota") ? title : `${title} | quemvota`
    const canonicalUrl = url ?? window.location.href

    // ── Título da aba ──────────────────────────────────────────────────────
    const prevTitle = document.title
    document.title = fullTitle

    // ── Helper: cria/atualiza meta tags ────────────────────────────────────
    const setMeta = (selector: string, attrPair: string, content: string) => {
      let el = document.querySelector(selector) as HTMLMetaElement | null
      if (!el) {
        el = document.createElement("meta")
        const [attr, val] = attrPair.split("=")
        el.setAttribute(attr, val ?? attr)
        el.setAttribute("data-seo-dynamic", "true")
        document.head.appendChild(el)
      }
      el.setAttribute("content", content)
      return el
    }

    const setLink = (rel: string, href: string) => {
      let el = document.querySelector(`link[rel="${rel}"]`) as HTMLLinkElement | null
      if (!el) {
        el = document.createElement("link")
        el.setAttribute("rel", rel)
        el.setAttribute("data-seo-dynamic", "true")
        document.head.appendChild(el)
      }
      el.setAttribute("href", href)
      return el
    }

    // ── Meta básicas ───────────────────────────────────────────────────────
    setMeta('meta[name="description"]',   "name=description",   description)
    setMeta('meta[name="robots"]',        "name=robots",        "index, follow")
    if (keywords) {
      setMeta('meta[name="keywords"]', "name=keywords", keywords)
    }

    // ── Open Graph ─────────────────────────────────────────────────────────
    setMeta('meta[property="og:title"]',       "property=og:title",       fullTitle)
    setMeta('meta[property="og:description"]', "property=og:description", description)
    setMeta('meta[property="og:url"]',         "property=og:url",         canonicalUrl)
    setMeta('meta[property="og:type"]',        "property=og:type",        type)
    setMeta('meta[property="og:image"]',       "property=og:image",       image)
    setMeta('meta[property="og:image:width"]', "property=og:image:width", "1200")
    setMeta('meta[property="og:image:height"]',"property=og:image:height","630")
    setMeta('meta[property="og:site_name"]',   "property=og:site_name",   SITE_NAME)
    setMeta('meta[property="og:locale"]',      "property=og:locale",      "pt_BR")

    // ── Twitter Card ───────────────────────────────────────────────────────
    setMeta('meta[name="twitter:card"]',        "name=twitter:card",        "summary_large_image")
    setMeta('meta[name="twitter:title"]',       "name=twitter:title",       fullTitle)
    setMeta('meta[name="twitter:description"]', "name=twitter:description", description)
    setMeta('meta[name="twitter:image"]',       "name=twitter:image",       image)
    setMeta('meta[name="twitter:site"]',        "name=twitter:site",        "@quemvota")

    // ── Canonical ─────────────────────────────────────────────────────────
    setLink("canonical", canonicalUrl)

    // ── JSON-LD: WebSite schema básico ─────────────────────────────────────
    const existingLd = document.querySelector('script[data-seo-dynamic="true"]')
    if (!existingLd) {
      const ld = document.createElement("script")
      ld.setAttribute("type", "application/ld+json")
      ld.setAttribute("data-seo-dynamic", "true")
      ld.textContent = JSON.stringify({
        "@context": "https://schema.org",
        "@type": "WebSite",
        name: SITE_NAME,
        url: BASE_URL,
        description: "Plataforma independente de transparência legislativa brasileira.",
        inLanguage: "pt-BR",
      })
      document.head.appendChild(ld)
    }

    // ── Cleanup ────────────────────────────────────────────────────────────
    return () => {
      document.querySelectorAll("[data-seo-dynamic='true']").forEach((el) => el.remove())
      document.title = prevTitle
    }
  }, [title, description, url, image, type, keywords])
}
