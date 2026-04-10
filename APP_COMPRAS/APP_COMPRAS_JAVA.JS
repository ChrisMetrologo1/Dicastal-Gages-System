// 1. Variable Global para el total
let acumuladoTotal = 0;

// 2. Función para CARGAR datos al abrir la página
window.onload = function() {
    const listaGuardada = localStorage.getItem('miLista');
    const totalGuardado = localStorage.getItem('miTotal');

    if (listaGuardada) {
        document.getElementById('cuerpoTabla').innerHTML = listaGuardada;
    }
    if (totalGuardado) {
        acumuladoTotal = parseFloat(totalGuardado);
        document.getElementById('totalVenta').innerText = acumuladoTotal.toFixed(2);
    }
};

// 3. Función Principal: AGREGAR PRODUCTO
function agregarProducto() {
    // Captura de datos de los inputs
    const nombreInput = document.getElementById('producto');
    const precioInput = document.getElementById('precio');
    const cantidadInput = document.getElementById('cantidad');
    const tipo = document.querySelector('input[name="tipo"]:checked').value;

    const nombre = nombreInput.value;
    const precio = parseFloat(precioInput.value);
    const cantidad = parseFloat(cantidadInput.value);

    // Validación técnica: Que no falten datos
    if (nombre === "" || isNaN(precio) || isNaN(cantidad)) {
        alert("Por favor, llena todos los campos correctamente.");
        return;
    }

    // Cálculos
    const totalLinea = precio * cantidad;
    acumuladoTotal += totalLinea;

    // Crear la fila con el botón de eliminar
    const fila = `
        <tr>
            <td>${nombre}</td>
            <td>${tipo}</td>
            <td>$${precio.toFixed(2)}</td>
            <td>x ${cantidad}</td>
            <td>$${totalLinea.toFixed(2)}</td>
            <td>
                <button class="btn-eliminar" onclick="eliminarFila(this, ${totalLinea})">❌</button>
            </td>
        </tr>
    `;

    // Insertar en la tabla y actualizar pantalla
    document.getElementById('cuerpoTabla').innerHTML += fila;
    document.getElementById('totalVenta').innerText = acumuladoTotal.toFixed(2);

    // Guardar en la memoria del navegador
    guardarEnLocalStorage();

    // Limpiar los cuadros de texto para el siguiente producto
    nombreInput.value = "";
    precioInput.value = "";
    cantidadInput.value = "";
    nombreInput.focus();
}

// 4. Función para ELIMINAR una fila específica
function eliminarFila(boton, subtotal) {
    if (confirm("¿Quitar este producto?")) {
        // Restar del total
        acumuladoTotal -= subtotal;
        document.getElementById('totalVenta').innerText = acumuladoTotal.toFixed(2);

        // Borrar la fila visualmente
        const fila = boton.closest('tr');
        fila.remove();

        // Actualizar la memoria
        guardarEnLocalStorage();
    }
}

// 5. Función para BORRAR TODO
function borrarListaCompleta() {
    if (confirm("¿Estás seguro de borrar toda la lista?")) {
        acumuladoTotal = 0;
        document.getElementById('cuerpoTabla').innerHTML = "";
        document.getElementById('totalVenta').innerText = "0.00";
        localStorage.clear();
    }
}

// 6. Función auxiliar para guardar (No repetir código)
function guardarEnLocalStorage() {
    const htmlTabla = document.getElementById('cuerpoTabla').innerHTML;
    localStorage.setItem('miLista', htmlTabla);
    localStorage.setItem('miTotal', acumuladoTotal);
}