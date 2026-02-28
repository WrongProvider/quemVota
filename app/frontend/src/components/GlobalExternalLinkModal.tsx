import { useEffect, useState } from 'react';
import { ExternalLink, ChevronRight } from 'lucide-react';

export default function GlobalExternalLinkModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [targetUrl, setTargetUrl] = useState('');

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const link = (e.target as HTMLElement).closest('a');
      
      if (!link) return;

      // 🛑 A SOLUÇÃO: Se o link tiver nossa "marcação" especial, ignora e deixa abrir!
      if (link.getAttribute('data-ignore-modal') === 'true') {
        return;
      }

      const href = link.getAttribute('href');
      
      if (!href || href.startsWith('/') || href.startsWith('#') || href.includes(window.location.hostname)) {
        return;
      }

      if (href.startsWith('http')) {
        e.preventDefault(); // Bloqueia a abertura
        setTargetUrl(href); // Salva o link
        setIsOpen(true);    // Mostra o modal
      }
    };

    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="p-6 text-center">
          <div className="w-16 h-16 bg-blue-50 text-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <ExternalLink size={28} />
          </div>
          <h3 className="text-xl font-bold text-slate-800 mb-2" style={{ fontFamily: 'Fraunces, serif' }}>
            Aviso de Redirecionamento
          </h3>
          <p className="text-sm text-slate-600 mb-6">
            Você está saindo do <strong>quemvota.com.br</strong> e será redirecionado para:<br />
            <span className="inline-block mt-2 px-3 py-1.5 bg-slate-100 rounded-lg text-xs font-mono text-slate-500 break-all border border-slate-200">
              {targetUrl}
            </span>
          </p>
          
          <div className="flex gap-3">
            <button
              onClick={() => setIsOpen(false)}
              className="flex-1 py-2.5 px-4 rounded-xl border border-slate-200 text-slate-600 font-medium hover:bg-slate-50 transition-colors cursor-pointer"
            >
              Cancelar
            </button>
            <a
              href={targetUrl}
              target="_blank"
              rel="noopener noreferrer"
              data-ignore-modal="true" /* <-- O botão avisa o script para não interceptar ele */
              onClick={() => setIsOpen(false)}
              className="flex-1 py-2.5 px-4 rounded-xl bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 cursor-pointer no-underline"
            >
              Continuar <ChevronRight size={16} />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}