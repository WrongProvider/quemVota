import { type ReactNode, useState } from "react"

type ToolDicaProps = {
  content: string
  children: ReactNode
  onClick?: () => void
}

export default function ToolDica({ content, children, onClick }: ToolDicaProps) {
  const [visible, setVisible] = useState(false)

  return (
    <div
      style={{
        position: "relative",
        display: "inline-block",
      }}
      onMouseEnter={() => setVisible(true)}
      onMouseLeave={() => setVisible(false)}
      onClick={onClick}
    >
      {children}

      {visible && (
        <div
          style={{
            position: "absolute",
            bottom: "130%",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "#222",
            color: "#fff",
            padding: "8px 12px",
            borderRadius: "6px",
            fontSize: "12px",
            whiteSpace: "nowrap",
            zIndex: 9999,
            boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
            opacity: 0.95,
            pointerEvents: "none",
          }}
        >
          {content}
        </div>
      )}
    </div>
  )
}

