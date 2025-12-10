/*************************************************
 * SALES DASHBOARD FULL INTEGRATION
 *************************************************/
let footer_total = 0;
let table;
let ventasMesChart = null;
let topPartnersChart = null;

/* -----------------------
   Helpers
----------------------- */
function showLoading() {
    document.querySelectorAll(".kpi-value").forEach(el => {
        el.innerHTML = `<div class="spinner-border spinner-border-sm"></div>`;
    });
}
function updateFooterTotal() {
    document.getElementById("footer_total").textContent =
        footer_total.toLocaleString("es-EC", {
            style: "currency",
            currency: "USD",
        });
}
function getParams() {
    return {
        date_from: $('#filterDateFrom').val(),
        date_to: $('#filterDateTo').val(),
        type_doc: $('#filterTypeDocument').val(),
        partner_id: $('#filterPartner').val(),
        continent: $('#filterLevel1').val(),
        country: $('#filterLevel2').val(),
        region: $('#filterLevel3').val(),
        province: $('#filterLevel4').val(),
        city: $('#filterLevel5').val(),
        establishment: $('#filterLevel6').val(),
        point: $('#filterLevel7').val(),
    };
}

/* -----------------------
   LOCALIZACIÓN
----------------------- */
function loadLocation(level, parentId, element) {
    let url = parentId
        ? `/api/locations/${level}/${parentId}/`
        : `/api/locations/${level}/`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            element.innerHTML = `<option value="ALL">Todos</option>`;
            data.forEach(loc => {
                element.insertAdjacentHTML(
                    "beforeend",
                    `<option value="${loc.id}">${loc.name}</option>`
                );
            });
        });
}

function initLocationCascade() {
    const l = n => document.getElementById(`filterLevel${n}`);

    loadLocation(1, null, l(1));
    l(1).addEventListener("change", () => loadLocation(2, l(1).value, l(2)));
    l(2).addEventListener("change", () => loadLocation(3, l(2).value, l(3)));
    l(3).addEventListener("change", () => loadLocation(4, l(3).value, l(4)));
    l(4).addEventListener("change", () => loadLocation(5, l(4).value, l(5)));
    l(5).addEventListener("change", () => loadLocation(6, l(5).value, l(6)));
    l(6).addEventListener("change", () => loadLocation(7, l(6).value, l(7)));
}

/* -----------------------
   KPI & Charts
----------------------- */
function updateDashboard() {
    showLoading();
    const params = new URLSearchParams(getParams());

    fetch(`/api/sales_dashboard/?${params}`)
        .then(res => res.json())
        .then(json => {
            // KPIs
            $("#kpiTotalVentas").text(
                json.total_ventas.toLocaleString("es-EC", { style: "currency", currency: "USD" })
            );
            $("#kpiFacturas").text(json.facturas);
            $("#kpiNotas").text(json.notas);
            $("#kpiPartners").text(json.partners);

            // Chart Ventas x Mes
            const labelsMes = json.ventas_mes.map(v => `${v.date__month}/${v.date__year}`);
            const dataMes = json.ventas_mes.map(v => v.total);

            if (ventasMesChart) ventasMesChart.destroy();

            ventasMesChart = new Chart(document.getElementById("chartVentasMes"), {
                type: "bar",
                data: {
                    labels: labelsMes,
                    datasets: [{ label: "Ventas por Mes", data: dataMes }]
                }
            });

            // Chart Top Partners
            const labelsPartners = json.top_partners.map(v => v.partner__name);
            const dataPartners = json.top_partners.map(v => v.total);

            if (topPartnersChart) topPartnersChart.destroy();

            topPartnersChart = new Chart(document.getElementById("chartTopPartners"), {
                type: "pie",
                data: {
                    labels: labelsPartners,
                    datasets: [{ data: dataPartners }]
                }
            });
        });
}

/* -----------------------
   DATATABLES
----------------------- */
function initTable() {

    if ($.fn.DataTable.isDataTable('#salesTable')) {
        $('#salesTable').DataTable().destroy();
    }

    table = $('#salesTable').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: "/api/datatables_sales/",
            type: "GET",
            data: getParams,
            dataSrc: json => {
                footer_total = json.totals.total_sum || 0;
                updateFooterTotal();
                return json.data;
            }
        },
        dom: '<"d-flex justify-content-between mb-2"Bf>rt<"d-flex justify-content-between mt-2"lp>',
        buttons: ["copy", "excel", "csv", "pdf", "print"],
        order: [[0, "desc"]],
        pageLength: 10,
        language: {
            url: "/static/datatables/es-ES.json"
        },
    });
}

/* -----------------------
   INIT
----------------------- */
document.addEventListener("DOMContentLoaded", () => {
    initLocationCascade();
    initTable();
    updateDashboard();

    document.getElementById("btnApplyFilters")
        .addEventListener("click", () => {
            initTable();
            updateDashboard();
        });

    // Cargar Partners
    fetch("/api/partners/")
        .then(res => res.json())
        .then(data => {
            const sel = document.getElementById("filterPartner");
            data.forEach(p => sel.insertAdjacentHTML("beforeend", `<option value="${p.id}">${p.name}</option>`));
        });
});
