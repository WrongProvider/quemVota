import { useState } from "react"
import { ExclamationTriangleIcon, XMarkIcon } from "@heroicons/react/24/outline"

export default function DisclaimerBanner() {
  const [dismissed, setDismissed] = useState(false)

  if (dismissed) return null

  return (
    <div className="bg-amber-50 border-t-2 border-amber-400">
      <div className="max-w-5xl mx-auto px-4 py-4 flex items-start gap-3">

        {/* Ícone */}
        <div className="flex-shrink-0 mt-0.5">
          <ExclamationTriangleIcon className="w-5 h-5 text-amber-500" />
        </div>

        {/* Texto */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-amber-800 mb-0.5">
            Projeto em Desenvolvimento
          </p>
          <p className="text-xs text-amber-700 leading-relaxed">
            Este projeto está em fase de desenvolvimento e o banco de dados ainda não foi totalmente
            ajustado para replicar fielmente os dados da Câmara dos Deputados. Os dados e scores
            apresentados <strong>podem não estar corretos</strong> e não devem ser interpretados como
            informação oficial ou definitiva. Use apenas para fins educacionais e de demonstração.
          </p>
        </div>

        {/* Fechar */}
        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 p-1 rounded-lg text-amber-500 hover:bg-amber-100 hover:text-amber-700 transition-colors mt-0.5"
          aria-label="Fechar aviso, estou ciente que o projeto está em desenvolvimento"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>

      </div>
    </div>
  )
}
