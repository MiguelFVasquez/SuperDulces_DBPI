export interface SalesMetrics {
  total_transactions: number;
  total_units_sold: number;
}

export interface TopProduct {
  sku: string;
  name: string;
  total_qty: number;
  total_revenue: number;
  total_cost: number;
  total_profit: number;
  margin_percentage: number;
}


export interface TicketAverage {
  ticket_average: number;
}