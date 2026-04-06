// layout de rotas
import { BrowserRouter, Routes, Route, Navigate, useParams } from "react-router-dom"
import Politicos from "./pages/Politicos"
import Rankings from "./pages/Rankings"
import PoliticoDetalhe from "./pages/PoliticosDetalhe"
import ProjetosVotacoes from "./pages/ProjetoVotacoes"
import Home from "./pages/Home"
import './App.css'
import Metodologia from "./pages/Metodologia"
import Faq from "./pages/Faq"
import Sobre from "./pages/Sobre"
import Roadmap from "./pages/Roadmap"
import GlobalExternalLinkModal from "./components/GlobalExternalLinkModal"
import ComparacaoPoliticos from "./pages/ComparacaoPoliticos"

/**
 * Redireciona URLs legadas com ID numérico para o formato com slug.
 *
 * Como o slug é derivado do nome (que só existe após buscar o detalhe),
 * o componente PoliticoDetalhe é responsável por fazer o redirect final
 * após carregar os dados. Este componente apenas garante que a rota antiga
 * /politicos_detalhe/:id seja tratada — redirecionando para /politicos/:id
 * onde o PoliticoDetalhe detecta o ID numérico e resolve o slug.
 */
function LegacyPoliticoRedirect() {
  const { id } = useParams<{ id: string }>()
  return <Navigate to={`/politicos/${id}`} replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/politicos" element={<Politicos />} />

        {/* ── Rota principal com suporte a slug e ID numérico ── */}
        {/* Exemplos válidos:                                      */}
        {/*   /politicos/joao-silva-neto  ← slug (canônico, SEO)  */}
        {/*   /politicos/1047             ← ID numérico (redirect) */}
        <Route path="/politicos/:id" element={<PoliticoDetalhe />} />

        {/* ── Rota legada — redireciona para o novo padrão ── */}
        <Route path="/politicos_detalhe/:id" element={<LegacyPoliticoRedirect />} />

        <Route path="/rankings" element={<Rankings />} />
        <Route path="/comparar/:slug1/:slug2" element={<ComparacaoPoliticos/>} />
        <Route path="/sobre" element={<Sobre />} />
        <Route path="/metodologia" element={<Metodologia />} />
        <Route path="/faq" element={<Faq />} />
        <Route path="/proposicoes" element={<ProjetosVotacoes />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="*" element={<p>Página não encontrada</p>} />
      </Routes>
      <GlobalExternalLinkModal />
    </BrowserRouter>
  )
}