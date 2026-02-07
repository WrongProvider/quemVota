import Header from "../components/Header"
import { Link } from "react-router-dom"
import {
  MagnifyingGlassIcon,
  ChartBarIcon,
  Squares2X2Icon,
  ScaleIcon,
  UserGroupIcon,
} from "@heroicons/react/24/outline"

export default function Home() {
  return (
    <>
      <Header/>
      <main className="pt-20 bg-white">
        {/* HERO */}
        <section className="relative overflow-hidden">
          {/* Background glow */}
          <div className="absolute inset-0">
            <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-[900px] md:w-[1200px] h-[420px] md:h-[600px] rounded-full bg-blue-100 blur-3xl opacity-70" />
          </div>

          <div className="relative max-w-6xl mx-auto px-4 sm:px-6 py-16 sm:py-20 md:py-28 text-center">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-semibold text-gray-800 mb-5 leading-tight">
              Transparência sobre quem
              <br className="hidden sm:block" />
              decide o seu futuro
            </h1>

            <p className="text-gray-600 text-base sm:text-lg max-w-3xl mx-auto mb-8 sm:mb-10">
              Acompanhe votações, presenças, discursos e decisões do Congresso
              Nacional com dados oficiais, organizados de forma clara e acessível.
            </p>

            {/* SEARCH */}
            <div className="max-w-xl sm:max-w-2xl mx-auto mb-10 sm:mb-14">
              <div className="flex items-center bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
                <input
                  type="text"
                  placeholder="Pesquisar por parlamentar, votação ou tema..."
                  className="flex-1 px-4 sm:px-5 py-3 sm:py-4 outline-none text-sm sm:text-base text-gray-700"
                />
                <button className="bg-blue-600 hover:bg-blue-700 transition px-4 sm:px-6 py-3 sm:py-4 text-white">
                  🔍
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* CARDS */}
        <section className="relative pt-8 sm:pt-0 pb-20 sm:pb-24">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6">
            {/* Card 1 */}
            <Card
              icon={"👥"}
              title="Parlamentares"
              description="Veja o perfil de parlamentares, presença em votações e mais."
              link="/politicos"
            />

            <Card
              icon={"🧩"}
              title="Projetos, leis e temas"
              description="Pesquise por votações e proposições legislativas."
            />

            <Card
              icon={"📊"}
              title="Rankings"
              description="Compare parlamentares por presença e votações."
            />

            <Card
              icon={"⚖️"}
              title="Metodologia"
              description="Saiba como coletamos e organizamos os dados oficiais."
              link="/metodologia"
            />
          </div>

          <p className="text-center text-xs sm:text-sm text-gray-500 mt-8">
            Dados públicos da Câmara dos Deputados e do Senado Federal.
          </p>
        </section>
    </main>

    </>
  )
}

/* ---------- Card component ---------- */

function Card({
  icon,
  title,
  description,
  link,
}: {
  icon: React.ReactNode
  title: string
  description: string
  link?: string
}) {
  const content = (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 hover:shadow-md transition h-full">
      <div className="text-blue-600 mb-4 text-3xl">
        {icon}
      </div>
      <h3 className="font-semibold text-gray-800 mb-2">
        {title}
      </h3>
      <p className="text-sm text-gray-600">
        {description}
      </p>
    </div>
  )

  return link ? <Link to={link}>{content}</Link> : content
}
