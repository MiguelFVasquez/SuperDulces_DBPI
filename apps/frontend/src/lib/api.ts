import axios from "axios";
import type { SalesMetrics, TopProduct, TicketAverage } from "./models/metrics";

// Aquí definimos la URL de tu backend en FastAPI
const api = axios.create({
  baseURL: "http://127.0.0.1:8000/metrics", //URL base de la API
  headers: {
    "Content-Type": "application/json",
  },
});


//Endopoints para obtener los datos de la API

// Función para obtener las métricas de ventas
export const getSalesMetrics = async (): Promise<SalesMetrics> => {
  const response = await api.get("/sales"); 
  return response.data;
};

// Función para obtener los productos más vendidos
export const getTopProducts = async (): Promise<TopProduct[]> => {
  const response = await api.get("/top-products");
  return response.data;
};

//Función para obtener los productos menos vendidos
export const getLeastProducts = async (): Promise<TopProduct[]> => {
  const response = await api.get("/least-products");
  return response.data;
}

// Función para obtener el ticket promedio
export const getTicketAverage = async (): Promise<TicketAverage> => {
  const response = await api.get("/ticket-average");
  return response.data;
};

export default api;