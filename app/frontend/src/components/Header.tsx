import { useState, useEffect, useRef } from "react"
import { Link, useLocation } from "react-router-dom"

// ─────────────────────────────────────────────────────────────────────────────
// Tipos
// ─────────────────────────────────────────────────────────────────────────────

interface SubLink {
  name: string
  href: string
  description: string
  icon: React.ReactNode
}

interface NavItem {
  name: string
  href?: string
  children?: SubLink[]
  highlight?: boolean
}

// ─────────────────────────────────────────────────────────────────────────────
// Ícones SVG inline
// ─────────────────────────────────────────────────────────────────────────────

const Icons = {
  Users: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
      <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
    </svg>
  ),
  BarChart: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" />
      <line x1="6" y1="20" x2="6" y2="14" /><line x1="2" y1="20" x2="22" y2="20" />
    </svg>
  ),
  FileText: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  ),
  BookOpen: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
      <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
    </svg>
  ),
  Info: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><line x1="12" y1="16" x2="12" y2="12" /><line x1="12" y1="8" x2="12.01" y2="8" />
    </svg>
  ),
  HelpCircle: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  ),
  ChevronDown: () => (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="6 9 12 15 18 9" />
    </svg>
  ),
  ChevronRight: () => (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  ),
  Arrow: () => (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 6h8M6 2l4 4-4 4" />
    </svg>
  ),
  Close: () => (
    <svg width="13" height="13" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
      <path d="M2 2l10 10M12 2L2 12" />
    </svg>
  ),
  Logo: () => (
    <svg viewBox="0 0 100 100" fill="none" width="14" height="14">
      <circle cx="45" cy="45" r="35" stroke="#1E3A8A" strokeWidth="10" fill="white" />
      <circle cx="45" cy="45" r="20" fill="#1E3A8A" />
      <rect x="30" y="43" width="30" height="4" fill="white" rx="2" />
      <line x1="68" y1="68" x2="90" y2="90" stroke="#1E3A8A" strokeWidth="10" strokeLinecap="round" />
    </svg>
  ),
  Map: () => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="18" x2="8" y2="22" />
      <line x1="16" y1="18" x2="16" y2="22" />
    </svg>
  ),
}

// ─────────────────────────────────────────────────────────────────────────────
// Estrutura de navegação
// ─────────────────────────────────────────────────────────────────────────────

const NAV_ITEMS: NavItem[] = [
  { name: "Home", href: "/" },
  {
    name: "Institucional",
    children: [
      {
        name: "Metodologia",
        href: "/metodologia",
        description: "Como calculamos scores e processamos os dados",
        icon: <Icons.BookOpen />,
      },
      {
        name: "Sobre",
        href: "/sobre",
        description: "Quem somos e o propósito do quemvota",
        icon: <Icons.Info />,
      },
      {
        name: "FAQ",
        href: "/faq",
        description: "Dúvidas frequentes sobre a plataforma",
        icon: <Icons.HelpCircle />,
      },
      {
        name: "Roadmap",
        href: "/roadmap",
        description: "O que vem por aí no quemvota",
        icon: <Icons.Map />,
      },
    ],
  },
  {
    name: "Explorar dados",
    highlight: true,
    children: [
      {
        name: "Parlamentares",
        href: "/politicos",
        description: "Perfil, gastos, votações e presença de cada deputado",
        icon: <Icons.Users />,
      },
      {
        name: "Rankings",
        href: "/rankings",
        description: "Compare parlamentares por performance, gastos e discursos",
        icon: <Icons.BarChart />,
      },
      {
        name: "Projetos e Votações",
        href: "/proposicoes",
        description: "Proposições em tramitação e votações no plenário",
        icon: <Icons.FileText />,
      },
    ],
  }
]

// ─────────────────────────────────────────────────────────────────────────────
// Dropdown desktop
// ─────────────────────────────────────────────────────────────────────────────

