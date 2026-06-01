// Interfaz para el historial
export interface ProcessedInvoice {
  id: string;
  fileName: string;
  date: string;
  itemsCount: number;
  totalValue: number;
  items: ReceiptItem[];
}

export interface ReceiptItem {
  referencia_proveedor: string;
  referencia_syscafe: string;
  nombre: string;
  cantidad: number;
  costo_unitario: number;
  iva: number;
  homologado: boolean;
}

export interface ReceiptSummary {
  total_items: number;
  homologados_exitosos: number;
  pendientes_revision: number;
}

export interface ReceiptResponse {
  filename: string;
  items: ReceiptItem[];
  resumen: ReceiptSummary;
}