// InfoDicaBotao.tsx
import { forwardRef } from "react"

type InfoBotaoProps = {
  size?: number
} & React.HTMLAttributes<HTMLDivElement>

const InfoBotao = forwardRef<HTMLDivElement, InfoBotaoProps>(
  ({ size = 18, ...props }, ref) => {
    return (
      <div
        ref={ref}
        {...props}
        style={{
          width: size,
          height: size,
          borderRadius: "50%",
          backgroundColor: "#1E88E5",
          color: "white",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: size * 0.6,
          fontWeight: "bold",
          cursor: "help",
          transition: "transform 0.2s ease, background-color 0.2s ease",
          ...props.style,
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = "scale(1.1)"
          e.currentTarget.style.backgroundColor = "#1976D2"
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = "scale(1)"
          e.currentTarget.style.backgroundColor = "#1E88E5"
        }}
      >
        i
      </div>
    )
  }
)

InfoBotao.displayName = "InfoBotao"

export default InfoBotao