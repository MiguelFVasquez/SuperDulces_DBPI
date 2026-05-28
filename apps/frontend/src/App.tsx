import { useState } from 'react'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col items-center justify-center p-6 font-sans">
      <div className="max-w-md w-full bg-slate-800 rounded-xl p-8 shadow-2xl border border-slate-700 text-center">
        <h1 className="text-3xl font-bold text-indigo-400 mb-2">SuperDulces BI</h1>
        <p className="text-slate-400 mb-6 text-sm">Fase 1: Frontend Inicializado con Éxito</p>
        
        <div className="bg-slate-900/50 rounded-lg p-5 mb-6 border border-slate-700/50">
          <p className="text-xs text-emerald-400 font-mono mb-3">Vite + React + Tailwind CSS</p>
          <button 
            onClick={() => setCount((count) => count + 1)}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 text-white font-medium rounded-lg transition-colors shadow-md transform active:scale-95"
          >
            Contador de prueba: {count}
          </button>
        </div>
        
        <p className="text-xs text-slate-500">
          Estructura lista para el desarrollo del Dashboard[cite: 1].
        </p>
      </div>
    </div>
  )
}

export default App