import os
import re
import threading
import time
from datetime import datetime, time as dt_time, timedelta
from pathlib import Path
import pandas as pd
import openpyxl
from flask import Flask, render_template_string, request, jsonify

# ------------------------------------------------------------
# CONFIGURACIÓN (CAMBIA SOLO ESTA RUTA PARA PRUEBAS LOCALES)
# ------------------------------------------------------------
# Para pruebas locales, usa una carpeta en tu PC con la estructura simulada
SERVIDOR_BASE = r"\\10.43.234.42\Calidad\05 Lab CMM\CMM"   # <--- CAMBIA AQUÍ para pruebas locales
# Para producción, cambiar a la ruta real del servidor:
# SERVIDOR_BASE = r"\\10.43.234.42\Calidad\05 Lab CMM"

ARCHIVO_REGISTRO = "registro_cmm.xlsx"
RAZONES = ["R1", "R2", "Desbudeo", "3D", "Otro"]
INTERVALO_MONITOREO = 10   # minutos entre búsquedas de archivos

app = Flask(__name__)

# ------------------------------------------------------------
# FUNCIONES PARA MANEJAR EL EXCEL (DOS HOJAS)
# ------------------------------------------------------------
def inicializar_excel():
    """Crea el archivo Excel con las dos hojas si no existe"""
    if os.path.exists(ARCHIVO_REGISTRO):
        return
    with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl') as writer:
        # Hoja de folios (resumen)
        df_folios = pd.DataFrame(columns=[
            "Folio", "CNC", "Numero_parte", "Producto", "Hora_ingreso",
            "Razon", "Equipo_CMM", "Cantidad_piezas", "Estado_resumen",
            "Hora_salida", "Confirmado"
        ])
        df_folios.to_excel(writer, sheet_name="Folios", index=False)
        # Hoja de piezas (detalle)
        df_piezas = pd.DataFrame(columns=[
            "Folio", "QR", "Hora_entrada", "Hora_salida", "Status_individual",
            "Ruta_archivo", "Lado", "Maquina", "Razon", "Equipo", "Numero_parte", "Producto"
        ])
        df_piezas.to_excel(writer, sheet_name="Piezas", index=False)

def guardar_folio(folio_data):
    """Guarda o actualiza una fila en la hoja Folios"""
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
    if folio_data["Folio"] in df["Folio"].values:
        df.loc[df["Folio"] == folio_data["Folio"], list(folio_data.keys())] = list(folio_data.values())
    else:
        df = pd.concat([df, pd.DataFrame([folio_data])], ignore_index=True)
    with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name="Folios", index=False)

def guardar_pieza(pieza_data):
    """Guarda una nueva pieza en la hoja Piezas"""
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
    df = pd.concat([df, pd.DataFrame([pieza_data])], ignore_index=True)
    with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name="Piezas", index=False)

def actualizar_pieza(qr, updates):
    """Actualiza campos de una pieza existente"""
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
    idx = df[df["QR"] == qr].index
    if len(idx) > 0:
        for key, value in updates.items():
            df.loc[idx, key] = value
        with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name="Piezas", index=False)

def obtener_piezas_por_folio(folio):
    """Devuelve todas las piezas de un folio como lista de dicts"""
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
    df_folio = df[df["Folio"] == folio]
    return df_folio.to_dict(orient="records")

def obtener_todas_piezas():
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
    return df.to_dict(orient="records")

