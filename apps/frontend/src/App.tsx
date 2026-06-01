import { useState } from "react";
import { DashboardLayout } from "./components/layout/DashboardLayout";
import { CommercialDashboard } from "./pages/CommercialDashboard";
import { InventoryDashboard } from "./pages/InventoryDashboard";
import { ReceiptDashboard } from "./pages/ReceiptDashboard"; // Asegúrate de crear este componente para la sección de facturas

function App() {
  const [activeView, setActiveView] = useState("comercial");
  return (
    <DashboardLayout activeView={activeView} setActiveView={setActiveView}>
      {/* Renderizado condicional: Solo se muestra el que coincida con el estado */}
      {activeView === "comercial" && <CommercialDashboard />}
      {activeView === "inventario" && <InventoryDashboard />}
      {activeView === "facturas" && <ReceiptDashboard />} {/* Asegúrate de crear este componente para la sección de facturas */}
    </DashboardLayout>
  );
}

export default App;