import { useParams } from "react-router-dom"
import { usePoliticoDetalhe, usePoliticos } from "../hooks/usePoliticos"

export default function PoliticoDetalhe() {
  const { id } = useParams()
  const { data: politico, isLoading, isError } = usePoliticoDetalhe(Number(id))

  if (isLoading) {
    return (
      <main className="max-w-5xl mx-auto px-4 py-12">
        <p className="text-slate-500">Carregando parlamentar...</p>
      </main>
    )
  }

  if (isError || !politico) {
    return (
      <main className="max-w-5xl mx-auto px-4 py-12">
        <p className="text-red-500">Erro ao carregar parlamentar.</p>
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-50 to-white">

      {/* HERO */}
      <section className="border-b bg-white">
        <div className="max-w-5xl mx-auto px-4 py-12 flex flex-col md:flex-row gap-10 items-center">

          {/* FOTO */}
          <div className="bg-slate-50 p-4 rounded-2xl shadow-sm">
            <img
              src={politico.url_foto}
              alt={politico.nome}
              className="w-40 h-40 object-contain rounded-xl"
            />
          </div>

          {/* IDENTIDADE */}
          <div className="flex-1 text-center md:text-left">
            <h1 className="text-4xl font-semibold">
              {politico.nome}
            </h1>

            <p className="text-lg text-slate-600 mt-2">
              {politico.partido_sigla} • {politico.uf}
            </p>

            <div className="mt-6 flex flex-wrap gap-3 justify-center md:justify-start text-sm">
              {politico.situacao && (
                <span className="bg-slate-100 px-3 py-1 rounded-full text-slate-600">
                  {politico.situacao}
                </span>
              )}
              {politico.condicao_eleitoral && (
                <span className="bg-slate-100 px-3 py-1 rounded-full text-slate-600">
                  {politico.condicao_eleitoral}
                </span>
              )}
            </div>
          </div>

        </div>
      </section>

      {/* INFORMAÇÕES INSTITUCIONAIS */}
      <section className="max-w-5xl mx-auto px-4 py-10">

        <div className="bg-white border rounded-2xl shadow-sm p-8 space-y-6">

          <h2 className="text-xl font-semibold">
            Informações Institucionais
          </h2>

          <div className="grid md:grid-cols-2 gap-6 text-sm">

            <div>
              <p className="text-slate-500">Escolaridade</p>
              <p className="font-medium mt-1">
                {politico.escolaridade || "Não informado"}
              </p>
            </div>

            <div>
              <p className="text-slate-500">Situação</p>
              <p className="font-medium mt-1">
                {politico.situacao || "Não informado"}
              </p>
            </div>

            <div>
              <p className="text-slate-500">Condição Eleitoral</p>
              <p className="font-medium mt-1">
                {politico.condicao_eleitoral || "Não informado"}
              </p>
            </div>

          </div>

        </div>

        {/* CONTATO */}
        <div className="mt-8 bg-white border rounded-2xl shadow-sm p-8 space-y-6">

          <h2 className="text-xl font-semibold">
            Contato do Gabinete
          </h2>

          <div className="space-y-4 text-sm">

            <div>
              <p className="text-slate-500">Email</p>
              <p className="font-medium mt-1">
                {politico.email_gabinete || "Não informado"}
              </p>
            </div>

            <div>
              <p className="text-slate-500">Telefone</p>
              <p className="font-medium mt-1">
                {politico.telefone_gabinete || "Não informado"}
              </p>
            </div>

          </div>

        </div>

      </section>
    </main>
  )
}
