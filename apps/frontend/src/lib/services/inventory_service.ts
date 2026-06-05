import axios from "axios";
import type { Inventory } from "../models/inventory";


export const api = axios.create({
  baseURL: import.meta.env.VITE_BASE_URL, 
});


//Función para obtener el estado del inventario
export const getInventoryStatus = async (): Promise<Inventory[]> => {
  const response = await api.get("/inventory/");
  return response.data;
};

// Función para actualizar el stock mínimo de un producto
export const updateMinStock = async (sku: string, minStock: number): Promise<any> => {
  const response = await api.put(`/inventory/min-stock?sku=${sku}&min_stock=${minStock}`);
  return response.data;
};

