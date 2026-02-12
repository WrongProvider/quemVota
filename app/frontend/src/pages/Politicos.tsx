import { useSearchParams } from "react-router-dom"
import { useEffect, useState } from "react"
import { useDebounce } from "../hooks/useDebounce"
import { listarPoliticos } from "../api/politicos"

export default function Politicos() {
  const [searchParams] = useSearchParams()
  const q = searchParams.get("q") || ""

  const [search, setSearch] = useState(q)
  const debouncedSearch = useDebounce(search, 400)

  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    async function fetchData() {
      setLoading(true)
      try {
        const res = await listarPoliticos({
          q: debouncedSearch,
          limit: 20,
        })
        setData(res)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [debouncedSearch])

  return (
    <main className="max-w-6xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-semibold mb-6">
        Parlamentares
      </h1>

      {/* Input sincronizado */}
      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Buscar parlamentar..."
        className="w-full mb-6 rounded-lg border px-4 py-3"
      />

      {loading && <p className="text-gray-500">Carregando...</p>}

      {!loading && data.length === 0 && (
        <p className="text-gray-500">Nenhum resultado encontrado.</p>
      )}

      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((p) => (
          <li
            key={p.id}
            className="rounded-xl border p-4 hover:shadow transition"
          >
            <p className="font-semibold">{p.nome}</p>
            <p className="text-sm text-gray-600">
              {p.partido_sigla} • {p.uf}
            </p>
          </li>
        ))}
      </ul>
    </main>
  )
}
