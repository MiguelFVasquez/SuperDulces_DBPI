import { type ReactNode, useState } from "react";
import { PackageSearch, Settings, Menu, ChevronLeft, Receipt, BadgeDollarSign, X  } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils"; // Utilidad de shadcn para manejar clases condicionales
import { ThemeToggle } from "../Theme/ThemeToggle";

interface DashboardLayoutProps {
  children: ReactNode;
  activeView: string; // Recibimos la vista actual desde App.tsx
  setActiveView: (view: string) => void; // Recibimos la función para cambiar la vista
}

export function DashboardLayout({ children, activeView, setActiveView }: DashboardLayoutProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const menuItems = [
    { id: "comercial",icon: BadgeDollarSign, label: "Comercial", color: "text-brand-orange", active: true },
    { id: "inventario", icon: PackageSearch, label: "Inventario", color: "text-brand-blue", active: false },
    { id:"facturas", icon: Receipt, label: "Facturas", color: "text-green-500", active: false},
  ];

  const handleSidebarItemClick = (id: string) => {
    setActiveView(id);
    setIsMobileMenuOpen(false); // Cerramos el menú en móvil al seleccionar
  };

  return (
    // Añadimos 'dark:bg-slate-950' y transición suave de color al contenedor raíz
    <div className="flex h-screen w-full bg-brand-light dark:bg-slate-950 overflow-hidden font-sans transition-colors duration-300">
      
      {/* Overlay para móvil (backdrop) */}
      {isMobileMenuOpen && (
        <div 
          className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Lateral */}
      <aside 
        className={cn(
          "bg-brand-dark text-slate-300 flex flex-col shadow-xl transition-all duration-300 ease-in-out z-50",
          "fixed inset-y-0 left-0 md:relative md:flex", // Posicionamiento responsive
          isMobileMenuOpen ? "translate-x-0 w-64" : "-translate-x-full md:translate-x-0", // Animación entrada móvil
          !isMobileMenuOpen && isCollapsed ? "md:w-20" : "md:w-64" // Ancho en desktop
        )}
      >
        {/* Cabecera Sidebar */}
        <div className="h-16 flex items-center px-6 border-b border-slate-700/50 justify-between flex-shrink-0">
          {(isMobileMenuOpen || !isCollapsed) && (
            <div className="flex items-center gap-2 overflow-hidden whitespace-nowrap">
              <div className="w-8 h-8 rounded-full bg-brand-orange flex-shrink-0 flex items-center justify-center text-white font-bold text-xl">
                S
              </div>
              <span className="text-lg font-bold text-white tracking-wide">
                Super<span className="text-brand-orange">Dulces</span>
              </span>
            </div>
          )}
          
          {/* Botón colapsar (Desktop) / Cerrar (Móvil) */}
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => isMobileMenuOpen ? setIsMobileMenuOpen(false) : setIsCollapsed(!isCollapsed)}
            className="text-slate-400 hover:bg-white/10 hover:text-white ml-auto"
          >
            {isMobileMenuOpen ? (
              <X className="h-5 w-5 md:hidden" />
            ) : isCollapsed ? (
              <Menu className="h-5 w-5" />
            ) : (
              <ChevronLeft className="h-5 w-5" />
            )}
          </Button>
        </div>

        {/* Menú de Navegación Principal */}
        <nav className="flex-1 py-6 px-3 space-y-2 overflow-y-auto">
          {(isMobileMenuOpen || !isCollapsed) && (
            <p className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">
              Analítica
            </p>
          )}
          
          {menuItems.map((item) => (
            <Button 
              key={item.label}
              variant="ghost" 
              onClick={() => handleSidebarItemClick(item.id)} 
              className={cn(
                "w-full justify-start hover:bg-white/10 hover:text-white transition-all",
                activeView === item.id && "bg-white/10 text-white",
                !isMobileMenuOpen && isCollapsed ? "px-2 justify-center" : "px-3"
              )}
            >
              <item.icon className={cn("h-5 w-5 flex-shrink-0", item.color, (isMobileMenuOpen || !isCollapsed) && "mr-3")} />
              {(isMobileMenuOpen || !isCollapsed) && <span>{item.label}</span>}
            </Button>
          ))}
        </nav>

        {/* 2. Sección Inferior Fija: Configuración y Selector de Tema */}
        <div className="p-3 border-t border-slate-700/40 space-y-1.5 bg-brand-dark/30 flex-shrink-0">
          <Button 
            variant="ghost" 
            className={cn(
              "w-full justify-start hover:bg-white/10 hover:text-white transition-all",
              !isMobileMenuOpen && isCollapsed ? "px-2 justify-center" : "px-3"
            )}
          >
            <Settings className={cn("h-5 w-5 flex-shrink-0 text-slate-400", (isMobileMenuOpen || !isCollapsed) && "mr-3")} />
            {(isMobileMenuOpen || !isCollapsed) && <span className="text-sm">Configuración</span>}
          </Button>

          <Separator className="bg-slate-700/40 my-2" />

          {/* Fila del Conmutador Adaptativo */}
          <div 
            className={cn(
              "flex items-center transition-all",
              !isMobileMenuOpen && isCollapsed ? "justify-center py-1" : "justify-between px-3 py-1"
            )}
          >
            {(isMobileMenuOpen || !isCollapsed) && (
              <span className="text-xs font-medium text-slate-400 select-none">
                Modo Oscuro
              </span>
            )}
            <ThemeToggle />
          </div>
        </div>
      </aside>

      {/* Área Principal Adaptativa al Dark Mode */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden bg-brand-light dark:bg-slate-950 transition-colors duration-300">
        {/* Header Superior con soporte oscuro */}
        <header className="h-16 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between px-4 md:px-8 shadow-sm transition-colors duration-300">
          <div className="flex items-center gap-3">
            {/* Burger Menu para móvil */}
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden text-slate-600 dark:text-slate-400"
            >
              <Menu className="h-6 w-6" />
            </Button>

            <h2 className="text-base md:text-xl font-semibold text-slate-800 dark:text-slate-100 transition-colors duration-300 line-clamp-1" >
              {activeView === "comercial" && "D. Comercial"}
              {activeView === "inventario" && "Inventario"}
              {activeView === "facturas" && "Facturas"}
              <span className="hidden sm:inline">
                {activeView === "comercial" && " Comercial"}
                {activeView === "inventario" && " de Inventario"}
                {activeView === "facturas" && " de Proveedores"}
              </span>
            </h2>
          </div>

          <div className="flex items-center gap-4 text-[10px] md:text-xs text-slate-400 dark:text-slate-500 font-medium tracking-wider">
            <span className="hidden xs:inline">SISTEMA MÉTRICAS</span> v1.0
          </div>
        </header>

        {/* Contenido Dinámico */}
        <div className="flex-1 overflow-auto p-4 md:p-8">
          {children}
        </div>
      </main>
    </div>
  );
}