import { useEffect, useState } from "react";
import { Receipt, ShoppingCart, Package, TrendingUp } from "lucide-react";
import { KpiCard } from "@/components/KpiCard";
import { getSalesMetrics, getTicketAverage, getTopProducts }from "@/lib/api";
import { TopProductsChart } from "@/components/TopProductsChart";
import type { SalesMetrics, TicketAverage, TopProduct } from "@/lib/models/metrics";

export function CommercialDashboard() {
  const [sales, setSales] = useState<SalesMetrics | null>(null);
  const [ticket, setTicket] = useState<TicketAverage | null>(null);
  const [topProducts, setTopProducts] = useState<TopProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Ejecutamos ambas peticiones en paralelo para optimizar la carga
        const [salesData, ticketData, productsData] = await Promise.all([
          getSalesMetrics(),
          getTicketAverage(),
          getTopProducts()  
        ]);
        
        setSales(salesData);
        setTicket(ticketData);
        setTopProducts(productsData);
      } catch (error) {
        console.error("Error al cargar las métricas desde FastAPI:", error);
        // Fallbacks en caso de que el servidor esté apagado
        setSales({ total_transactions: 0, total_units_sold: 0 });
        setTicket({ ticket_average: 0 });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // Formateador de moneda colombiana
  const formatCurrency = (value: number) => 
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);

  // Formateador de números (para unidades y transacciones)
  const formatNumber = (value: number) => 
    new Intl.NumberFormat("es-CO").format(value);

  return (
    <div className="space-y-6">
      {/* Fila de KPIs mapeados a los datos reales */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          title="Transacciones"
          value={loading ? "..." : formatNumber(sales?.total_transactions || 0)}
          description="Total de operaciones registradas"
          icon={<ShoppingCart className="h-5 w-5 text-brand-orange" />}
        />
        <KpiCard
          title="Unidades Vendidas"
          value={loading ? "..." : formatNumber(sales?.total_units_sold || 0)}
          description="Volumen total de productos"
          icon={<Package className="h-5 w-5 text-brand-blue" />}
        />
        <KpiCard
          title="Ticket Promedio"
          value={loading ? "..." : formatCurrency(ticket?.ticket_average || 0)}
          description="Valor medio por transacción"
          icon={<Receipt className="h-5 w-5 text-brand-yellow" />}
        />
        {/* Tarjeta estática por ahora, luego la conectamos a otra métrica */}
        <KpiCard
          title="Estado del Sistema"
          value="En Línea"
          description="ETL ejecutado correctamente"
          icon={<TrendingUp className="h-5 w-5 text-green-500" />}
        />
      </div>

      {/* Espacio para la gráfica de Recharts */}
      <div className="grid gap-6 grid-cols-1">
        {loading ? (
          <div className="h-96 bg-white animate-pulse rounded-xl border border-slate-200" />
        ) : (
          <TopProductsChart data={topProducts} />
        )}
      </div>
    </div>
  );
}