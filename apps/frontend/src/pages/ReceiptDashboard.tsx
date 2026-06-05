import React, { useState } from 'react';
import { Upload, FileJson, FileText, CheckCircle, History, FileSpreadsheet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { HistoryRecord, ReceiptItem, ReceiptResponse } from "@/lib/models/receipts"; // Define esta interfaz según tus necesidades 
import { useEffect } from 'react'; // Necesario para cargar al inicio
import { sendDocument, getDocumentHistory, downloadJson, downloadTxt } from "@/lib/services/receipts_services"; // Tus funciones de API

export function ReceiptDashboard() {
  const [fileStatus, setFileStatus] = useState<string>("Esperando factura del proveedor...");
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  
  // Estado para manejar el historial de archivos procesados
  const [history, setHistory] = useState<HistoryRecord[]>([]);


  const [extractedData, setExtractedData] = useState<ReceiptResponse | null>(null);


  // Cargar el historial de documentos procesados al montar el componente
  useEffect(() => {
    const fetchHistory = async () => {
        try {
            const data = await getDocumentHistory();
            setHistory(data);
        } catch (error) {
            console.error("Error al cargar historial:", error);
        }
    };
    fetchHistory();
  }, []);

  // Función para manejar la descarga de archivos (JSON o TXT)
  const handleExport = (format: 'JSON' | 'TXT') => {
    if (!extractedData) return;

    downloadInvoiceFile(
        extractedData.items,
        extractedData.syscafe_json, 
        extractedData.filename || currentFile?.name,
        format
    );
  };


const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
        const file = e.target.files[0];
        setCurrentFile(file);
        setFileStatus(`Subiendo y procesando: ${file.name}...`);
        setIsProcessing(true);
        setExtractedData(null);

        try {
            // 1. Subimos el documento (devuelve ReceiptResponse)
            const result = await sendDocument(file);

            // 2. Lo guardamos en extractedData (ahora TypeScript lo acepta)
            setExtractedData(result);

            setFileStatus(
                result.resumen.pendientes_revision > 0
                ? `¡Atención! Pendiente homologar ${result.resumen.pendientes_revision} productos.`
                : `¡Homologación 100% exitosa!`
            );

            // 3. Recargamos la tabla del historial (devuelve HistoryRecord[])
            const updatedHistory = await getDocumentHistory(); 
            setHistory(updatedHistory); 

        } catch (error: any) {
            console.error("Error al procesar el archivo:", error);
            setFileStatus(`Error: ${error.response?.data?.detail || "Fallo en la comunicación con el servidor"}`);
            setCurrentFile(null);
        } finally {
            setIsProcessing(false);
        }
    }
  };
    
  const downloadInvoiceFile = (
      items: ReceiptItem[], 
      syscafeJson: any[], // Nuevo parámetro para recibir la cabecera completa
      fileName: string | undefined, 
      format: 'JSON' | 'TXT'
  ) => {
      const nameToUse = fileName || 'factura_exportada';
      let finalFileName = nameToUse.split('.')[0]; 

      let content = '';

      if (format === 'JSON') {
          // CORRECCIÓN: Descarga el JSON de SysCafé, no el arreglo de React
          content = JSON.stringify(syscafeJson, null, 2);
          finalFileName += '.json';
      } else {
          content =
          'referencia,nombre,cantidad,precio\n' +
          items
              .map((i) => `${i.sku},"${i.nombre}",${i.cantidad},${i.costo}`)
              .join('\n');
          finalFileName += '.txt';
      }

      const blob = new Blob([content], {
          type: format === 'JSON' ? 'application/json' : 'text/plain',
      });

      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = finalFileName;
      link.click();
      URL.revokeObjectURL(url);
  };

  // FUNCION AUXILIAR PARA FORMATEAR VALORES MONETARIOS
  //const formatCurrency = (value: number) =>
  //  new Intl.NumberFormat("es-CO", { style: "currency", currency: "COP", maximumFractionDigits: 0 }).format(value);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Cabecera */}
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Automatización de Facturas</h1>
        <p className="text-slate-600 dark:text-slate-400 text-sm">
          Carga las facturas de tus proveedores. El sistema homologará las referencias y generará el archivo para SysCafé.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* COLUMNA IZQUIERDA: Zona de Carga y Acciones */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-colors duration-300">
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold text-slate-700 dark:text-slate-200">
                Cargar Documento
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Dropzone */}
              <div className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-colors ${isProcessing ? 'border-brand-orange bg-orange-50 dark:bg-brand-orange/10 animate-pulse' : 'border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 hover:bg-slate-100 dark:hover:bg-slate-800'}`}>
                {isProcessing ? (
                  <FileSpreadsheet className="h-10 w-10 text-brand-orange mb-4 animate-bounce" />
                ) : currentFile ? (
                  <CheckCircle className="h-10 w-10 text-green-500 mb-4" />
                ) : (
                  <Upload className="h-10 w-10 text-slate-400 mb-4" />
                )}
                
                <label className={`cursor-pointer px-4 py-2 rounded-lg font-medium text-sm transition-colors ${currentFile && !isProcessing ? 'bg-slate-200 text-slate-700 dark:bg-slate-800 dark:text-slate-300' : 'bg-brand-orange text-white hover:bg-orange-600'}`}>
                  {isProcessing ? 'Procesando...' : currentFile ? 'Cargar otra factura' : 'Seleccionar Archivo'}
                  <input type="file" className="hidden" accept=".xlsx, .csv, .pdf" onChange={handleFileUpload} disabled={isProcessing} />
                </label>
                <p className="mt-3 text-xs font-medium text-slate-500 text-center">{fileStatus}</p>
              </div>

              {/* Botones de Acción - Solo visibles tras procesar */}
              {currentFile && !isProcessing && (
                <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col gap-3">
                  <p className="text-xs font-medium text-slate-500 mb-1">Descargar formato para SysCafé:</p>
                  <button onClick={() => handleExport('JSON')} className="flex items-center justify-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2.5 rounded-lg text-sm font-medium transition-colors w-full">
                    <FileJson className="h-4 w-4" /> Formato JSON
                  </button>
                  <button onClick={() => handleExport('TXT')} className="flex items-center justify-center gap-2 bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors w-full">
                    <FileText className="h-4 w-4" /> Formato TXT
                  </button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* COLUMNA DERECHA: Historial */}
        <div className="lg:col-span-2">
          <Card className="border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm transition-colors duration-300 h-full">
            <CardHeader className="flex flex-row items-center justify-between pb-4">
              <CardTitle className="text-lg font-semibold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                <History className="h-5 w-5 text-brand-blue" />
                Historial de Procesamiento
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm text-left text-slate-500 dark:text-slate-400">
                  <thead className="text-xs text-slate-700 uppercase bg-slate-50 dark:bg-slate-800/50 dark:text-slate-300 border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-4 py-3 font-medium">Fecha</th>
                      <th className="px-4 py-3 font-medium">Archivo Origen</th>
                      <th className="px-4 py-3 font-medium text-center">Items</th>
                      <th className="px-4 py-3 font-medium text-center">Acción</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((record) => (
                      <tr key={record.id} className="border-b dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                        <td className="px-4 py-3 whitespace-nowrap">{record.created_at}</td>
                        <td className="px-4 py-3 font-medium text-slate-900 dark:text-slate-200">{record.file_name}</td>
                        <td className="px-4 py-3 text-center">
                          <span className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 px-2 py-1 rounded-md text-xs">
                            {record.total_items}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">
                            <div className="flex justify-center gap-2">
                                <button
                                title="Descargar JSON"
                                onClick={() => downloadJson(Number(record.id))}
                            className="p-1.5 text-slate-400 hover:text-brand-blue hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-md transition-colors"
                            >
                            <FileJson className="h-4 w-4" />
                            </button>

                                <button
                                title="Descargar TXT"
                                onClick={() => downloadTxt(Number(record.id))}
                            className="p-1.5 text-slate-400 hover:text-brand-orange hover:bg-orange-50 dark:hover:bg-orange-900/30 rounded-md transition-colors"
                            >
                                <FileText className="h-4 w-4" />
                                </button>
                            </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}