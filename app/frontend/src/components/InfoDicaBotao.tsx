type InfoBotaoProps = {
  size?: number
}

export default function InfoBotao({ size = 18 }: InfoBotaoProps) {
  return (
    <div
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
        cursor: "pointer",
        transition: "0.2s ease",
      }}
    >
      i
    </div>
  )
}
