import axios from "axios";
import type { SalesMetrics, TopProduct, TicketAverage } from "./models/metrics";
import type { Inventory } from "./models/inventory";
import type { HistoryRecord, ReceiptResponse } from "./models/receipts";
// Aquí definimos la URL de tu backend en FastAPI
const api = axios.create({
  baseURL: "http://127.0.0.1:8000", //URL base de la API
  headers: {
    "Content-Type": "application/json",
  },
});


//Endopoints para obtener los datos de la API

// Función para obtener las métricas de ventas
export const getSalesMetrics = async (): Promise<SalesMetrics> => {
  const response = await api.get("/metrics/sales"); 
  return response.data;
};

// Función para obtener los productos más vendidos
export const getTopProducts = async (): Promise<TopProduct[]> => {
  const response = await api.get("/metrics/top-products");
  return response.data;
};

//Función para obtener los productos menos vendidos
export const getLeastProducts = async (): Promise<TopProduct[]> => {
  const response = await api.get("/metrics/least-products");
  return response.data;
}

// Función para obtener el ticket promedio
export const getTicketAverage = async (): Promise<TicketAverage> => {
  const response = await api.get("/metrics/ticket-average");
  return response.data;
};

//Función para obtener el estado del inventario
export const getInventoryStatus = async (): Promise<Inventory[]> => {
  const response = await api.get("/inventory/");
  return response.data;
};

// Exportamos el objeto api para su uso en otros archivos
export const sendDocument = async (file: File): Promise<ReceiptResponse> => {
  const formData = new FormData();
  formData.append("file", file);
  // Enviamos el archivo al backend usando multipart/form-data  
  const response = await api.post<ReceiptResponse>("/receipts/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" }
  });
  
  return response.data;
};

// Función para obtener el historial de documentos procesados
// Asumiendo que esta función está en tu servicio de API o donde haces el fetch
export const getDocumentHistory = async (): Promise<HistoryRecord[]> => {
  const response = await api.get("/receipts/history");
  return response.data; // Esto devuelve el array que viste en Postman
};
//función para descargar el JSON de una factura específica
export const downloadJson = async (invoiceId: number): Promise<void> => {
  // Nota: Asegúrate de que esta ruta coincida con tu backend
  const response = await api.get(`/receipts/download-receipt/${invoiceId}`, {
    responseType: "blob", 
  });

  // Crear un enlace temporal para forzar la descarga en el navegador
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `factura_${invoiceId}.json`);
  document.body.appendChild(link);
  link.click();
  
  // Limpieza
  link.remove();
  window.URL.revokeObjectURL(url);
};


// Función para actualizar el stock mínimo de un producto
export const updateMinStock = async (sku: string, minStock: number): Promise<any> => {
  const response = await api.put(`/inventory/min-stock?sku=${sku}&min_stock=${minStock}`);
  return response.data;
};



export default api;