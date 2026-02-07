import { useState } from "react"
import { Link } from "react-router-dom"
import { Bars3Icon, XMarkIcon } from "@heroicons/react/24/outline"

export default function Header() {
  const [open, setOpen] = useState(false)

  return (
    <>
      {/* HEADER */}
      <nav className="fixed top-0 z-50 w-full border-b border-neutral-300 bg-white/80 backdrop-blur transition-all">
        <div className="mx-auto max-w-7xl px-4 md:px-16 lg:px-24 py-4 flex items-center justify-between">
          
          {/* LOGO */}
          <Link to="/" className="font-semibold text-lg text-gray-800">
            QuemVota
          </Link>

          {/* MENU DESKTOP */}
          <div className="hidden md:flex gap-3 text-sm text-gray-700">
            <Link className="px-3 py-1 hover:text-zinc-500" to="/">
              Home
            </Link>
            <Link className="px-3 py-1 hover:text-zinc-500" to="/politicos">
              Parlamentares
            </Link>
            <Link className="px-3 py-1 hover:text-zinc-500" to="/metodologia">
              Metodologia
            </Link>
          </div>

          {/* CTA DESKTOP */}
          <Link
            to="/politicos"
            className="hidden md:inline-block rounded-full bg-blue-600 px-6 py-2.5 text-sm text-white shadow-[inset_0_2px_4px_rgba(255,255,255,0.4)] hover:bg-blue-700 transition"
          >
            Explorar dados
          </Link>

          {/* BOTÃO MOBILE */}
          <button
            onClick={() => setOpen(true)}
            className="md:hidden text-gray-700"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
        </div>
      </nav>

      {/* MENU MOBILE (DRAWER) */}
      <div
        className={`fixed top-0 right-0 z-[60] h-full w-full bg-white transition-all duration-300 ${
          open ? "translate-y-0" : "-translate-y-full"
        }`}
      >
        <div className="flex items-center justify-between p-4 border-b">
          <span className="font-semibold">QuemVota</span>
          <button onClick={() => setOpen(false)}>
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="flex flex-col gap-4 p-4 text-base">
          <Link onClick={() => setOpen(false)} to="/">
            Home
          </Link>
          <Link onClick={() => setOpen(false)} to="/politicos">
            Parlamentares
          </Link>
          <Link onClick={() => setOpen(false)} to="/metodologia">
            Metodologia
          </Link>

          <Link
            to="/politicos"
            className="mt-4 w-max rounded-full bg-blue-600 px-6 py-2.5 text-sm text-white"
          >
            Explorar dados
          </Link>
        </div>
      </div>
    </>
  )
}
