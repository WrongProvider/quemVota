import { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline";

export default function Header() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
}, []);
  // Fecha o menu automaticamente ao mudar de rota
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // Impede o scroll do body quando o menu estiver aberto
  useEffect(() => {
  document.body.style.overflow = open ? "hidden" : "unset";
  
  // Função de limpeza (cleanup)
  return () => {
    document.body.style.overflow = "unset";
  };
}, [open]);

  const navLinks = [
    { name: "Home", href: "/" },
    { name: "Parlamentares", href: "/politicos" },
    { name: "Metodologia", href: "/metodologia" },
  ];

  return (
    <>
      {/* NAVBAR PRINCIPAL */}
      <nav className={`fixed top-0 left-0 z-50 w-full transition-all duration-300 ${
  scrolled ? "border-b border-neutral-200 bg-white/90 shadow-sm backdrop-blur-md" : "bg-transparent"
}`}>
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-6">
          <div className="flex h-16 items-center justify-between">
            
            {/* LOGO */}
            <Link to="/" className="flex items-center gap-2 group">
              <span className="text-xl font-bold tracking-tight text-blue-600 group-hover:text-blue-700 transition">
                QuemVota
              </span>
            </Link>

            {/* LINKS DESKTOP */}
            <div className="hidden md:flex items-center gap-1">
              {navLinks.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.name}
                    to={link.href}
                    className={`px-4 py-2 text-sm font-medium transition-colors ${
                      isActive 
                        ? "text-blue-600 border-b-2 border-blue-600" // Estilo para página ativa
                        : "text-gray-600 hover:text-blue-600"
                    }`}
                  >
                    {link.name}
                  </Link>
                );
              })}
              
              <Link
                to="/politicos"
                className="ml-4 hidden lg:inline-flex items-center justify-center rounded-full bg-blue-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-all active:scale-95"
              >
                Explorar dados
              </Link>
            </div>

            {/* BOTÃO MOBILE (HAMBÚRGUER) */}
            <div className="flex md:hidden">
              <button
                type="button"
                onClick={() => setOpen(true)}
                className="inline-flex items-center justify-center rounded-md p-2 text-gray-700 hover:bg-gray-100 focus:outline-none"
              >
                <Bars3Icon className="h-7 w-7" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* OVERLAY MOBILE */}
      <div
        className={`fixed inset-0 z-[60] bg-gray-900/50 backdrop-blur-sm transition-opacity duration-300 md:hidden ${
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
        onClick={() => setOpen(false)}
      />

      {/* MENU LATERAL (DRAWER) */}
      <div
        className={`fixed inset-y-0 right-0 z-[70] w-full max-w-xs overflow-y-auto bg-white px-6 py-6 transition-transform duration-300 ease-in-out sm:ring-1 sm:ring-gray-900/10 md:hidden ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between">
          <Link to="/" className="-m-1.5 p-1.5 font-bold text-blue-600">
            QuemVota
          </Link>
          <button
            type="button"
            className="-m-2.5 rounded-md p-2.5 text-gray-700"
            onClick={() => setOpen(false)}
          >
            <XMarkIcon className="h-7 w-7" aria-hidden="true" />
          </button>
        </div>

        <div className="mt-8 flow-root">
          <div className="flex flex-col gap-y-4">
            {navLinks.map((link) => (
              <Link
                key={link.name}
                to={link.href}
                className="text-lg font-semibold leading-7 text-gray-900 hover:bg-gray-50 p-2 rounded-lg"
              >
                {link.name}
              </Link>
            ))}
            <hr className="my-2 border-gray-100" />
            <Link
              to="/politicos"
              className="rounded-full bg-blue-600 px-6 py-3 text-center text-base font-semibold text-white shadow-md hover:bg-blue-700"
            >
              Explorar dados
            </Link>
          </div>
        </div>
      </div>
    </>
  );
}

