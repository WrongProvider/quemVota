import { useQuery } from "@tanstack/react-query"
import { listarPoliticos } from "../api/politicos"

export default function Politicos() {
  const { data, isLoading, error } = useQuery<Politico[]>({
    queryKey: ["politicos"],
    queryFn: () => listarPoliticos({ limit: 20 }),
  })

  if (isLoading) {
    return <p className="p-6">Carregando...</p>
  }

  if (error) {
    return (
      <p className="p-6 text-red-600">
        Erro ao carregar dados
      </p>
    )
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-semibold mb-6">
        Parlamentares
      </h1>

      <ul className="space-y-3">
        {data?.map((p) => (
          <li
            key={p.id}
            className="border rounded-md p-4"
          >
            <strong>{p.nome}</strong>
            <div className="text-sm text-gray-600">
              {p.partido_sigla}/{p.uf}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
