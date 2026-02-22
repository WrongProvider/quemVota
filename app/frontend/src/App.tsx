//  layout de rotas
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Politicos from "./pages/Politicos"
import Rankings from "./pages/Rankings"
import PoliticoDetalhe from "./pages/PoliticosDetalhe"
import Home from "./pages/Home"
import './App.css'
import Metodologia from "./pages/Metodologia"

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/politicos" element={<Politicos />} />
        <Route path="/politicos_detalhe/:id" element={<PoliticoDetalhe />} />
        <Route path="/rankings" element={<Rankings />} />
        <Route path="*" element={<p>Página não encontrada</p>} />
        <Route path="/sobre" element={<p>Sobre o projeto</p>} />
        <Route path="/metodologia" element={<Metodologia />} />
      </Routes>
    </BrowserRouter>
  )
}

