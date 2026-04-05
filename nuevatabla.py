import pandas as pd
import os
import sqlite3
import warnings

# Limpiar consola y evitar avisos molestos
warnings.filterwarnings("ignore")
def clear(): os.system('cls' if os.name == 'nt' else 'clear')

# --- CONFIGURACIÓN DE COLORES ---
VERDE, AMARILLO, ROJO, CYAN, RESET = '\033[92m', '\033[93m', '\033[91m', '\033[36m', '\033[0m'

# --- 1. PREPARACIÓN Y MIGRACIÓN ---
def preparar_sistema():
    conexion = sqlite3.connect('inventario_gages.db')
    cursor = conexion.cursor()
    
    # Creamos tablas con tus nombres originales
    cursor.execute('''CREATE TABLE IF NOT EXISTS gages(
        "ID del Gage" TEXT PRIMARY KEY,
        Tipo TEXT,
        "Fecha de Calibración" DATE,
        "Próxima Calibración" DATE,
        "Técnico" TEXT
        )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_gage TEXT,
        fecha_calibracion DATE,
        resultado TEXT,
        tecnico TEXT,
        FOREIGN KEY(id_gage) REFERENCES gages("ID del Gage")
        )''')
    
    # Verificamos si la tabla está vacía para cargar el archivo de 805 items
    cursor.execute("SELECT COUNT(*) FROM gages")
    if cursor.fetchone()[0] == 0:
        archivo = 'DICASTAL MEXICO FASE ll.xlsx - Inspección calidad.csv'
        if os.path.exists(archivo):
            print(f"{AMARILLO}Cargando datos maestros de Dicastal...{RESET}")
            df_temp = pd.read_csv(archivo, skiprows=4)
            df_temp.columns = [str(c).strip() for c in df_temp.columns]
            
            df_migrar = pd.DataFrame()
            # Mapeo flexible para evitar errores de nombres
            col_id = [c for c in df_temp.columns if 'ID' in c][0]
            col_nom = [c for c in df_temp.columns if 'Nombre' in c][0]
            col_f_v = [c for c in df_temp.columns if 'verificación' in c][0]
            col_f_c = [c for c in df_temp.columns if 'caducidad' in c][0]

            df_migrar['ID del Gage'] = df_temp[col_id]
            df_migrar['Tipo'] = df_temp[col_nom]
            df_migrar['Fecha de Calibración'] = pd.to_datetime(df_temp[col_f_v], errors='coerce').dt.date
            df_migrar['Próxima Calibración'] = pd.to_datetime(df_temp[col_f_c], errors='coerce').dt.date
            df_migrar['Técnico'] = "CARGA INICIAL"
            
            df_migrar = df_migrar.dropna(subset=['ID del Gage'])
            df_migrar.to_sql('gages', conexion, if_exists='append', index=False)
            print(f"{VERDE}✅ {len(df_migrar)} elementos cargados con éxito.{RESET}")
    
    conexion.commit()
    conexion.close()

def obtener_color_estado(dias):
    if dias <= 0: return ROJO, "VENCIDO"
    if dias <= 15: return AMARILLO, "PROXIMO"
    return VERDE, "OK"

# --- EJECUCIÓN INICIAL ---
preparar_sistema()
hoy = pd.Timestamp.now().normalize()

while True:
    # Recargamos el DF en cada vuelta para tener datos frescos
    conexion = sqlite3.connect('inventario_gages.db')
    df = pd.read_sql_query("SELECT * FROM gages", conexion)
    conexion.close()
    
    df['Próxima Calibración'] = pd.to_datetime(df['Próxima Calibración'])
    df['dias faltantes'] = (df['Próxima Calibración'] - hoy).dt.days

    clear()
    print(f"{CYAN}***** BIENVENIDO A LA APP DE GAGES DICASTAL - FASE II *****{RESET}")
    
    vencidos_count = len(df[df['dias faltantes'] <= 0])
    print(f"\n{AMARILLO}--- RESUMEN: {len(df)} Equipos en Inventario ---{RESET}")
    if vencidos_count > 0: print(f"{ROJO}[!] ALERTA: {vencidos_count} equipos VENCIDOS.{RESET}")
    else: print(f"{VERDE}[OK] Todo el equipo está vigente.{RESET}")
    print("-" * 50)

    print("1.- Lista completa")
    print("2.- Ver próximos a vencer")
    print("3.- Reporte Ejecutivo (Excel)")
    print("4.- Buscar por ID")
    print("5.- Agregar nuevo Gage")
    print("6.- Actualizar Calibración")
    print("7.- Registrar Resultado")
    print("8.- Ver Historial")
    print("9.- Detalle de Alertas")
    print("10.- Salir")
    
    opcion = input("\nSelecciona una opción: ")

    if opcion == "1":
        clear()
        print(df[['ID del Gage', 'Tipo', 'Próxima Calibración', 'dias faltantes']].to_string(index=False))
        input("\nEnter para volver...")

    elif opcion == "2":
        try:
            limite = int(input("¿Días a futuro para el reporte? "))
            prox = df[(df['dias faltantes'] > 0) & (df['dias faltantes'] <= limite)]
            print(f"\n{'ID':<15} | {'DÍAS':<5} | {'ESTADO'}")
            for _, r in prox.iterrows():
                col, est = obtener_color_estado(r['dias faltantes'])
                print(f"{r['ID del Gage']:<15} | {col}{r['dias faltantes']:<5}{RESET} | {col}{est}{RESET}")
        except: print("Número inválido.")
        input("\nEnter para volver...")

    elif opcion == "3":
        clear()
        vencidos = df[df['dias faltantes'] <= 0].copy()
        if not vencidos.empty:
            nombre = f"Reporte_Dicastal_{pd.Timestamp.now().strftime('%d_%m_%Y')}.xlsx"
            writer = pd.ExcelWriter(nombre, engine='xlsxwriter')
            vencidos.to_excel(writer, sheet_name='Vencidos', index=False, startrow=3)
            # Insertar logo si existe
            if os.path.exists('logo_dicastal.png'):
                writer.sheets['Vencidos'].insert_image('A1', 'logo_dicastal.png', {'x_scale': 0.4, 'y_scale': 0.4})
            writer.close()
            print(f"{VERDE}Reporte generado: {nombre}{RESET}")
        else: print("No hay datos para exportar.")
        input("\nEnter para volver...")

    elif opcion == "4":
        id_b = input("ID a buscar: ").upper()
        res = df[df['ID del Gage'].str.upper() == id_b]
        if not res.empty:
            print(res[['ID del Gage', 'Tipo', 'Próxima Calibración', 'dias faltantes']])
        else: print("No encontrado.")
        input("\nEnter para volver...")

    elif opcion == "6" or opcion == "7":
        id_b = input("ID del Gage: ").upper()
        if id_b in df['ID del Gage'].values:
            n_f = input("Nueva fecha (YYYY-MM-DD): ")
            res_val = input("Resultado (Aprobado/Reprobado): ")
            tec = input("Tu nombre: ")
            conn = sqlite3.connect('inventario_gages.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE gages SET "Próxima Calibración" = ? WHERE "ID del Gage" = ?', (n_f, id_b))
            cursor.execute('INSERT INTO historial (id_gage, fecha_calibracion, resultado, tecnico) VALUES (?,?,?,?)',
                           (id_b, pd.Timestamp.now().strftime('%Y-%m-%d'), res_val, tec))
            conn.commit()
            conn.close()
            print(f"{VERDE}Actualizado correctamente.{RESET}")
        input("\nEnter para volver...")

    elif opcion == "10":
        break