import { useEffect, useState } from "react"
import { listarRankings } from "../api/rankings.api"
import type { RankingItem } from "../api/rankings.api"
import { TrophyIcon } from "@heroicons/react/24/outline"

export default function RankingDespesas() {
  const [data, setData] = useState<RankingItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function fetchData() {
      try {
        const res = await listarRankings(10)
        setData(res)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  function formatCurrency(value: number) {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: "BRL",
    }).format(value)
  }

  return (
    <main className="max-w-5xl mx-auto px-4 pt-24 pb-16">
      {/* Header */}
      <div className="flex items-center gap-3 mb-10">
        <TrophyIcon className="h-8 w-8 text-yellow-500" />
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900">
          Ranking de Despesas
        </h1>
      </div>

      {loading && (
        <p className="text-gray-500">Carregando ranking...</p>
      )}

      {!loading && (
        <div className="space-y-4">
          {data.map((item, index) => (
            <div
              key={item.politico_id}
              className="flex items-center justify-between rounded-xl border border-gray-200 p-4 shadow-sm hover:shadow-md transition"
            >
              {/* Posição */}
              <div className="flex items-center gap-4">
                <span className="text-lg font-bold text-gray-700 w-6">
                  {index + 1}
                </span>

                <div>
                  <p className="font-semibold text-gray-900">
                    {item.nome}
                  </p>
                  <p className="text-sm text-gray-500">
                    ID: {item.politico_id}
                  </p>
                </div>
              </div>

              {/* Valor */}
              <div className="text-right">
                <p className="text-lg font-semibold text-red-600">
                  {formatCurrency(item.total_gasto)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </main>
  )
}
