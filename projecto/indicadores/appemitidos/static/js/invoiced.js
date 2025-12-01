// ==============================================
// 📊 EVENTO: Click sobre el ícono de mes
// ==============================================
document.addEventListener("DOMContentLoaded", function() {

  document.addEventListener('click', async (e) => {
    const link = e.target.closest('.link-month');
    glb_typedocument = document.getElementById('typedocument').value;

    if (!link) return;

    e.preventDefault();
    const month = link.dataset.month;
    const agrouptype = link.dataset.agrouptype || "Mensual";

    try {
      const baseUrl = '/api/consolidado_emitidos_filtrado/';
      const url = `${baseUrl}${glb_chkyears}/${glb_chkmonths}/${agrouptype}/${month}/${glb_typedocument}?${glb_params}`;
      const response = await fetch(url);
      const result = await response.json();

      const tbody = document.getElementById('detailsBody');
      const tSubtotal = document.getElementById('totalSubtotal');
      const tIva = document.getElementById('totalIva');
      const tTotal = document.getElementById('totalGeneral');

      tbody.innerHTML = '';
      let sumSubtotal = 0, sumIva = 0, sumTotal = 0;

      if (result.details && result.details.length > 0) {
        result.details.forEach(d => {
          const subtotal = parseFloat(d.subtotal) || 0;
          const iva = parseFloat(d.iva) || 0;
          const total = parseFloat(d.total) || 0;

          sumSubtotal += subtotal;
          sumIva += iva;
          sumTotal += total;

          const periodo = (() => {
            switch (agrouptype) {
              case 'Mensual':
              case 'Trimestral':
              case 'Semestral':
                return d.month_name ?? (d.month ? `${d.month}/${d.year}` : d.year ?? '');
              case 'Anual':
                return d.year ?? getMonthName(d.month);
              default:
                return d.periodo ?? d.month_name ?? d.month ?? d.year ?? '';
            }
          })();
          
          tbody.innerHTML += `
            <tr>
              <td>${periodo}</td>
              <td class="myfontRight">${ formatterUSD(subtotal) }</td>
              <td class="myfontRight">${ formatterUSD(iva) }</td>
              <td class="myfontRight">${ formatterUSD(total) }</td>
            </tr>`;
        });
      } else {
        tbody.innerHTML = `<tr><td colspan="4" class="text-muted">Sin datos</td></tr>`;
      }

      // Actualizar totales
      tSubtotal.textContent = formatterUSD(sumSubtotal);
      tIva.textContent = formatterUSD(sumIva);
      tTotal.textContent = formatterUSD(sumTotal);

      // Actualizar título
      document.getElementById('detailsModalLabel').innerText = `Detalles de ${result.month_name}`;
      const modal = new bootstrap.Modal(document.getElementById('detailsModal'));
      modal.show();

    } catch (error) {
      console.error("Error al cargar detalles:", error);
    }
  });

  // ========================================================
  // 🪟 FUNCIÓN: Modal arrastrable (estable, sin saltos)
  // ========================================================
  
  // Inicializar modal arrastrable
  makeModalDraggable("#detailsModal");
  makeModalDraggable("#filtersModal");
});
