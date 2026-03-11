import * as TooltipPrimitive from "@radix-ui/react-tooltip"
import { type ReactNode, useState } from "react"

type InfoDicaProps = {
  content: string
  children: ReactNode
  side?: "top" | "right" | "bottom" | "left"
}

export default function InfoDica({ content, children, side = "bottom" }: InfoDicaProps) {
  const [open, setOpen] = useState(false)

  return (
    <TooltipPrimitive.Provider delayDuration={200}>
      <TooltipPrimitive.Root open={open} onOpenChange={setOpen}>
        <TooltipPrimitive.Trigger
          asChild
          onClick={(e) => {
            e.preventDefault()
            setOpen((v) => !v)
          }}
        >
          {children}
        </TooltipPrimitive.Trigger>

        <TooltipPrimitive.Portal>
          <TooltipPrimitive.Content
            side={side}
            sideOffset={6}
            align="center"
            avoidCollisions
            collisionPadding={{ top: 8, right: 16, bottom: 8, left: 16 }}
            sticky="always"
            onClick={() => setOpen(false)}
            className="z-[9999] max-w-[min(250px,calc(100vw-32px))] rounded-md bg-gray-900 px-3 py-2 text-xs leading-relaxed text-white shadow-lg cursor-pointer break-words animate-in fade-in-0 zoom-in-95"
          >
            {content}
            <TooltipPrimitive.Arrow className="fill-gray-900" />
          </TooltipPrimitive.Content>
        </TooltipPrimitive.Portal>
      </TooltipPrimitive.Root>
    </TooltipPrimitive.Provider>
  )
}