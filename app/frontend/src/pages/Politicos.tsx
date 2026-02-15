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
    <main className="max-w-6xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold mb-6">
        Parlamentares
      </h1>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Buscar parlamentar..."
        className="w-full mb-6 rounded-lg border px-4 py-3"
      />

      {isLoading && (
        <p className="text-gray-500">Carregando...</p>
      )}

      {isError && (
        <p className="text-red-500">
          Erro ao carregar dados.
        </p>
      )}

      {!isLoading && data?.length === 0 && (
        <p className="text-gray-500">
          Nenhum resultado encontrado.
        </p>
      )}

      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data?.map((p) => (
          <Link
            to={`/politicos/${p.id}`}
            key={p.id}
            className="rounded-xl border p-4 hover:shadow transition block"
          >
            <p className="font-semibold">{p.nome}</p>
            <p className="text-sm text-gray-600">
              {p.partido_sigla} • {p.uf}
            </p>
          </Link>

        ))}
      </ul>
    </main>
  )
}
