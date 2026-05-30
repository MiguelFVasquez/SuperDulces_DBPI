import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type{ TopProduct } from "@/lib/models/metrics";

interface Props {
  data: TopProduct[];
}

export function TopProductsChart({ data }: Props) {
  // Función segura para formatear la moneda que no peleará con TypeScript
  const formatTooltipCurrency = (value: any) => {
    // Nos aseguramos de que el valor sea tratado numéricamente
    const numericValue = typeof value === 'number' ? value : Number(value);
    
    return new Intl.NumberFormat("es-CO", { 
      style: "currency", 
      currency: "COP",
      maximumFractionDigits: 0 // Sin decimales para que se vea más limpio
    }).format(numericValue);
  };

  return (
    <Card className="border-slate-200 shadow-sm col-span-full">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-slate-700">Top 5 Productos por Ingresos</CardTitle>
      </CardHeader>
      <CardContent className="h-[400px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f1f5f9" />
            <XAxis 
              type="number" 
              hide 
            />
            <YAxis 
              dataKey="name" 
              type="category" 
              width={180} // Le di un poco más de ancho para los nombres de tus productos
              tick={{ fontSize: 11, fill: "#64748b" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(value) => value.length > 25 ? `${value.substring(0, 25)}...` : value}
            />
            <Tooltip 
              cursor={{ fill: '#f8fafc' }}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              // Aplicamos nuestra nueva función segura aquí
              formatter={(value: any) => [formatTooltipCurrency(value), "Ingresos"]}
            />
            <Bar dataKey="total_revenue" radius={[0, 4, 4, 0]} barSize={35}>
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={index === 0 ? "#FF5A00" : "#fb923c"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}