import Header from "../components/Header"
import { Link, useNavigate } from "react-router-dom"
import { useState } from "react"; 

import {
  MagnifyingGlassIcon,
  ChartBarIcon,
  Squares2X2Icon,
  ScaleIcon,
  UserGroupIcon,
} from "@heroicons/react/24/outline"

import { motion } from "framer-motion";



export default function Home() {
  // redirect para a página de políticos ao submeter a pesquisa
  const [query, setQuery] = useState("")
  const navigate = useNavigate()

  function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!query.trim()) return
    navigate(`/politicos?q=${encodeURIComponent(query)}`)
  }
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
            <motion.h1 
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              className="text-3xl sm:text-4xl md:text-5xl font-semibold text-gray-800 mb-5"
            >
              Transparência sobre quem decide o seu futuro
            </motion.h1>

            <p className="text-gray-600 text-base sm:text-lg max-w-3xl mx-auto mb-8 sm:mb-10">
              Acompanhe votações, presenças, discursos e decisões do Congresso
              Nacional com dados oficiais, organizados de forma clara e acessível.
            </p>

            {/* SEARCH */}
            <div className="max-w-xl sm:max-w-2xl mx-auto mb-10 sm:mb-14">
              <div className="flex items-center bg-white rounded-xl shadow-md overflow-hidden border border-gray-200">
                <form
                  onSubmit={handleSearch}
                  className="flex items-center bg-white rounded-xl shadow-md overflow-hidden border border-gray-200"
                ></form>
                <input
                  type="text"
                  placeholder="Pesquisar por parlamentar, votação ou tema..."
                  className="flex-1 px-4 sm:px-5 py-3 sm:py-4 outline-none text-sm sm:text-base text-gray-700"
                  onChange={(e) => setQuery(e.target.value)}
                />
                <button className="bg-blue-600 hover:bg-blue-700 transition px-4 sm:px-6 py-3 sm:py-4 text-white">
                  <MagnifyingGlassIcon className="h-5 w- text-white" />
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* CARDS */}
        <section className="relative pt-8 sm:pt-0 pb-20 sm:pb-24">
          <div className="max-w-6xl mx-auto px-4 sm:px-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6">
            
            {/* Envolva cada Card com o motion.div */}
            <motion.div
              initial={{ opacity: 0, y: 20 }} // Começa invisível e 20px abaixo
              whileInView={{ opacity: 1, y: 0 }} // Quando aparecer no scroll, sobe e aparece
              viewport={{ once: true }} // Anima apenas uma vez
              transition={{ duration: 0.5, delay: 0.1 }} // Pequeno atraso para o primeiro
            >
              <Card
                icon={"👥"}
                title="Parlamentares"
                description="Veja o perfil de parlamentares, presença em votações e mais."
                link="/politicos"
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }} // Atraso maior (efeito cascata)
            >
              <Card
                icon={"🧩"}
                title="Projetos, leis e temas"
                description="Pesquise por votações e proposições legislativas."
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.3 }} // Atraso maior (efeito cascata)
            >
              <Card
                icon={"📊"}
                title="Rankings"
                description="Compare parlamentares por presença e votações."
              />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.4 }} // Atraso maior (efeito cascata)
            >
              <Card
                icon={"⚖️"}
                title="Metodologia"
                description="Saiba como coletamos e organizamos os dados oficiais."
                link="/metodologia"
              />
            </motion.div>
            
            {/* Repita o padrão para os outros cards, aumentando o delay em 0.1 cada */}
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
