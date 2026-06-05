import axios from "axios";
import type { HistoryRecord, ReceiptResponse } from "../models/receipts";

export const api = axios.create({
  baseURL: import.meta.env.VITE_BASE_URL, 
});

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

// Función para descargar el TXT de una factura específica
export const downloadTxt = async (invoiceId: number): Promise<void> => {
  const response = await api.get(`/receipts/download-receipt-txt/${invoiceId}`, {
    responseType: "blob", // Súper importante para que llegue como archivo
  });

  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `factura_${invoiceId}.txt`);
  document.body.appendChild(link);
  link.click();
  
  link.remove();
  window.URL.revokeObjectURL(url);
};