def actualizar_resumen_folio(folio):
    """Recalcula el resumen de un folio basado en sus piezas"""
    piezas = obtener_piezas_por_folio(folio)
    if not piezas:
        return
    cantidad = len(piezas)
    ok_count = sum(1 for p in piezas if p.get("Status_individual") == "OK")
    nok_count = cantidad - ok_count
    estado_resumen = f"{ok_count} OK / {nok_count} NOK" if nok_count > 0 else f"{ok_count} OK"
    # Hora de salida = la máxima hora de salida de las piezas (si existe)
    horas_salida = [p["Hora_salida"] for p in piezas if p.get("Hora_salida")]
    hora_salida = max(horas_salida) if horas_salida else ""
    # Actualizar el folio en el Excel
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
    idx = df[df["Folio"] == folio].index
    if len(idx) > 0:
        df.loc[idx, "Cantidad_piezas"] = cantidad
        df.loc[idx, "Estado_resumen"] = estado_resumen
        df.loc[idx, "Hora_salida"] = hora_salida
        with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name="Folios", index=False)

# ------------------------------------------------------------
# FUNCIONES DE EXTRACCIÓN DE DATOS DE EXCEL (soporta .xls y .xlsx)
# ------------------------------------------------------------
def extraer_metadatos_excel(ruta_excel):
    """Extrae QR, número de parte, hora de salida, status OK/NOK desde .xls o .xlsx"""
    try:
        # Leer solo las celdas necesarias con pandas (sin cargar toda la hoja)
        df = pd.read_excel(ruta_excel, sheet_name="Report", header=None, usecols="B", nrows=20)
        qr = str(df.iloc[8, 0]) if len(df) > 8 else ""
        part_number = str(df.iloc[10, 0]) if len(df) > 10 else ""
        # Leer hora de salida (B5)
        hora_df = pd.read_excel(ruta_excel, sheet_name="Report", header=None, usecols="B", nrows=5)
        hora_cell = hora_df.iloc[4, 0] if len(hora_df) > 4 else ""
        if isinstance(hora_cell, (datetime, pd.Timestamp)):
            hora_salida = hora_cell.strftime("%H:%M")
        else:
            hora_salida = str(hora_cell)[:5] if hora_cell else ""
        # Leer status (columna G desde fila 16 en adelante)
        df_status = pd.read_excel(ruta_excel, sheet_name="Report", header=None, usecols="G", skiprows=15)
        status = "OK"
        for val in df_status[0]:
            if val == "NOK":
                status = "NOK"
                break
        return qr, part_number, hora_salida, status
    except Exception as e:
        print(f"Error leyendo {ruta_excel}: {e}")
        return None, None, None, None

def obtener_datos_de_ruta(ruta_excel):
    """Extrae máquina, lado, producto desde la estructura de carpetas"""
    partes = Path(ruta_excel).parts
    try:
        idx_cmm = [i for i, p in enumerate(partes) if p.startswith("CMM")][0]
        producto = partes[idx_cmm + 1]
        maquina = partes[idx_cmm + 2]
        lado = partes[idx_cmm + 3]
        return maquina, lado, producto
    except:
        return None, None, None

