/**
 * globals.js
 * Archivo de configuración global del proyecto.
 * Define constantes, funciones de formato y utilidades comunes.
 * Cargado desde base.html antes de otros scripts dependientes.
 */

// 🌎 CONFIGURACIÓN GLOBAL DEL PROYECTO
const GLOBALS = {
  apiBaseUrl: '/api/',               // Base para endpoints Django
  locale: 'es-EC',                   // Configuración regional
  currency: 'USD',                   // Moneda por defecto
  decimalDigits: 2,                  // Cantidad de decimales mostrados
  chartColors: [                     // Paleta de colores para gráficos
    '#2563eb', '#16a34a', '#f59e0b', '#dc2626',
    '#8b5cf6', '#ec4899', '#0ea5e9', '#14b8a6',
    '#f97316', '#4b5563', '#d97706', '#059669'
  ],
  chartBorderColor: 'rgba(0, 0, 0, 0.1)',
  chartTextColor: '#1f2937',
};

const iconozoom = '<i class="bi bi-zoom-in text-primary me-1"></i>';

// 💰 FORMATO DE MONEDA
function formatCurrency(value) {
  return new Intl.NumberFormat(GLOBALS.locale, {
    style: 'currency',
    currency: GLOBALS.currency,
    minimumFractionDigits: GLOBALS.decimalDigits,
  }).format(value || 0);
}

function formatterUSD(value) {
    if (value === 0 || value === "") {
        return "";
    }else {
        return new Intl.NumberFormat(GLOBALS.locale, {
            style: 'currency',
            currency: GLOBALS.currency,
            minimumFractionDigits: GLOBALS.decimalDigits,
        }).format(value || 0);
    }
}

function formatterPOR(value) {
    return new Intl.NumberFormat(GLOBALS.locale, {
        style: 'percent', // Establece el estilo a porcentaje
        maximumFractionDigits: GLOBALS.decimalDigits, // Máximo de dígitos decimales (ej. 75.89%)
    }).format(value / 100 || 0); // Divide por 100 para convertir a decimal
}

// 📅 NOMBRE DEL MES (equivalente a Python calendar.month_name)
function getMonthName(monthNumber) {
  const months = [
    '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  return months[monthNumber] || '';
}

// 📊 GENERADOR DE COLORES PARA GRÁFICOS (rotativo)
function generarColores(cantidad) {
  const colors = [];
  for (let i = 0; i < cantidad; i++) {
    colors.push(GLOBALS.chartColors[i % GLOBALS.chartColors.length]);
  }
  return colors;
}

// 🎨 Determinar color de contraste (para texto legible sobre fondo)
function getContrastColor(hexColor) {
  // Convierte HEX a RGB
  const c = hexColor.substring(1);
  const rgb = parseInt(c, 16);
  const r = (rgb >> 16) & 0xff;
  const g = (rgb >> 8) & 0xff;
  const b = rgb & 0xff;
  // Calcular luminancia
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return luminance > 0.6 ? '#000' : '#fff';
}

// ⚙️ CONFIGURACIÓN GLOBAL PARA CHART.JS
const chartDefaults = {
  responsive: true,
  plugins: {
    legend: {
      display: true,
      labels: {
        color: GLOBALS.chartTextColor,
        font: { size: 14, weight: 'bold' },
      },
    },
    tooltip: {
      backgroundColor: 'rgba(30,30,30,0.8)',
      titleFont: { size: 13 },
      bodyFont: { size: 12 },
      callbacks: {
        label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`,
      },
    },
  },
  scales: {
    x: {
      ticks: { color: GLOBALS.chartTextColor },
      grid: { color: GLOBALS.chartBorderColor },
    },
    y: {
      ticks: {
        color: GLOBALS.chartTextColor,
        callback: (val) => formatCurrency(val),
      },
      grid: { color: GLOBALS.chartBorderColor },
    },
  },
};

// 🧠 FUNCIONES AUXILIARES GLOBALES

// Esperar cierto tiempo (ej. para animaciones o delays)
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Mostrar alerta temporal en pantalla
function showToast(message, type = 'info') {
  const colors = { info: '#3b82f6', success: '#16a34a', error: '#dc2626' };
  const toast = document.createElement('div');
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    top: 1rem; right: 1rem;
    background-color: ${colors[type]};
    color: white;
    padding: 0.8rem 1.2rem;
    border-radius: 0.5rem;
    z-index: 1055;
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    font-size: 0.9rem;
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}


// 📦 EXPONER FUNCIONES Y VARIABLES GLOBALES
window.GLOBALS = GLOBALS;
window.formatCurrency = formatCurrency;
window.getMonthName = getMonthName;
window.generarColores = generarColores;
window.getContrastColor = getContrastColor;
window.chartDefaults = chartDefaults;
window.showToast = showToast;
window.sleep = sleep;



// Variables globales (visibles para todo el proyecto)
let glb_chkyears = null;
let glb_chkmonths = null;
let glb_typedocument = "ALL";
let glb_locationFiltersText = "";
let glb_params = "";
let glb_data = [];
let glb_grouptype = "Mensual";
let miGrafico = null;

// 🔸 Función para cargar parámetros iniciales (años, meses, etc.)
async function LoadStarParameters() {
  const locations = {
    continents: "-1",
    countries: "-1",
    regions: "-1",
    provinces: "-1",
    cities: "-1",
    establishments: "-1",
    points: "-1"
  };

  try {
    const response = await fetch(`/star_parameters/`);
    const data = await response.json();

    // Guardamos los valores globales
    glb_chkyears = data.years.join(",");
    glb_chkmonths = data.months.join(",");
    glb_typedocument = "ALL";
    glb_params = new URLSearchParams(locations).toString();

    /* console.log("✅ Parámetros cargados correctamente:");
    console.log("Años:", glb_chkyears, "Meses:", glb_chkmonths); */
  } catch (error) {
    console.error("❌ Error cargando parámetros iniciales:", error);
  }
}

/* // 🔹 globals.js
console.log("globals.js cargado correctamente ✅");
 */