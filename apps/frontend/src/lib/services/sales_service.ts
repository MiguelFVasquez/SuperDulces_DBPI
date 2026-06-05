import axios from "axios";
import type { SalesMetrics, TicketAverage, TopProduct } from "../models/metrics";


export const api = axios.create({
  baseURL: import.meta.env.VITE_BASE_URL, 
});

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