# ------------------------------------------------------------
# MONITOREO AUTOMÁTICO (busca archivos nuevos y actualiza)
# ------------------------------------------------------------
def buscar_y_actualizar_pendientes():
    """Busca en las carpetas CMM archivos del día de hoy y actualiza piezas pendientes"""
    hoy = datetime.now()
    año, mes, dia = hoy.year, hoy.month, hoy.day
    # Recorrer CMM1..CMM6 (puedes ampliar hasta CMM6)
    for i in range(1, 7):
        cmm_path = os.path.join(SERVIDOR_BASE, f"CMM{i}")
        if not os.path.isdir(cmm_path):
            continue
        # Recorrer modelos
        for modelo_dir in Path(cmm_path).iterdir():
            if not modelo_dir.is_dir():
                continue
            # Recorrer máquinas
            for maq_dir in modelo_dir.iterdir():
                if not maq_dir.is_dir():
                    continue
                # Recorrer lados
                for lado_dir in maq_dir.iterdir():
                    if not lado_dir.is_dir():
                        continue
                    fecha_dir = lado_dir / str(año) / f"{mes:02d}" / f"{dia:02d}"
                    if not fecha_dir.exists():
                        continue
                    # Buscar archivos .xls y .xlsx
                    for ext in ['*.xls', '*.xlsx']:
                        for archivo in fecha_dir.glob(ext):
                            qr, part_number, hora_salida, status = extraer_metadatos_excel(archivo)
                            if not qr:
                                continue
                            # Verificar si este QR ya está registrado en la hoja Piezas
                            df_piezas = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
                            if qr in df_piezas["QR"].values:
                                # Si ya existe, solo actualizamos los datos que puedan faltar
                                actualizar_pieza(qr, {
                                    "Hora_salida": hora_salida,
                                    "Status_individual": status,
                                    "Ruta_archivo": str(archivo),
                                    "Numero_parte": part_number
                                })
                                continue
                            # Obtener máquina, lado, producto de la ruta
                            maquina, lado, producto = obtener_datos_de_ruta(archivo)
                            if not maquina:
                                continue
                            # Buscar si hay una entrada previa (sin folio) para este QR
                            # Si no, la creamos con hora_entrada por defecto (actual - 1h para simular)
                            entrada_existente = df_piezas[df_piezas["QR"] == qr]
                            if not entrada_existente.empty:
                                # Actualizar los datos de esa entrada
                                actualizar_pieza(qr, {
                                    "Hora_salida": hora_salida,
                                    "Status_individual": status,
                                    "Ruta_archivo": str(archivo),
                                    "Lado": lado,
                                    "Maquina": maquina,
                                    "Numero_parte": part_number,
                                    "Producto": producto
                                })
                            else:
                                # Crear nueva entrada (simulamos hora_entrada como hace 1 hora)
                                hora_entrada_simulada = (datetime.now() - timedelta(hours=1)).strftime("%H:%M")
                                pieza_data = {
                                    "Folio": "",
                                    "QR": qr,
                                    "Hora_entrada": hora_entrada_simulada,
                                    "Hora_salida": hora_salida,
                                    "Status_individual": status,
                                    "Ruta_archivo": str(archivo),
                                    "Lado": lado,
                                    "Maquina": maquina,
                                    "Razon": "R1",  # valor por defecto
                                    "Equipo": i,
                                    "Numero_parte": part_number,
                                    "Producto": producto
                                }
                                guardar_pieza(pieza_data)
                            print(f"✅ Pieza procesada: {qr} - {maquina} {lado}")
    # Refrescar resúmenes de folios existentes
    df_folios = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
    for folio in df_folios["Folio"].dropna().unique():
        actualizar_resumen_folio(folio)

