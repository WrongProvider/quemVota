import { Link } from "react-router-dom"
import Header from "../components/Header"
import { useSeo } from "../hooks/useSeo"
import { Users, Scale, FileSearch, ArrowLeft, Home } from "lucide-react"

export default function NotFound() {
  useSeo({
    title: "Página não encontrada | quemvota",
    description: "A página que você está procurando não existe ou foi movida. Explore os dados públicos da Câmara dos Deputados no quemvota.",
    noindex: true,
  })

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans antialiased text-slate-800">
      <Header />

      <main className="flex-1 flex items-center justify-center px-4 sm:px-6 py-12 sm:py-20">
        <div className="max-w-lg w-full text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-amber-50 border border-amber-200 text-amber-600 font-bold text-2xl mb-6 shadow-sm">
            404
          </div>

          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mb-3">
            Página não encontrada
          </h1>
          <p className="text-sm sm:text-base text-slate-600 mb-8 max-w-md mx-auto leading-relaxed">
            O endereço solicitado não foi localizado ou não está mais disponível. Você pode retornar à página inicial ou navegar pelas seções principais de dados públicos:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-8 text-left">
            <Link
              to="/politicos"
              className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/70 transition-all shadow-sm group min-h-[48px]"
            >
              <div className="p-2 rounded-lg bg-blue-50 text-blue-600 group-hover:scale-105 transition-transform">
                <Users size={18} />
              </div>
              <div>
                <span className="block text-xs font-semibold text-slate-900">Deputados</span>
                <span className="block text-[11px] text-slate-500">Perfis e gastos</span>
              </div>
            </Link>

            <Link
              to="/comparar"
              className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/70 transition-all shadow-sm group min-h-[48px]"
            >
              <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600 group-hover:scale-105 transition-transform">
                <Scale size={18} />
              </div>
              <div>
                <span className="block text-xs font-semibold text-slate-900">Comparador</span>
                <span className="block text-[11px] text-slate-500">Alinhamento</span>
              </div>
            </Link>

            <Link
              to="/proposicoes"
              className="flex items-center gap-3 p-3.5 rounded-xl border border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/70 transition-all shadow-sm group min-h-[48px]"
            >
              <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 group-hover:scale-105 transition-transform">
                <FileSearch size={18} />
              </div>
              <div>
                <span className="block text-xs font-semibold text-slate-900">Proposições</span>
                <span className="block text-[11px] text-slate-500">Votações</span>
              </div>
            </Link>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 transition-colors shadow-sm min-h-[44px]"
            >
              <Home size={16} />
              Voltar ao Início
            </Link>
            <button
              onClick={() => window.history.back()}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-slate-300 text-slate-700 text-sm font-medium hover:bg-slate-100 transition-colors min-h-[44px]"
            >
              <ArrowLeft size={16} />
              Página anterior
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
