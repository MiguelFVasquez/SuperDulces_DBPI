/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Colores extraídos del logo de SuperDulces
        brand: {
          orange: '#FF5A00', // Naranja principal (Fondo/Botones)
          blue: '#00B4D8',   // Azul cyan (Gráficas/Listón)
          yellow: '#FFD166', // Amarillo (Acentos/Textos)
          dark: '#1F2937',   // Gris oscuro (Textos principales)
          light: '#F8FAFC',  // Gris muy claro (Fondo del dashboard)
        }
      }
    },
  },
  plugins: [],
}