# ------------------------------------------------------------
# CIERRE DE TURNO: ASIGNAR FOLIOS A PIEZAS NO AGRUPADAS
# ------------------------------------------------------------
def cerrar_turno():
    """Agrupa piezas sin folio por máquina, formando grupos de 2 LH + 2 RH, asigna folio"""
    df_piezas = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
    pendientes = df_piezas[df_piezas["Folio"].isna() | (df_piezas["Folio"] == "")]
    if pendientes.empty:
        return
    # Agrupar por máquina
    for maquina, grupo_maq in pendientes.groupby("Maquina"):
        lh = grupo_maq[grupo_maq["Lado"] == "LH"].sort_values("Hora_entrada")
        rh = grupo_maq[grupo_maq["Lado"] == "RH"].sort_values("Hora_entrada")
        num_grupos = min(len(lh)//2, len(rh)//2)
        if num_grupos == 0:
            continue
        # Generar folios
        fecha_str = datetime.now().strftime("%d%m%y")
        df_folios = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
        folios_hoy = df_folios[df_folios["Folio"].str.startswith(fecha_str, na=False)]
        if folios_hoy.empty:
            consecutivo = 1
        else:
            numeros = [int(f.split("-")[1]) for f in folios_hoy["Folio"]]
            consecutivo = max(numeros) + 1
        for i in range(num_grupos):
            lh_pair = lh.iloc[2*i:2*i+2]
            rh_pair = rh.iloc[2*i:2*i+2]
            grupo = pd.concat([lh_pair, rh_pair])
            # Datos comunes
            parte = grupo.iloc[0]["Numero_parte"] if grupo.iloc[0]["Numero_parte"] else ""
            producto = grupo.iloc[0]["Producto"] if grupo.iloc[0]["Producto"] else ""
            razon = grupo.iloc[0]["Razon"] if grupo.iloc[0]["Razon"] else ""
            equipo = grupo.iloc[0]["Equipo"] if grupo.iloc[0]["Equipo"] else ""
            horas_entrada = grupo["Hora_entrada"]
            hora_ingreso = min(horas_entrada)
            horas_salida = grupo["Hora_salida"].dropna()
            hora_salida = max(horas_salida) if not horas_salida.empty else ""
            ok_count = (grupo["Status_individual"] == "OK").sum()
            nok_count = len(grupo) - ok_count
            estado_resumen = f"{ok_count} OK / {nok_count} NOK" if nok_count > 0 else f"{ok_count} OK"
            folio = f"{fecha_str}-{consecutivo:03d}"
            consecutivo += 1
            folio_data = {
                "Folio": folio,
                "CNC": maquina,
                "Numero_parte": parte,
                "Producto": producto,
                "Hora_ingreso": hora_ingreso,
                "Razon": razon,
                "Equipo_CMM": equipo,
                "Cantidad_piezas": len(grupo),
                "Estado_resumen": estado_resumen,
                "Hora_salida": hora_salida,
                "Confirmado": ""
            }
            guardar_folio(folio_data)
            # Actualizar las piezas con el folio
            for idx in grupo.index:
                df_piezas.loc[idx, "Folio"] = folio
            print(f"📌 Folio asignado: {folio} para máquina {maquina}")
        # Guardar cambios en piezas
        with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_piezas.to_excel(writer, sheet_name="Piezas", index=False)
    # Refrescar resúmenes
    df_folios = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
    for folio in df_folios["Folio"].dropna().unique():
        actualizar_resumen_folio(folio)

# ------------------------------------------------------------
# INTERFAZ WEB (PDA Y TABLA INTERACTIVA)
# ------------------------------------------------------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Registro CMM - Trazabilidad</title>
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.4/css/jquery.dataTables.min.css">
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.4/js/jquery.dataTables.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #2c3e50; color: white; padding: 10px; border-radius: 5px; }
        .registro-panel { background-color: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }
        label { font-weight: bold; }
        input, select { margin: 5px; padding: 8px; width: 200px; }
        button { padding: 8px 15px; background-color: #3498db; color: white; border: none; border-radius: 3px; cursor: pointer; }
        button:hover { background-color: #2980b9; }
        table { width: 100%; margin-top: 20px; }
        .confirmado { background-color: #d4edda; }
        .pendiente { background-color: #fff3cd; }
        .modal { display: none; position: fixed; z-index: 1; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.4); }
        .modal-content { background-color: #fefefe; margin: 5% auto; padding: 20px; border: 1px solid #888; width: 80%; border-radius: 5px; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close:hover { color: black; }
    </style>
</head>
<body>
<div class="header">
    <h2>Trazabilidad CMM - Entrada/Salida de Material</h2>
    <p>Monitoreo automático cada {{ intervalo }} minutos | Turno actual: {{ turno }}</p>
</div>

<div class="registro-panel">
    <h3>Registrar entrada de pieza</h3>
    <label>Escanear QR:</label>
    <input type="text" id="qr" placeholder="Código QR" autofocus>
    <label>Razón de medición:</label>
    <select id="razon">
        {% for r in razones %}
        <option value="{{ r }}">{{ r }}</option>
        {% endfor %}
    </select>
    <label>Máquina (CNC):</label>
    <input type="text" id="maquina" placeholder="Ej. A2, B3, C5">
    <label>Equipo CMM:</label>
    <input type="number" id="equipo" placeholder="Número (1-6)" min="1" max="6">
    <label>Lado:</label>
    <select id="lado">
        <option value="LH">LH (Izquierdo)</option>
        <option value="RH">RH (Derecho)</option>
    </select>
    <button onclick="registrarEntrada()">Registrar entrada</button>
    <span id="mensaje" style="margin-left: 20px;"></span>
</div>

<div>
    <button onclick="cerrarTurno()">Cerrar turno y asignar folios</button>
    <button onclick="location.reload()">Refrescar tabla</button>
</div>

<table id="tablaFolios" class="display">
    <thead>
        <tr>
            <th>Folio</th><th>CNC</th><th>Número de parte</th><th>Producto</th><th>Hora ingreso</th>
            <th>Razón</th><th>Equipo CMM</th><th>Cantidad piezas</th><th>Estado resumen</th><th>Hora salida</th><th>Confirmado</th><th>Acciones</th>
        </tr>
    </thead>
    <tbody>
        {% for f in folios %}
        <tr class="{% if f.Confirmado == 'SI' %}confirmado{% else %}pendiente{% endif %}">
            <td>{{ f.Folio }}</td><td>{{ f.CNC }}</td><td>{{ f.Numero_parte }}</td><td>{{ f.Producto }}</td>
            <td>{{ f.Hora_ingreso }}</td><td>{{ f.Razon }}</td><td>{{ f.Equipo_CMM }}</td>
            <td>{{ f.Cantidad_piezas }}</td><td>{{ f.Estado_resumen }}</td><td>{{ f.Hora_salida }}</td>
            <td>{{ f.Confirmado if f.Confirmado else 'Pendiente' }}</td>
            <td><button onclick="verDetalle('{{ f.Folio }}')">Detalle</button>
                {% if f.Confirmado != 'SI' %}
                <button onclick="confirmarFolio('{{ f.Folio }}')">Confirmar</button>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<!-- Modal para detalle -->
<div id="modalDetalle" class="modal">
    <div class="modal-content">
        <span class="close" onclick="cerrarModal()">&times;</span>
        <h3>Detalle del folio <span id="folioDetalle"></span></h3>
        <table id="tablaDetalle" class="display" style="width:100%">
            <thead><tr><th>QR</th><th>Hora entrada</th><th>Hora salida</th><th>Status</th><th>Lado</th></tr></thead>
            <tbody></tbody>
        </table>
    </div>
</div>

<script>
    $(document).ready(function() {
        $('#tablaFolios').DataTable({
            "order": [[0, "desc"]],
            "pageLength": 25
        });
    });

    function registrarEntrada() {
        var qr = document.getElementById('qr').value;
        var razon = document.getElementById('razon').value;
        var maquina = document.getElementById('maquina').value;
        var equipo = document.getElementById('equipo').value;
        var lado = document.getElementById('lado').value;
        if (!qr || !maquina || !equipo) {
            document.getElementById('mensaje').innerText = "Faltan datos";
            return;
        }
        fetch('/registrar_entrada', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({qr: qr, razon: razon, maquina: maquina, equipo: equipo, lado: lado})
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('mensaje').innerText = data.mensaje;
            document.getElementById('qr').value = '';
            document.getElementById('qr').focus();
            if (data.ok) location.reload();
        });
    }

    function verDetalle(folio) {
        fetch('/detalle_folio/' + folio)
        .then(response => response.json())
        .then(data => {
            document.getElementById('folioDetalle').innerText = folio;
            var tbody = document.querySelector('#tablaDetalle tbody');
            tbody.innerHTML = '';
            data.piezas.forEach(p => {
                var row = `<tr><td>${p.QR}</td><td>${p.Hora_entrada}</td><td>${p.Hora_salida}</td><td>${p.Status_individual}</td><td>${p.Lado}</td></tr>`;
                tbody.innerHTML += row;
            });
            $('#modalDetalle').show();
        });
    }

    function confirmarFolio(folio) {
        if (confirm('¿Confirmar este folio? Se marcará como cerrado.')) {
            fetch('/confirmar_folio', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({folio: folio})
            })
            .then(response => response.json())
            .then(data => {
                alert(data.mensaje);
                location.reload();
            });
        }
    }

    function cerrarTurno() {
        if (confirm('Cerrar turno actual y asignar folios a las piezas pendientes?')) {
            fetch('/cerrar_turno', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                alert(data.mensaje);
                location.reload();
            });
        }
    }

    function cerrarModal() {
        $('#modalDetalle').hide();
    }
    window.onclick = function(event) {
        if (event.target == document.getElementById('modalDetalle')) cerrarModal();
    }
</script>
</body>
</html>
"""

@app.route('/')
def index():
    hora_actual = datetime.now().time()
    turno = "1° (07:00-19:00)" if dt_time(7,0) <= hora_actual < dt_time(19,0) else "2° (19:00-07:00)"
    try:
        df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
        folios = df.to_dict(orient="records")
    except:
        folios = []
    return render_template_string(HTML_TEMPLATE, folios=folios, razones=RAZONES, intervalo=INTERVALO_MONITOREO, turno=turno)

@app.route('/registrar_entrada', methods=['POST'])
def registrar_entrada():
    data = request.json
    qr = data.get('qr')
    razon = data.get('razon')
    maquina = data.get('maquina')
    equipo = data.get('equipo')
    lado = data.get('lado')
    if not all([qr, razon, maquina, equipo, lado]):
        return jsonify({"ok": False, "mensaje": "Faltan datos"})
    df_piezas = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Piezas")
    if qr in df_piezas["QR"].values:
        return jsonify({"ok": False, "mensaje": "Este QR ya fue registrado"})
    pieza_data = {
        "Folio": "",
        "QR": qr,
        "Hora_entrada": datetime.now().strftime("%H:%M"),
        "Hora_salida": "",
        "Status_individual": "",
        "Ruta_archivo": "",
        "Lado": lado,
        "Maquina": maquina,
        "Razon": razon,
        "Equipo": equipo,
        "Numero_parte": "",
        "Producto": ""
    }
    guardar_pieza(pieza_data)
    return jsonify({"ok": True, "mensaje": f"Entrada registrada para {qr}"})

@app.route('/detalle_folio/<folio>')
def detalle_folio(folio):
    piezas = obtener_piezas_por_folio(folio)
    return jsonify({"piezas": piezas})

@app.route('/confirmar_folio', methods=['POST'])
def confirmar_folio():
    folio = request.json.get('folio')
    df = pd.read_excel(ARCHIVO_REGISTRO, sheet_name="Folios")
    idx = df[df["Folio"] == folio].index
    if len(idx) > 0:
        df.loc[idx, "Confirmado"] = "SI"
        with pd.ExcelWriter(ARCHIVO_REGISTRO, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name="Folios", index=False)
        return jsonify({"mensaje": f"Folio {folio} confirmado"})
    return jsonify({"mensaje": "Folio no encontrado"})

@app.route('/cerrar_turno', methods=['POST'])
def cerrar_turno_endpoint():
    cerrar_turno()
    return jsonify({"mensaje": "Turno cerrado. Folios asignados."})

# ------------------------------------------------------------
# MONITOR AUTOMÁTICO EN HILO SEPARADO
# ------------------------------------------------------------
def monitor_loop():
    while True:
        print(f"[{datetime.now()}] Ejecutando monitoreo...")
        buscar_y_actualizar_pendientes()
        time.sleep(INTERVALO_MONITOREO * 60)

# ------------------------------------------------------------
# INICIO DE LA APLICACIÓN
# ------------------------------------------------------------
if __name__ == "__main__":
    inicializar_excel()
    # Iniciar el hilo del monitor
    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    # Ejecutar servidor web
    app.run(host='0.0.0.0', port=5000, debug=False)