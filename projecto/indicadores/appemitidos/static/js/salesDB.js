/*************************************************
 * SALES DASHBOARD FULL INTEGRATION (ESTABLE)
 *************************************************/
let footer_total = 0;
let table = null;
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
        footer_total.toLocaleString("en-US", {
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

function resetCascadingLocation(startLevel) {
    for (let i = startLevel; i <= 7; i++) {
        const el = document.getElementById(`filterLevel${i}`);
        if (el) el.innerHTML = `<option value="ALL">Todos</option>`;
    }
}

function initLocationCascade() {
    const l = n => document.getElementById(`filterLevel${n}`);

    loadLocation(1, null, l(1));

    l(1).addEventListener("change", () => {
        resetCascadingLocation(2);
        if (l(1).value !== "ALL") loadLocation(2, l(1).value, l(2));
    });
    l(2).addEventListener("change", () => {
        resetCascadingLocation(3);
        if (l(2).value !== "ALL") loadLocation(3, l(2).value, l(3));
    });
    l(3).addEventListener("change", () => {
        resetCascadingLocation(4);
        if (l(3).value !== "ALL") loadLocation(4, l(3).value, l(4));
    });
    l(4).addEventListener("change", () => {
        resetCascadingLocation(5);
        if (l(4).value !== "ALL") loadLocation(5, l(4).value, l(5));
    });
    l(5).addEventListener("change", () => {
        resetCascadingLocation(6);
        if (l(5).value !== "ALL") loadLocation(6, l(5).value, l(6));
    });
    l(6).addEventListener("change", () => {
        resetCascadingLocation(7);
        if (l(6).value !== "ALL") loadLocation(7, l(6).value, l(7));
    });
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

            /* =========================
               KPIs
            ========================= */
            $("#kpiTotalVentas").text(
                json.total_ventas.toLocaleString("es-EC", {
                    style: "currency",
                    currency: "USD"
                })
            );
            $("#kpiFacturas").text(json.facturas);
            $("#kpiNotas").text(json.notas);
            $("#kpiPartners").text(json.partners);

            /* =========================
            🔹 GRÁFICO DE BARRAS – Ventas por Mes
            ========================= */
            const labelsMes = json.ventas_mes.map(
                v => `${v.date__month}/${v.date__year}`
            );

            const dataMes = json.ventas_mes.map(
                v => v.total
            );

            if (ventasMesChart) ventasMesChart.destroy();

            ventasMesChart = new Chart(
                document.getElementById("chartVentasMes"),
                {
                    type: "bar",
                    data: {
                        labels: labelsMes,
                        datasets: [{
                            label: "Ventas por Mes",
                            data: dataMes,
                            backgroundColor: "rgba(54, 162, 235, 0.7)",
                            borderColor: "rgba(54, 162, 235, 1)",
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { position: "top" },
                            title: {
                                display: true,
                                text: "Ventas Mensuales"
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                }
            );
            /* =========================
               🔹 AQUÍ SE DECLARA labelsPartners
               ========================= */
            const labelsPartners = json.top_partners.map(
                v => v.partner__name
            );

            const dataPartners = json.top_partners.map(
                v => v.total
            );
            
            /* =========================
               Gráfico Doughnut
               ========================= */
            if (topPartnersChart) topPartnersChart.destroy();

            const colors = generarColores(dataPartners.length);

            topPartnersChart = new Chart(
                document.getElementById("chartTopPartners"),
                {
                    type: "doughnut",
                    data: {
                        labels: labelsPartners,
                        datasets: [{
                            data: dataPartners,
                            backgroundColor: colors
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        cutout: '55%',
                        plugins: {
                            legend: { display: false },
                            title: {
                                display: true,
                                text: 'Top 5 Partners por Ventas'
                            }
                        }
                    }
                }
            );

            /* =========================
               🔹 LEYENDA MANUAL (USA labelsPartners)
               ========================= */
            const legendContainer = document.getElementById("chartTopPartnersLegend");

            legendContainer.innerHTML = "";

            const totalPartners = parseFloat(dataPartners.reduce((a, b) => parseFloat(a) + parseFloat(b), 0));

            labelsPartners.forEach((label, index) => {
                const value = dataPartners[index];
                const percent = totalPartners
                    ? ((value / totalPartners) * 100).toFixed(1)
                    : 0;

                const color = topPartnersChart.data.datasets[0].backgroundColor[index];

                legendContainer.insertAdjacentHTML("beforeend", `
                    <li 
                        class="d-flex align-items-center mb-2 legend-item"
                        data-index="${index}"
                        style="cursor:pointer;"
                    >
                        <span style="
                            display:inline-block;
                            width:14px;
                            height:14px;
                            background-color:${color};
                            margin-right:8px;
                            border-radius:3px;
                        "></span>

                        <span class="small flex-grow-1">
                            ${label}
                        </span>

                        <span class="small text-muted me-2">
                            ${value.toLocaleString("es-EC", {
                                style: "currency",
                                currency: "USD"
                            })}
                        </span>

                        <span class="badge bg-light text-dark">
                            ${percent}%
                        </span>
                    </li>
                `);
            });
            
        });
}

/* -----------------------
   DATATABLES (CLAVE)
----------------------- */
function initTable() {

    table = $('#salesTable').DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: "/api/datatables_sales/",
            type: "GET",
            data: function (d) {
                return Object.assign(d, getParams());
            },
            dataSrc: function (json) {
                footer_total = parseFloat(json.totals.total_sum) || 0;
                updateFooterTotal();
                return json.data;
            }
        },
        columns: [
            { title: "Fecha" },
            { title: "Identificación" },
            { 
                title: "Partner",
                className: "text-start"
            },
            { title: "Factura" },
            { title: "Estab." },
            { 
                title: "Subtotal",
                className: "text-end fw-bold",
                render: $.fn.dataTable.render.number(
                    ',', '.', 2, '$'
                )
            },
            { 
                title: "Iva",
                className: "text-end fw-bold",
                render: $.fn.dataTable.render.number(
                    ',', '.', 2, '$'
                )
            },
            {
                title: "Total",
                className: "text-end fw-bold",
                render: $.fn.dataTable.render.number(
                    ',', '.', 2, '$'
                )
            }
        ],
        order: [[0, "desc"]],
        pageLength: 20,
        language: {
            url: "/static/datatables/es-ES.json"
        },
        buttons: ["copy", "excel", "csv", "pdf", "print"]
    });
}

/* -----------------------
   INIT
----------------------- */
document.addEventListener("DOMContentLoaded", () => {

    fetch("/api/sales_date_range/")
        .then(res => res.json())
        .then(data => {
            $("#filterDateFrom").val(data.min_date);
            $("#filterDateTo").val(data.max_date);

            initTable();        // 🔒 SOLO UNA VEZ
            updateDashboard(); // 🔒 SOLO UNA VEZ
        });

    initLocationCascade();

    document.getElementById("btnApplyFilters")
        .addEventListener("click", () => {
            table.ajax.reload(null, true); // ✅ CORRECTO
            updateDashboard();
        });

    fetch("/api/partners/")
        .then(res => res.json())
        .then(data => {
            const sel = document.getElementById("filterPartner");
            data.forEach(p =>
                sel.insertAdjacentHTML("beforeend",
                    `<option value="${p.id}">${p.name}</option>`)
            );
        });

    document.getElementById("chartTopPartnersLegend")
        .addEventListener("click", (e) => {
            const item = e.target.closest(".legend-item");
            if (!item) return;

            if (!topPartnersChart) return; // por si aún no se creó

            const index = Number(item.dataset.index);

            topPartnersChart.toggleDataVisibility(index);
            topPartnersChart.update();

            item.classList.toggle("opacity-50");
        });
    
    const legend = document.getElementById("chartTopPartnersLegend");

    legend.addEventListener("mouseover", (e) => {
        const item = e.target.closest(".legend-item");
        if (!item || !topPartnersChart) return;

        const index = Number(item.dataset.index);

        topPartnersChart.setActiveElements([
            { datasetIndex: 0, index }
        ]);
        topPartnersChart.update();
    });

    legend.addEventListener("mouseout", () => {
        if (!topPartnersChart) return;

        topPartnersChart.setActiveElements([]);
        topPartnersChart.update();
    });

    document.getElementById("btnShowAllPartners")
        .addEventListener("click", () => {
            if (!topPartnersChart) return;

            const count =
                topPartnersChart.data.datasets[0].data.length;
            
            for (let i = 0; i < count; i++) {
                if (!topPartnersChart.getDataVisibility(i)) {
                    topPartnersChart.toggleDataVisibility(i);
                }
            }

            topPartnersChart.update();

            document
                .querySelectorAll("#chartTopPartnersLegend .legend-item")
                .forEach(li => li.classList.remove("opacity-50"));
        });
});
