/********************************************
 * Sales DataTables - Server Side with Filters
 ********************************************/

let footer_total = 0;
let table;

// Inicializar DataTable con filtros incluidos
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
            data: function (d) {
                d.date_from = $('#filterDateFrom').val();
                d.date_to = $('#filterDateTo').val();
                d.type_doc = $('#filterTypeDocument').val();
                d.partner_id = $('#filterPartner').val();
            },
            dataSrc: function (json) {
                footer_total = json.totals.total_sum || 0;
                return json.data;
            }
        },
        dom: '<"d-flex justify-content-between mb-2"Bf>rt<"d-flex justify-content-between mt-2"lp>',
        buttons: [
            { extend: 'copyHtml5', text: '📋 Copiar' },
            { extend: 'excelHtml5', text: '📊 Excel' },
            { extend: 'csvHtml5', text: '📁 CSV' },
            { extend: 'pdfHtml5', text: '📄 PDF' },
            { extend: 'print', text: '🖨️ Imprimir' }
        ],
        order: [[0, 'desc']],
        pageLength: 10,
        lengthMenu: [10, 25, 50, 100],
        responsive: true,
        language: {
            url: "/static/datatables/es-ES.json",
            buttons: {
                copyTitle: 'Copiado',
                copySuccess: { _: '%d filas copiadas', 1: '1 fila copiada' }
            }
        },
        footerCallback: function () {
            document.getElementById("footer_total").textContent =
                Number(footer_total).toLocaleString("es-EC", {
                    style: "currency",
                    currency: "USD"
                });
        },
        columnDefs: [
            { targets: 5, className: "text-end fw-bold" }
        ]
    });
}


// Cargar lista de Partners desde Django
function loadPartners() {
    fetch("/api/partners/")
        .then(res => res.json())
        .then(data => {
            const select = document.getElementById("filterPartner");
            data.forEach(p => {
                select.insertAdjacentHTML("beforeend",
                    `<option value="${p.id}">${p.name}</option>`
                );
            });
        })
        .catch(err => console.error("Error cargando partners", err));
}


// Eventos iniciales
document.addEventListener("DOMContentLoaded", () => {
    loadPartners();
    initTable();

    document.getElementById("btnApplyFilters").addEventListener("click", () => {
        initTable(); // Recargar tabla con filtros
    });
});
