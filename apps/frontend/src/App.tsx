import { useState } from "react";
import { DashboardLayout } from "./components/layout/DashboardLayout";
import { CommercialDashboard } from "./pages/CommercialDashboard";
import { InventoryDashboard } from "./pages/InventoryDashboard";

function App() {
  const [activeView, setActiveView] = useState("comercial");
  return (
    <DashboardLayout activeView={activeView} setActiveView={setActiveView}>
      {/* Renderizado condicional: Solo se muestra el que coincida con el estado */}
      {activeView === "comercial" && <CommercialDashboard />}
      {activeView === "inventario" && <InventoryDashboard />}
    </DashboardLayout>
  );
}

export default App;