import { useEffect, useState } from "react";
import { PackageOpen, DollarSign, AlertTriangle } from "lucide-react";
import { KpiCard } from "@/components/KpiCard"; 
import { getInventoryStatus } from "@/lib/api"; 
import type { Inventory } from "@/lib/models/inventory"; 
import { InventoryTable } from "@/components/inventory/InventoryTable"; 

export function InventoryDashboard() {
  const [inventory, setInventory] = useState<Inventory[]>([]);
  const [loading, setLoading] = useState(true);


  // 1. Extraemos la función para poder reutilizarla
  const fetchInventory = async () => {
    try {
      const data = await getInventoryStatus();
      setInventory(data);
    } catch (error) {
      console.error("Error al obtener el inventario:", error);
    } finally {
      setLoading(false);
    }
  };


 useEffect(() => {
    fetchInventory();
  }, []);

  // Cálculos dinámicos de métricas a partir del listado completo
  const totalSkus = inventory.length;
  const totalValue = inventory.reduce((acc, item) => acc + item.total_value, 0);
  const outOfStock = inventory.filter(item => item.current_stock === 0).length;

  // Formateadores
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);

  const formatNumber = (value: number) =>
    new Intl.NumberFormat("es-CO").format(value);

  return (
    <div className="space-y-6">
      {/* Fila de KPIs */}
      <div className="grid gap-6 md:grid-cols-3">
        <KpiCard
          title="Total Referencias (SKUs)"
          value={loading ? "..." : formatNumber(totalSkus)}
          description="Productos únicos en el catálogo"
          icon={<PackageOpen className="h-5 w-5 text-brand-blue" />}
        />
        <KpiCard
          title="Valorización de Bodega"
          value={loading ? "..." : formatCurrency(totalValue)}
          description="Capital total inmovilizado"
          icon={<DollarSign className="h-5 w-5 text-green-500" />}
        />
        <KpiCard
          title="Alertas de Agotados"
          value={loading ? "..." : formatNumber(outOfStock)}
          description="Productos con saldo en cero"
          icon={<AlertTriangle className="h-5 w-5 text-brand-orange" />}
        />
      </div>

      {/* Contenedor de la Tabla */}
      <div className="grid grid-cols-1">
        {loading && inventory.length === 0 ? (
          <div className="h-[600px] bg-white dark:bg-slate-900 animate-pulse rounded-xl border border-slate-200 dark:border-slate-800 transition-colors duration-300" />
        ) : (
          <InventoryTable data={inventory} onUpdateSuccess={fetchInventory} />
        )}
      </div>
    </div>
  );
}