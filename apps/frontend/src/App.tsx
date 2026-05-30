import { DashboardLayout } from "./components/layout/DashboardLayout";
import { CommercialDashboard } from "./pages/CommercialDashboard";

function App() {
  return (
    <DashboardLayout>
      <CommercialDashboard />
    </DashboardLayout>
  );
}

export default App;