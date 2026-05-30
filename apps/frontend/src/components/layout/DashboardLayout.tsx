import { type ReactNode, useState } from "react";
import { LayoutDashboard, PackageSearch, Settings, Menu, ChevronLeft } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils"; // Utilidad de shadcn para manejar clases condicionales

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const menuItems = [
    { icon: LayoutDashboard, label: "Comercial", color: "text-brand-orange", active: true },
    { icon: PackageSearch, label: "Inventario", color: "text-brand-blue", active: false },
  ];

  return (
    <div className="flex h-screen w-full bg-brand-light overflow-hidden font-sans">
      
      {/* Sidebar Lateral */}
      <aside 
        className={cn(
          "bg-brand-dark text-slate-300 flex flex-col shadow-xl transition-all duration-300 ease-in-out hidden md:flex",
          isCollapsed ? "w-20" : "w-64"
        )}
      >
        {/* Cabecera Sidebar */}
        <div className="h-16 flex items-center px-6 border-b border-slate-700/50 justify-between">
          {!isCollapsed && (
            <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
              <div className="w-8 h-8 rounded-full bg-brand-orange flex-shrink-0 flex items-center justify-center text-white font-bold text-xl">
                S
              </div>
              <span className="text-lg font-bold text-white tracking-wide">
                Super<span className="text-brand-orange">Dulces</span>
              </span>
            </div>
          )}
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="text-slate-400 hover:bg-white/10 hover:text-white ml-auto"
          >
            {isCollapsed ? <Menu className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
          </Button>
        </div>

        {/* Menú de Navegación */}
        <nav className="flex-1 py-6 px-3 space-y-2">
          {!isCollapsed && (
            <p className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">
              Analítica
            </p>
          )}
          
          {menuItems.map((item) => (
            <Button 
              key={item.label}
              variant="ghost" 
              className={cn(
                "w-full justify-start hover:bg-white/10 hover:text-white transition-all",
                item.active && "bg-white/10 text-white",
                isCollapsed ? "px-2 justify-center" : "px-3"
              )}
            >
              <item.icon className={cn("h-5 w-5 flex-shrink-0", item.color, !isCollapsed && "mr-3")} />
              {!isCollapsed && <span>{item.label}</span>}
            </Button>
          ))}

          <Separator className="my-4 bg-slate-700/50" />
          
          <Button 
            variant="ghost" 
            className={cn(
              "w-full justify-start hover:bg-white/10 hover:text-white",
              isCollapsed ? "px-2 justify-center" : "px-3"
            )}
          >
            <Settings className={cn("h-5 w-5 flex-shrink-0 text-slate-400", !isCollapsed && "mr-3")} />
            {!isCollapsed && <span>Configuración</span>}
          </Button>
        </nav>
      </aside>

      {/* Área Principal */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-8 shadow-sm">
          <h2 className="text-xl font-semibold text-slate-800">Dashboard Comercial</h2>
          <div className="flex items-center gap-4 text-xs text-slate-400 font-medium">
            SISTEMA DE MÉTRICAS v1.0
          </div>
        </header>

        <div className="flex-1 overflow-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}