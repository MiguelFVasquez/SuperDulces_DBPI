import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useTheme } from "@/components/Theme/Theme-provider"; // <-- Importamos el hook
import type { TopProduct } from "@/lib/models/metrics";

interface Props {
  topProducts: TopProduct[];
  leastProducts: TopProduct[];
}

type ChartView = "top_revenue" | "top_qty" | "least_revenue";

export function ProductsAnalyticChart({ topProducts, leastProducts }: Props) {
  const [currentView, setCurrentView] = useState<ChartView>("top_revenue");
  const { theme } = useTheme(); // <-- Obtenemos el tema actual

  // Determinamos si es oscuro (manejando el caso "system")
  const isDark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
  // Configuración dinámica del gráfico según el estado del selector
  const getChartConfig = () => {
    switch (currentView) {
      case "top_qty":
        return {
          // Ordenamos el top 5 localmente por cantidad por si difieren las prioridades
          data: [...topProducts].sort((a, b) => b.total_qty - a.total_qty),
          dataKey: "total_qty",
          label: "Unidades Vendidas",
          title: "Top 5 Productos por Volumen (Unidades)",
          color: "#0070f3" // Azul dinámico para diferenciar volúmenes
        };
      case "least_revenue":
        return {
          data: leastProducts,
          dataKey: "total_revenue",
          label: "Ingresos",
          title: "Productos de Menor Rotación (Ingresos)",
          color: "#64748b" // Slate neutral para alertas de stock estancado
        };
      case "top_revenue":
      default:
        return {
          data: topProducts,
          dataKey: "total_revenue",
          label: "Ingresos",
          title: "Top 5 Productos por Ingresos",
          color: "#FF5A00" // Naranja vibrante para destacar el producto estrella
        };
    }
  };

  const config = getChartConfig();

  // Formateadores inteligentes
  const formatTooltip = (value: any) => {
    const num = typeof value === "number" ? value : Number(value);
    if (config.dataKey === "total_revenue") {
      return [new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(num), "Ingresos"];
    }
    return [new Intl.NumberFormat("es-CO").format(num), "Unidades"];
  };

  return (
    <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm w-full transition-colors duration-300">
      <CardHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6">
       <CardTitle className="text-lg font-semibold text-slate-700 dark:text-slate-200">
          {config.title}
        </CardTitle>
        
        {/* Selector de Vistas optimizado para UX */}
        <div className="flex bg-slate-100 dark:bg-slate-950 p-1 rounded-lg border border-slate-200 dark:border-slate-800 text-xs font-medium self-end sm:self-auto">
          <button
            onClick={() => setCurrentView("top_revenue")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              currentView === "top_revenue" 
                ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm font-semibold" 
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            Top Ingresos
          </button>
          <button
            onClick={() => setCurrentView("top_qty")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              currentView === "top_qty" 
                ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm font-semibold" 
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            Top Unidades
          </button>
          <button
            onClick={() => setCurrentView("least_revenue")}
            className={`px-3 py-1.5 rounded-md transition-all ${
              currentView === "least_revenue" 
                ? "bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm font-semibold" 
                : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
            }`}
          >
            Menor Rotación
          </button>
        </div>
      </CardHeader>

      <CardContent className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={config.data} layout="vertical" margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke={isDark ? "#334155" : "#f1f5f9"} /><XAxis type="number" hide />
            <YAxis 
              dataKey="name" 
              type="category" 
              width={160} 
              tick={{ fontSize: 10, fill: isDark ? "#94a3b8" : "#64748b" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => value.length > 22 ? `${value.substring(0, 22)}...` : value}
            />
            <Tooltip 
              cursor={{ fill: isDark ? '#1e293b' : '#f8fafc' }}
              contentStyle={{ 
                backgroundColor: isDark ? '#0f172a' : '#ffffff',
                borderColor: isDark ? '#1e293b' : '#f1f5f9',
                color: isDark ? '#f8fafc' : '#0f172a',
                borderRadius: '8px', 
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)' 
              }}
              itemStyle={{ color: isDark ? '#e2e8f0' : '#334155' }}
              formatter={formatTooltip}
            />
            <Bar dataKey={config.dataKey} radius={[0, 4, 4, 0]} barSize={30}>
              {config.data.map((_, index) => (
                <Cell 
                  key={`cell-${index}`} 
                  fill={currentView === "top_revenue" && index === 0 ? "#FF5A00" : config.color} 
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}