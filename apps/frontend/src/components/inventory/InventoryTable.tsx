import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Search } from "lucide-react";
import type { Inventory } from "@/lib/models/inventory"; // Ajusta la ruta a donde guardaste la interfaz

interface Props {
  data: Inventory[];
}

export function InventoryTable({ data }: Props) {
  const [searchTerm, setSearchTerm] = useState("");

  // Filtrado reactivo por SKU o Nombre
  const filteredData = data.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);

  const formatNumber = (value: number) =>
    new Intl.NumberFormat("es-CO").format(value);

  return (
    <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-colors duration-300">
      <CardHeader className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4">
        <CardTitle className="text-lg font-semibold text-slate-700 dark:text-slate-200">
          Estado de Bodega
        </CardTitle>
        
        {/* Buscador Integrado */}
        <div className="relative w-full sm:w-72">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <Search className="w-4 h-4 text-slate-400" />
          </div>
          <input
            type="text"
            className="bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-slate-900 dark:text-slate-100 text-sm rounded-lg focus:ring-brand-orange focus:border-brand-orange block w-full pl-10 p-2.5 transition-colors duration-300 outline-none"
            placeholder="Buscar producto o SKU..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="overflow-x-auto rounded-md border border-slate-200 dark:border-slate-800 max-h-[600px] overflow-y-auto relative">
          <table className="w-full text-sm text-left text-slate-500 dark:text-slate-400">
            <thead className="text-xs text-slate-700 uppercase bg-slate-50 dark:bg-slate-800/50 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10 shadow-sm">
              <tr>
                <th scope="col" className="px-6 py-3 font-medium">SKU</th>
                <th scope="col" className="px-6 py-3 font-medium">Producto</th>
                <th scope="col" className="px-6 py-3 font-medium text-right">Costo Unit.</th>
                <th scope="col" className="px-6 py-3 font-medium text-right">Stock</th>
                <th scope="col" className="px-6 py-3 font-medium text-right">Valor Total</th>
              </tr>
            </thead>
            <tbody>
              {filteredData.length > 0 ? (
                // Limitamos la renderización inicial para no saturar el DOM (puedes agregar paginación después)
                filteredData.slice(0, 200).map((item, index) => (
                  <tr
                    key={`${item.sku}-${index}`}
                    className="bg-white dark:bg-slate-900 border-b dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                  >
                    <td className="px-6 py-3 font-medium text-slate-900 dark:text-slate-200 whitespace-nowrap">
                      {item.sku}
                    </td>
                    <td className="px-6 py-3 truncate max-w-[250px]" title={item.name}>
                      {item.name}
                    </td>
                    <td className="px-6 py-3 text-right">
                      {formatCurrency(item.unit_cost)}
                    </td>
                    <td className="px-6 py-3 text-right">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${item.current_stock > 0 ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}`}>
                        {formatNumber(item.current_stock)}
                      </span>
                    </td>
                    <td className="px-6 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
                      {formatCurrency(item.total_value)}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-500 dark:text-slate-400">
                    No se encontraron resultados para "{searchTerm}"
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}