function Dropdown({ item, isOpen, onClose }: { item: NavItem; isOpen: boolean; onClose: () => void }) {
  if (!item.children) return null

  return (
    <div
      className="absolute left-1/2 z-50 w-72 pt-3"
      style={{
        top: "100%",
        transform: "translateX(-50%)",
        transition: "opacity 0.18s ease, transform 0.18s ease",
        opacity: isOpen ? 1 : 0,
        pointerEvents: isOpen ? "auto" : "none",
        translate: isOpen ? "0 0" : "0 -6px",
      }}
    >
      {/* Seta decorativa */}
      <div
        className="absolute top-[5px] left-1/2 -translate-x-1/2 w-3 h-3 bg-white border-l border-t border-black/[0.08] rotate-45 rounded-tl-sm"
        style={{ zIndex: 1 }}
      />

      {/* Painel */}
      <div className="relative bg-white rounded-2xl border border-black/[0.08] shadow-xl shadow-black/[0.08] p-1.5">
        {item.children.map((sub) => (
          <Link key={sub.href} to={sub.href} onClick={onClose} className="block no-underline group">
            <div className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 transition-colors">
              <div className="w-8 h-8 rounded-lg bg-slate-100 border border-black/[0.05] flex items-center justify-center flex-shrink-0 text-slate-500 group-hover:bg-blue-50 group-hover:text-blue-600 group-hover:border-blue-100 transition-all mt-0.5">
                {sub.icon}
              </div>
              <div>
                <div className="text-[13.5px] font-medium text-slate-800 leading-tight mb-0.5">
                  {sub.name}
                </div>
                <div className="text-xs text-slate-400 leading-snug">
                  {sub.description}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// Componente principal
// ─────────────────────────────────────────────────────────────────────────────

export default function Header() {
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)
  const [expandedDrawer, setExpandedDrawer] = useState<string | null>(null)
  const { pathname } = useLocation()
  const navRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setActiveDropdown(null)
      }
    }
    document.addEventListener("mousedown", onClickOutside)
    return () => document.removeEventListener("mousedown", onClickOutside)
  }, [])

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10)
    window.addEventListener("scroll", onScroll)
    return () => window.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    setDrawerOpen(false)
    setActiveDropdown(null)
    setExpandedDrawer(null)
  }, [pathname])

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? "hidden" : ""
    return () => { document.body.style.overflow = "" }
  }, [drawerOpen])

  function isParentActive(item: NavItem) {
    return item.children?.some((c) => pathname === c.href) ?? false
  }

  return (
    <div style={{ fontFamily: "'DM Sans', sans-serif" }}>

      {/* ── NAVBAR ── */}
      <nav className={`
        fixed top-0 left-0 w-full z-50 transition-all duration-300
        ${scrolled ? "bg-white/[0.92] backdrop-blur-md border-b border-black/[0.07] shadow-sm" : "bg-transparent"}
      `}>
        <div className="max-w-[1100px] mx-auto px-6 h-16 flex items-center justify-between">

          {/* LOGO */}
          <Link to="/" className="flex items-center gap-2 no-underline group">
            <div className="w-7 h-7 bg-[#1a1a1a] rounded-[7px] flex items-center justify-center flex-shrink-0 transition-colors duration-200 group-hover:bg-blue-600">
              <Icons.Logo />
            </div>
            <span style={{ fontFamily: "'DM Mono', monospace" }} className="text-[15px] font-medium text-[#1a1a1a] tracking-tight">
              quem<span className="text-blue-600">vota</span>
            </span>
          </Link>

          {/* DESKTOP NAV */}
          <div ref={navRef} className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => {
              const active = item.href ? pathname === item.href : isParentActive(item)
              const isOpen = activeDropdown === item.name

              // Link direto
              if (item.href) {
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      relative px-3.5 py-1.5 text-sm rounded-lg no-underline transition-all duration-150
                      ${active ? "text-[#1a1a1a] font-medium" : "text-zinc-500 hover:text-[#1a1a1a] hover:bg-black/[0.04]"}
                    `}
                  >
                    {item.name}
                    {active && <span className="absolute bottom-[-1px] left-3.5 right-3.5 h-[2px] bg-blue-600 rounded-full" />}
                  </Link>
                )
              }

              // Dropdown destacado (Explorar dados)
              if (item.highlight) {
                return (
                  <div key={item.name} className="relative ml-2">
                    <button
                      onClick={() => setActiveDropdown(isOpen ? null : item.name)}
                      className={`
                        flex items-center gap-1.5 px-4 py-[7px] rounded-lg text-[13.5px] font-medium
                        border-0 cursor-pointer text-white transition-all duration-150
                        hover:-translate-y-px active:translate-y-0
                        ${isOpen ? "bg-blue-600" : "bg-[#1a1a1a] hover:bg-blue-600"}
                      `}
                      style={{ fontFamily: "'DM Sans', sans-serif" }}
                    >
                      Explorar dados
                      <span className={`opacity-70 transition-transform duration-200 flex ${isOpen ? "rotate-180" : ""}`}>
                        <Icons.ChevronDown />
                      </span>
                    </button>
                    <Dropdown item={item} isOpen={isOpen} onClose={() => setActiveDropdown(null)} />
                  </div>
                )
              }

              // Dropdown normal (Institucional)
              return (
                <div key={item.name} className="relative">
                  <button
                    onClick={() => setActiveDropdown(isOpen ? null : item.name)}
                    className={`
                      flex items-center gap-1 px-3.5 py-1.5 rounded-lg text-sm
                      border-0 bg-transparent cursor-pointer transition-all duration-150
                      ${active || isOpen ? "text-[#1a1a1a] font-medium" : "text-zinc-500 hover:text-[#1a1a1a] hover:bg-black/[0.04]"}
                    `}
                    style={{ fontFamily: "'DM Sans', sans-serif" }}
                  >
                    {item.name}
                    <span className={`flex opacity-50 transition-transform duration-200 ${isOpen ? "rotate-180 !opacity-80" : ""}`}>
                      <Icons.ChevronDown />
                    </span>
                  </button>
                  {active && !isOpen && (
                    <span className="absolute bottom-[-1px] left-3.5 right-3.5 h-[2px] bg-blue-600 rounded-full" />
                  )}
                  <Dropdown item={item} isOpen={isOpen} onClose={() => setActiveDropdown(null)} />
                </div>
              )
            })}
          </div>

          {/* HAMBURGER */}
          <button
            className="md:hidden flex items-center justify-center w-10 h-10 rounded-lg hover:bg-black/[0.05] transition-colors border-0 bg-transparent cursor-pointer"
            onClick={() => setDrawerOpen((v) => !v)}
            aria-label="Abrir menu"
          >
            <div className="flex flex-col gap-[5px]">
              <span className={`block w-5 h-[1.5px] bg-[#1a1a1a] rounded-full origin-center transition-all duration-300 ${drawerOpen ? "translate-y-[6.5px] rotate-45" : ""}`} />
              <span className={`block w-5 h-[1.5px] bg-[#1a1a1a] rounded-full transition-all duration-300 ${drawerOpen ? "opacity-0 scale-x-0" : ""}`} />
              <span className={`block w-5 h-[1.5px] bg-[#1a1a1a] rounded-full origin-center transition-all duration-300 ${drawerOpen ? "-translate-y-[6.5px] -rotate-45" : ""}`} />
            </div>
          </button>

        </div>
      </nav>

      {/* ── OVERLAY MOBILE ── */}
      <div
        onClick={() => setDrawerOpen(false)}
        className={`
          fixed inset-0 z-[60] bg-black/25 backdrop-blur-sm transition-opacity duration-300
          ${drawerOpen ? "opacity-100" : "opacity-0 pointer-events-none"}
        `}
      />

      {/* ── DRAWER MOBILE ── */}
      <div
        className={`
          fixed top-0 right-0 h-full w-[290px] z-[70] bg-white
          flex flex-col px-6 py-6 overflow-y-auto
          transition-transform duration-[350ms] ease-[cubic-bezier(0.32,0.72,0,1)]
          shadow-[-8px_0_40px_rgba(0,0,0,0.12)]
          ${drawerOpen ? "translate-x-0" : "translate-x-full"}
        `}
      >
        {/* Header do drawer */}
        <div className="flex items-center justify-between mb-7 flex-shrink-0">
          <Link
            to="/"
            style={{ fontFamily: "'DM Mono', monospace" }}
            className="text-sm font-medium text-[#1a1a1a] no-underline"
          >
            quem<span className="text-blue-600">vota</span>
          </Link>
          <button
            onClick={() => setDrawerOpen(false)}
            className="w-8 h-8 rounded-lg bg-zinc-100 hover:bg-zinc-200 flex items-center justify-center transition-colors border-0 cursor-pointer text-zinc-500"
          >
            <Icons.Close />
          </button>
        </div>

        {/* Links */}
        <div className="flex flex-col gap-0.5 flex-1">
          {NAV_ITEMS.map((item) => {
            // Link direto
            if (item.href) {
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`
                    flex items-center justify-between px-3 py-3 rounded-xl text-sm no-underline transition-all
                    ${pathname === item.href
                      ? "bg-blue-50 text-blue-600 font-medium"
                      : "text-zinc-600 hover:bg-zinc-50 hover:text-[#1a1a1a]"
                    }
                  `}
                >
                  {item.name}
                  <span className={pathname === item.href ? "opacity-60" : "opacity-20"}>
                    <Icons.Arrow />
                  </span>
                </Link>
              )
            }

            // Grupo expansível
            const isExpanded = expandedDrawer === item.name
            const hasActiveChild = item.children?.some((c) => pathname === c.href)

            return (
              <div key={item.name}>
                <button
                  onClick={() => setExpandedDrawer(isExpanded ? null : item.name)}
                  className={`
                    w-full flex items-center justify-between px-3 py-3 rounded-xl text-sm
                    border-0 cursor-pointer transition-all
                    ${item.highlight
                      ? `text-white font-medium ${isExpanded ? "bg-blue-600" : "bg-[#1a1a1a] hover:bg-blue-600"} mb-0.5`
                      : `bg-transparent ${hasActiveChild ? "text-[#1a1a1a] font-medium" : "text-zinc-600"} hover:bg-zinc-50 hover:text-[#1a1a1a]`
                    }
                  `}
                  style={{ fontFamily: "'DM Sans', sans-serif" }}
                >
                  <span className="flex items-center gap-2">
                    {item.name}
                    {hasActiveChild && !item.highlight && (
                      <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
                    )}
                  </span>
                  <span className={`flex transition-transform duration-200 ${isExpanded ? "rotate-90" : ""} ${item.highlight ? "opacity-60" : "opacity-40"}`}>
                    <Icons.ChevronRight />
                  </span>
                </button>

                {isExpanded && (
                  <div className="ml-3 pl-3 border-l-2 border-zinc-100 mb-1 flex flex-col gap-0.5">
                    {item.children?.map((sub) => (
                      <Link
                        key={sub.href}
                        to={sub.href}
                        className={`
                          flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-[13.5px] no-underline transition-all
                          ${pathname === sub.href
                            ? "text-blue-600 font-medium"
                            : "text-zinc-500 hover:text-[#1a1a1a] hover:bg-zinc-50"
                          }
                        `}
                      >
                        <span className={pathname === sub.href ? "text-blue-500" : "text-zinc-400"}>
                          {sub.icon}
                        </span>
                        {sub.name}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Rodapé */}
        <div
          style={{ fontFamily: "'DM Mono', monospace" }}
          className="mt-6 text-center text-[11px] text-zinc-400 flex-shrink-0"
        >
          quemvota.com.br
        </div>
      </div>

    </div>
  )
}