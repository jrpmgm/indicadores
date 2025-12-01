async function loadinvoices(filename) {
    const response = await fetch(`/api/load_excel/${filename}/`);
    const data = await response.json();
}

async function cargarEmitidosBD(anio, meses, ptable) {
    const response = await fetch(`/api/consolidado_emitidos/${anio}/${meses}/`);
    const data = await response.json();

    const tbody = document.getElementById(ptable);
    tbody.innerHTML = '';
    const labels = [];
    const valores = [];

    if (data.resultados.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay datos</td></tr>';
    } else {
        data.resultados.forEach(reg => {
            const fila = `
                <tr>
                    <td>${ reg.year }</td>
                    <td>${ reg.month_name }</td>
                    <td>${ reg.total_emitidos }</td>
                </tr>
            `;
            tbody.innerHTML += fila;
        });
    }
    return data.resultados; // Retorna los resultados para usarlos en la gráfica
}

async function cargarFacturasBD(pselectedMonths, pselectedYears, ptbody, phead, agrouptype, typedpcument, queryParams) {

    //const yearsString = selectedYears.slice(1).join(',');
    //const yearsString = pselectedYears.join(',');
    const yearsString = pselectedYears;
    // Construir la cadena de meses separados por comas
    //const monthsString = pselectedMonths.join(',');
    const monthsString = pselectedMonths;
    // Construir la URL completa
    // Asegúrate de que esta URL coincida con tu configuración de Django
    // Si estás ejecutando en localhost, podría ser algo como:
    // const baseUrl = 'http://localhost:8000/api/consolidado_emitidos/';
    // Para este ejemplo, usaremos una URL de ejemplo que puedes reemplazar
    const baseUrl = '/api/consolidado_emitidos/'; // Asume que el path base es correcto
    let url = `${baseUrl}${yearsString}/${monthsString}/${agrouptype}/${typedpcument}/?${queryParams}`;
    
    try {
        // Realizar la petición GET
        const response = await fetch(url);
        if (!response.ok) {
            // Manejar errores HTTP (ej. 400, 500)
            const errorData = await response.json();
            return;
        }

        const data = await response.json();
        if (data.resultados.length === 0) {
            ptbody.innerHTML = '<tr><td colspan="5" class="text-center">No hay datos</td></tr>';
        } else {
            let encabezado = '';
            switch (agrouptype) {
                case 'Mensual':
                    encabezado =` 
                    <tr>
                        <th class="myfontCenter">Mes</th>`
                    break;
                case 'Anual':
                    encabezado =` 
                    <tr>
                        <th class="myfontCenter">Año</th>`
                    break;
                case 'Trimestral':
                    encabezado =` 
                    <tr>
                        <th class="myfontCenter">Trimestre</th>`
                    break;
                case 'Semestral':
                    encabezado =` 
                    <tr>
                        <th class="myfontCenter">Semestre</th>`
                    break;
                default:
                    encabezado =``;
            }
            encabezado += `<th class="myfontCenter">Subtotal</th>
                        <th class="myfontCenter">Per. Anterior</th>
                        <th class="myfontCenter">Val. Inc.</th>
                        <th class="myfontCenter">Porc. Inc.</th>
                        <th class="myfontCenter">Iva</th>
                        <th class="myfontCenter">Total</th>
                    </tr> 
                    `

            ptbody.innerHTML = ''; // Limpiar el cuerpo de la tabla antes de llenarlo
            data.resultados.forEach(reg => {
                const periodo = agrouptype === 'Mensual' ? reg.month_name : reg.year;
                const periodoAnterior = reg.periodoanterior === null ? '' : reg.periodoanterior;
                const valordiferencia = reg.subtotal - periodoAnterior;
                const icono = valordiferencia >= 0 
                    ? '<i class="bi bi-arrow-up-circle-fill text-success me-1"></i>' 
                    : '<i class="bi bi-arrow-down-circle-fill text-danger me-1"></i>';
                const porcentajeIncremento = periodoAnterior !== 0 
                    ? (100-((periodoAnterior * 100) / reg.subtotal))
                    : '0.00'; // Evitar división por cero

                let periodoValue = '';
                let labelperiod = '';
                switch (agrouptype) {
                    case 'Mensual':
                        periodoValue = reg.month;
                        labelperiod = getMonthName(reg.month);
                        break;
                    case 'Anual':
                        periodoValue = reg.year;
                        labelperiod = reg.periodo;
                        break;
                    case 'Trimestral':
                        periodoValue = reg.quarter;
                        labelperiod = reg.periodo;
                        break;
                    case 'Semestral':
                        periodoValue = reg.semester;
                        labelperiod = reg.periodo;
                        break;
                    default:
                        periodoValue = '';
                }
                
                //alert(reg.periodo); reg.periodo
                let fila = `<tr>
                        <td class="myfontLeft">${ labelperiod } <a href="#" class="link-month" data-month="${periodoValue}" data-agrouptype="${agrouptype}">${ iconozoom }</a></td>`;
                fila +=`<td class="myfont myfontRight">${ formatterUSD(reg.subtotal) }</td>`;
                
                fila += `
                        <td class="myfont myfontRight">${ formatterUSD(periodoAnterior) }</td>
                        <td class="myfont myfontRight">${ icono } ${ formatterUSD(valordiferencia) }</td>
                        <td class="myfont myfontRight">${ icono } ${ formatterPOR(porcentajeIncremento) }</td>
                        <td class="myfont myfontRight">${ formatterUSD(reg.iva) }</td>
                        <td class="myfont myfontRight">${ formatterUSD(reg.total)}</td>
                `;
                ptbody.innerHTML += fila;
            });
            phead.innerHTML = encabezado; // Asignar encabezado a la tabla
        }
        return data.resultados; // Guardar los datos para graficar
    } catch (error) {
        // Manejar errores de red o de la petición
        console.error('Error al obtener datos:', error);
    }
}