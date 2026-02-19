import { useSearchParams, Link } from "react-router-dom"
import { useState } from "react"
import { useDebounce } from "../hooks/useDebounce"
import { usePoliticos } from "../hooks/usePoliticos"

export default function Politicos() {
  const [searchParams] = useSearchParams()
  const initialQ = searchParams.get("q") || ""

  const [search, setSearch] = useState(initialQ)
  const debouncedSearch = useDebounce(search, 400)

  const { data, isLoading, isError } = usePoliticos({
    q: debouncedSearch,
    limit: 200,
  })

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="max-w-6xl mx-auto px-4 py-12">

        <h1 className="text-3xl font-semibold mb-8">
          Parlamentares
        </h1>

        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Buscar parlamentar..."
          className="w-full mb-10 rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-300 transition"
        />

        {isLoading && (
          <p className="text-slate-500">Carregando...</p>
        )}

        {isError && (
          <p className="text-red-500">
            Erro ao carregar dados.
          </p>
        )}

        {!isLoading && data?.length === 0 && (
          <p className="text-slate-500">
            Nenhum resultado encontrado.
          </p>
        )}

        <ul className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {data?.map((p) => (
            <Link
              to={`/politicos_detalhe/${p.id}`}
              key={p.id}
              className="group bg-white border border-slate-200 rounded-2xl p-6 flex items-center gap-5 shadow-sm hover:shadow-md hover:-translate-y-1 transition"
            >
              {/* FOTO */}
              <img
                src={p.url_foto}
                alt={p.nome}
                className="w-25 h-25 rounded-xl object-contain bg-slate-50 p-2 shadow-sm"
              />

              {/* INFO */}
              <div>
                <p className="font-semibold text-lg group-hover:text-black transition">
                  {p.nome}
                </p>
                <p className="text-sm text-slate-500 mt-1">
                  {p.partido_sigla} • {p.uf}
                </p>
              </div>
            </Link>
          ))}
        </ul>

      </div>
    </main>
  )
}
