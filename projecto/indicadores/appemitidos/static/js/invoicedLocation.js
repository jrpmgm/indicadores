async function LoadData(pyears, pmonths, pgroupType, params) {
  
  try {
    const url = `/api/invoicedLocationdata/${pyears}/${pmonths}/${pgroupType}/?${params}`;
    const response = await fetch(url);
    const data = await response.json();

    const tbody = document.getElementById("tablaLocalizacionesBody");
    tbody.innerHTML = "";

    if (!data.resultados || data.resultados.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-muted">No hay datos disponibles</td></tr>`;
      return;
    }

    // Normalizamos los datos (incluyendo los IDs)
    const rows = data.resultados.map(item => ({
      continent: item.location__parent__parent__parent__parent__parent__parent__name || "-",
      continent_id: item.location__parent__parent__parent__parent__parent__parent__id || null,

      country: item.location__parent__parent__parent__parent__parent__name || "-",
      country_id: item.location__parent__parent__parent__parent__parent__id || null,

      region: item.location__parent__parent__parent__parent__name || "-",
      region_id: item.location__parent__parent__parent__parent__id || null,

      province: item.location__parent__parent__parent__name || "-",
      province_id: item.location__parent__parent__parent__id || null,

      city: item.location__parent__parent__name || "-",
      city_id: item.location__parent__parent__id || null,

      establishment: item.location__parent__name || "-",
      establishment_id: item.location__parent__id || null,

      point: item.location__name || "-",
      point_id: item.location__id || null,

      subtotal: parseFloat(item.subtotal || 0),
      iva: parseFloat(item.iva || 0),
      total: parseFloat(item.total || 0),
    }));

    /**
     * 🔧 Calculamos rowspans
     */
    const keys = ["continent", "country", "region", "province", "city", "establishment"];
    const calcularRowSpans = (rows, keys) => {
      const spans = {};
      keys.forEach(k => (spans[k] = {}));

      let countMap = {};

      for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const next = rows[i + 1];

        for (let key of keys) {
          const pathKey = keys
            .slice(0, keys.indexOf(key) + 1)
            .map(k => row[k])
            .join("|");

          countMap[pathKey] = (countMap[pathKey] || 0) + 1;

          if (!next ||
            keys.some((k, idx) => idx <= keys.indexOf(key) && row[k] !== next[k])
          ) {
            spans[key][pathKey] = countMap[pathKey];
            countMap[pathKey] = 0;
          }
        }
      }
      return spans;
    };

    const rowSpans = calcularRowSpans(rows, keys);

    // Construcción HTML
    let html = "";
    const last = {};

    rows.forEach((r) => {
      html += "<tr>";

      keys.forEach((key, idx) => {
        const pathKey = keys
          .slice(0, idx + 1)
          .map(k => r[k])
          .join("|");

        if (r[key] !== last[key]) {

          const idField = key + "_id";
          const locId = r[idField];
          html += `
            <td class="myfontLeft" rowspan="${rowSpans[key][pathKey]}">
              ${r[key]}
              <a href="#" 
                class="loc-link"
                data-id="${locId}"
                data-level="${key}"
              >
                ${iconozoom}
              </a>
            </td>
          `;

          keys.slice(idx).forEach(k => (last[k] = k === key ? r[key] : null));
        }
      });

      html += `
        <td>${r.point}</td>
        <td class="myfontRight">${formatterUSD(r.subtotal)}</td>
        <td class="myfontRight">${formatterUSD(r.iva)}</td>
        <td class="myfontRight fw-bold">${formatterUSD(r.total)}</td>
      </tr>`;
    });

    tbody.innerHTML = html;

  } catch (error) {
    console.error("Error cargando consolidado de localización:", error);
  }
}

// Llamar al backend
async function loadLocationDetails(level, locId) {
  const url = `/api/locationDetails/${level}/${locId}/${glb_chkyears}/${glb_chkmonths}/${glb_grouptype}/?${glb_params}/`;
  const response = await fetch(url);
  const data = await response.json();

  const tbody = document.getElementById("detailsBody");
  tbody.innerHTML = "";

  data.detalles.forEach(item => {
    console.log(item);
    tbody.innerHTML += `
      <tr>
        <td>${item.periodo}</td>
        <td class="myfontRight">${formatterUSD(item.subtotal)}</td>
        <td class="myfontRight">${formatterUSD(item.iva)}</td>
        <td class="myfontRight fw-bold">${formatterUSD(item.total)}</td>
      </tr>
    `;
  });

  document.getElementById("detailsSubtotal").innerHTML = formatterUSD(data.totales.subtotal);
  document.getElementById("detailsIva").innerHTML = formatterUSD(data.totales.iva);
  document.getElementById("detailsTotal").innerHTML = formatterUSD(data.totales.total);

  document.getElementById("detailsModalLabel").innerHTML = `Detalles de: <b>${data.location}</b>`;

  new bootstrap.Modal(document.getElementById("detailsModal")).show();
}

document.addEventListener("DOMContentLoaded", async () => {

  await LoadStarParameters();
  await LoadData(glb_chkyears, glb_chkmonths, "Mensual", glb_params);

  document.addEventListener('filters:apply', async (e) => {

    const filters = e.detail;
    glb_params = new URLSearchParams(filters.locations).toString();
    glb_locationFiltersText = Object.values(filters.locations).join(" / ");

    let pyears = filters.years.join(',');
    let pmonths = filters.months.join(',');
    
    glb_chkyears = pyears.split(',').map(s => s.trim()).filter(y => /^\d+$/.test(y)).join(',');
    glb_chkmonths = pmonths.split(',').map(s => s.trim()).filter(m => /^\d+$/.test(m) && Number(m) >= 1 && Number(m) <= 12).join(',');
    
    const pgroupType = "Mensual"; // puedes hacerlo dinámico si gustas

    await LoadData(glb_chkyears, glb_chkmonths, pgroupType, glb_params);
  });

  document.addEventListener("click", async (e) => {
    const link = e.target.closest(".loc-link");
    if (!link) return;

    e.preventDefault();

    const locId = link.dataset.id;
    const level = link.dataset.level;

    await loadLocationDetails(level, locId);
  });

  // Inicializar modal arrastrable
  makeModalDraggable("#detailsModal");
  makeModalDraggable("#filtersModal");
});