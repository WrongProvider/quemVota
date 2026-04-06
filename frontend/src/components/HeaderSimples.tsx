import { Link } from "react-router-dom"
import { ArrowLeftIcon } from "@heroicons/react/24/outline"

export default function HeaderSimples() {
  return (
    <nav style={{ 
      padding: "1rem 2rem", 
      borderBottom: "1px solid #e5e5e5",
      background: "white",
      display: "flex",
      alignItems: "center",
      gap: "1rem"
    }}>
      <Link 
        to="/" 
        style={{ 
          display: "flex", 
          alignItems: "center", 
          gap: "0.5rem",
          textDecoration: "none",
          color: "#1E88E5",
          fontSize: "14px",
          fontWeight: 500
        }}
      >
        <ArrowLeftIcon style={{ width: "20px", height: "20px" }} />
        Voltar
      </Link>
      
      <Link to="/">
        <img src="/quemvota_logo.svg" alt="QuemVota" style={{ height: "35px" }} />
      </Link>
    </nav>
  )
}