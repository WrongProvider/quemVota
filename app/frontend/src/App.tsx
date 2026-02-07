//  layout de rotas
import { BrowserRouter, Routes, Route } from "react-router-dom"
import Politicos from "./pages/Politicos"
import Home from "./pages/Home"
import './App.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/politicos" element={<Politicos />} />
      </Routes>
    </BrowserRouter>
  )
}

