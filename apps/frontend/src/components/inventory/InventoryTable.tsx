import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Search,Pencil, Check, X, Loader2 } from "lucide-react";
import type { Inventory } from "@/lib/models/inventory"; // Ajusta la ruta a donde guardaste la interfaz
import { updateMinStock } from "@/lib/services/inventory_service";

interface Props {
  data: Inventory[];
  onUpdateSuccess?: () => void; // Prop para notificar al padre que se actualizó el stock mínimo (opcional)
}

export function InventoryTable({ data, onUpdateSuccess }: Props) {
  const [searchTerm, setSearchTerm] = useState("");
  // Estados para la edición en línea
  const [tableData, setTableData] = useState<Inventory[]>([]);
  const [editingSku, setEditingSku] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<number>(0);
  const [isSaving, setIsSaving] = useState<boolean>(false);

  // Estado para manejar un pequeño mensaje de éxito en la UI
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Filtrado reactivo por SKU o Nombre
  const filteredData = tableData.filter((item) =>
    item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    item.sku.toLowerCase().includes(searchTerm.toLowerCase())
  );
  // Sincronizar los datos entrantes con el estado local de la tabla
  useEffect(() => {
    setTableData(data);
  }, [data]);

  // Formateadores para moneda y números
  const formatCurrency = (value: number) =>
    new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);
  // Formateador para números sin decimales
  const formatNumber = (value: number) =>
    new Intl.NumberFormat("es-CO").format(value);

  // --- LÓGICA DE EDICIÓN ---
  
  // Función para iniciar la edición de un campo específico
  const startEditing = (sku: string, currentMinStock: number) => {
    setEditingSku(sku);
    setEditValue(currentMinStock);
  };
  // Función para cancelar la edición y volver al estado original
  const cancelEditing = () => {
    setEditingSku(null);
    setEditValue(0);
    setSuccessMessage(null); // Limpiamos mensajes anteriores
  };

  const handleSave = async (sku: string) => {
    setIsSaving(true);
    try {
      await updateMinStock(sku, editValue);
      
      // Actualizamos la tabla localmente para que se sienta instantáneo
      setTableData(prevData => 
        prevData.map(item => 
          item.sku === sku ? { ...item, min_stock: editValue } : item
        )
      );
      
      setEditingSku(null);
      
      // Notificamos en la UI
      setSuccessMessage(`✅ Stock mínimo de ${sku} actualizado a ${editValue}`);
      setTimeout(() => setSuccessMessage(null), 4000); // Se oculta en 4 segundos
      
      // Llamamos al padre para que recargue todo por detrás
      onUpdateSuccess?.();

    } catch (error) {
      console.error("Error al actualizar el stock mínimo:", error);
      alert("Hubo un error de conexión al guardar. Verifica el backend.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-colors duration-300">
      {successMessage && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50 bg-green-100 border border-green-400 text-green-700 px-4 py-2 rounded-md shadow-md animate-in fade-in slide-in-from-top-2 flex items-center gap-2 text-sm font-medium">
          {successMessage}
        </div>
      )}
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
                <th scope="col" className="px-4 sm:px-6 py-3 font-medium">SKU</th>
                <th scope="col" className="px-4 sm:px-6 py-3 font-medium">Producto</th>
                <th scope="col" className="hidden lg:table-cell px-6 py-3 font-medium text-right">Costo Unit.</th>
                <th scope="col" className="px-4 sm:px-6 py-3 font-medium text-right">Stock</th>
                <th scope="col" className="hidden md:table-cell px-6 py-3 font-medium text-right">Valor Total</th>
                <th scope="col" className="px-4 sm:px-6 py-3 font-medium text-right">Mínimo</th>
                <th scope="col" className="px-4 sm:px-6 py-3 font-medium text-center">Acciones</th>
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
                    <td className="px-4 sm:px-6 py-3 font-medium text-slate-900 dark:text-slate-200 whitespace-nowrap">
                      {item.sku}
                    </td>
                    <td className="px-4 sm:px-6 py-3 truncate max-w-[120px] sm:max-w-[250px]" title={item.name}>
                      {item.name}
                    </td>
                    <td className="hidden lg:table-cell px-6 py-3 text-right">
                      {formatCurrency(item.unit_cost)}
                    </td>
                    <td className="px-4 sm:px-6 py-3 text-right">
                      <span className={`px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-medium ${item.current_stock > 0 ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'}`}>
                        {formatNumber(item.current_stock)}
                      </span>
                    </td>
                    <td className="hidden md:table-cell px-6 py-3 text-right font-medium text-slate-700 dark:text-slate-300">
                      {formatCurrency(item.total_value)}
                    </td>
                    <td className="px-4 sm:px-6 py-3 text-center">
                      {editingSku === item.sku ? (
                        <input
                          type="number"
                          min="0"
                          value={editValue}
                          onChange={(e) => setEditValue(Number(e.target.value))}
                          className="w-14 sm:w-20 px-1 sm:px-2 py-1 text-center bg-white dark:bg-slate-950 border border-brand-orange rounded-md focus:outline-none focus:ring-2 focus:ring-brand-orange/50 dark:text-white"
                          autoFocus
                          disabled={isSaving}
                        />
                      ) : (
                        <span className={`px-2 py-0.5 sm:px-2.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-medium ${item.current_stock < item.min_stock ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300'}`}>
                          {formatNumber(item.min_stock)}
                        </span>
                      )}
                    </td>
                    {/* CELDA DE ACCIONES */}
                    <td className="px-2 sm:px-4 py-3 text-center">
                      {editingSku === item.sku ? (
                        <div className="flex items-center justify-center gap-1 sm:gap-2">
                          {isSaving ? (
                            <Loader2 className="h-4 w-4 animate-spin text-brand-orange" />
                          ) : (
                            <>
                              <button onClick={() => handleSave(item.sku)} className="p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded-md transition-colors" title="Guardar">
                                <Check className="h-4 w-4" />
                              </button>
                              <button onClick={cancelEditing} className="p-1 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-md transition-colors" title="Cancelar">
                                <X className="h-4 w-4" />
                              </button>
                            </>
                          )}
                        </div>
                      ) : (
                        <button 
                          onClick={() => startEditing(item.sku, item.min_stock)} 
                          className="p-1 sm:p-1.5 text-slate-400 hover:text-brand-blue hover:bg-slate-100 dark:hover:bg-slate-800 rounded-md transition-colors"
                          title="Editar stock mínimo"
                        >
                          <Pencil className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
                        </button>
                      )}
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