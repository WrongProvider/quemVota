//  layout de rotas
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Politicos from "./pages/Politicos"
import Rankings from "./pages/Rankings"
import PoliticoDetalhe from "./pages/PoliticosDetalhe"
import ProjetosVotacoes from "./pages/ProjetoVotacoes"
import Home from "./pages/Home"
import './App.css'
import Metodologia from "./pages/Metodologia"
import DisclaimerBanner from "./components/DisclaimerBanner"
import Faq from "./pages/Faq"
import Sobre from "./pages/Sobre"
import Roadmap from "./pages/Roadmap"

export default function App() {
  return (
    <BrowserRouter>
      <DisclaimerBanner />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/politicos" element={<Politicos />} />
        <Route path="/politicos_detalhe/:id" element={<PoliticoDetalhe />} />
        <Route path="/rankings" element={<Rankings />} />
        <Route path="/sobre" element={<Sobre />} />
        <Route path="/metodologia" element={<Metodologia />} />
        <Route path="/faq" element={<Faq />} />
        <Route path="/proposicoes" element={<ProjetosVotacoes />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="*" element={<p>Página não encontrada</p>} />
      </Routes>
      
    </BrowserRouter>
  )
}

