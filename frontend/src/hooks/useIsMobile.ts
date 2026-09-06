import { useState, useEffect } from "react"

/**
 * useIsMobile — Hook reativo para detecção de viewports móveis (< 768px).
 *
 * Utiliza matchMedia nativo com event listener para alta performance
 * e atualização instantânea em mudanças de viewport ou orientação de tela.
 */
export function useIsMobile(breakpoint: number = 768): boolean {
  const [isMobile, setIsMobile] = useState<boolean>(() => {
    if (typeof window === "undefined") return false
    return window.innerWidth < breakpoint
  })

  useEffect(() => {
    if (typeof window === "undefined") return

    const mql = window.matchMedia(`(max-width: ${breakpoint - 1}px)`)
    const handler = (e: MediaQueryListEvent) => {
      setIsMobile(e.matches)
    }

    setIsMobile(mql.matches)

    mql.addEventListener("change", handler)
    return () => mql.removeEventListener("change", handler)
  }, [breakpoint])

  return isMobile
}

export default useIsMobile
