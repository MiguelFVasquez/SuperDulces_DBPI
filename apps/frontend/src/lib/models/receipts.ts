// Interfaz para el historial
export interface ProcessedInvoice {
  id: string;
  fileName: string;
  date: string;
  itemsCount: number;
  totalValue: number;
  items: ReceiptItem[];
  syscafe_json: any[]; 
}

export interface ReceiptItem {
  sku: string;         
  nombre: string;
  cantidad: number;
  costo: number;       
  homologado: boolean;
  referencia?: string; 
}

export interface ReceiptSummary {
  total_items: number;
  homologados_exitosos: number;
  pendientes_revision: number;
}

export interface ReceiptResponse {
  filename?: string;
  items: ReceiptItem[];
  resumen: ReceiptSummary;
  syscafe_json: any[]; // El JSON con formato estricto que creamos en Python
}