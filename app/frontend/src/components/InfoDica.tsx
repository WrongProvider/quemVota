import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { type ReactNode } from "react"

type InfoDicaProps = {
  content: string
  children: ReactNode
  side?: "top" | "right" | "bottom" | "left"
}

export default function InfoDica({ content, children, side = "top" }: InfoDicaProps) {
  return (
    <TooltipPrimitive.Provider delayDuration={200}>
      <TooltipPrimitive.Root>
        <TooltipPrimitive.Trigger asChild>
          {children}
        </TooltipPrimitive.Trigger>
        
        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            sideOffset={5}
            style={{
              backgroundColor: "#222",
              color: "#fff",
              padding: "8px 12px",
              borderRadius: "6px",
              fontSize: "12px",
              maxWidth: "250px",
              zIndex: 9999,
              boxShadow: "0 4px 12px rgba(0,0,0,0.2)",
              animation: "fadeIn 0.2s ease-out",
            }}
          >
            {content}
            <TooltipPrimitive.Arrow
              style={{
                fill: "#222",
              }}
            />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}