import pandas as pd
import sqlite3
import os

def clear(): os.system('cls' if os.name == 'nt' else 'clear')

# --- CONFIGURACIÓN DE COLORES ---
VERDE, AMARILLO, ROJO, CYAN, RESET = '\033[92m', '\033[93m', '\033[91m', '\033[36m', '\033[0m'

def obtener_color_estado(dias):
    if dias <= 0: return ROJO, "VENCIDO"
    if dias <= 15: return AMARILLO, "PRÓXIMO"
    return VERDE, "VIGENTE"

hoy = pd.Timestamp.now().normalize()

while True:
    # Carga de datos de la DB (811 registros)
    conexion = sqlite3.connect('inventario_gages.db')
    df = pd.read_sql_query("SELECT * FROM gages", conexion)
    
    # Cálculos de fechas (1 año de vigencia)
    df['ultima_calibracion'] = pd.to_datetime(df['ultima_calibracion'])
    df['fecha_vence'] = df['ultima_calibracion'] + pd.DateOffset(years=1)
    df['dias_faltantes'] = (df['fecha_vence'] - hoy).dt.days

    clear()
    print(f"{CYAN}=================================================={RESET}")
    print(f"{CYAN}     SISTEMA GAGES DICASTAL - 10 OPCIONES         {RESET}")
    print(f"{CYAN}=================================================={RESET}")
    
    vencidos = len(df[df['dias_faltantes'] <= 0])
    print(f"\nResumen: Total {len(df)} | {ROJO}Vencidos: {vencidos}{RESET}")
    print("-" * 50)
    
    print("1.- Lista completa (Primeros 50)")
    print("2.- Ver próximos a vencer (15 días)")
    print("3.- Reporte Ejecutivo (Excel .xlsx)")
    print("4.- Buscar por ID o Cliente")
    print("5.- Agregar nuevo Gage manualmente")
    print("6.- Actualizar Fecha de Calibración")
    print("7.- Registrar Resultado (Historial)")
    print("8.- Ver Historial de un Gage")
    print("9.- Detalle de Alertas (Vencidos)")
    print("10.- Salir")
    
    op = input("\nSelecciona una opción: ")

    if op == "1":
        clear()
        print(df[['id_medicion', 'cliente', 'fecha_vence', 'dias_faltantes']].head(50).to_string(index=False))
        input("\nEnter para continuar...")

    elif op == "2":
        clear()
        prox = df[(df['dias_faltantes'] > 0) & (df['dias_faltantes'] <= 15)]
        print(prox[['id_medicion', 'cliente', 'dias_faltantes']] if not prox.empty else "No hay próximos a vencer.")
        input("\nEnter para continuar...")

    elif op == "3":
        nombre = f"Reporte_Gages_{pd.Timestamp.now().strftime('%d_%m_%y')}.xlsx"
        df.to_excel(nombre, index=False)
        print(f"{VERDE}✅ Reporte generado: {nombre}{RESET}")
        input("\nEnter para continuar...")

    elif op == "4":
        busq = input("Buscar ID o Cliente: ").upper()
        res = df[(df['id_medicion'].astype(str).str.contains(busq)) | (df['cliente'].astype(str).str.contains(busq, na=False))]
        print(res[['id_medicion', 'nombre', 'cliente', 'fecha_vence']] if not res.empty else "No encontrado.")
        input("\nEnter para continuar...")

    elif op == "5":
        # Opción para meter uno nuevo que no esté en los 811
        id_n = input("ID: "); nom_n = input("Nombre: "); cli_n = input("Cliente: ")
        desc_n = input("Descripción: "); fec_n = input("Última Calibración (YYYY-MM-DD): ")
        cursor = conexion.cursor()
        cursor.execute('INSERT INTO gages VALUES (?,?,?,?,?)', (id_n, nom_n, cli_n, desc_n, fec_n))
        conexion.commit()
        print(f"{VERDE}Gage {id_n} agregado.{RESET}")
        input("\nEnter para continuar...")

    elif op == "6" or op == "7":
        id_u = input("ID a actualizar: ")
        if id_u in df['id_medicion'].values:
            n_f = input("Nueva fecha (YYYY-MM-DD): ")
            res_val = input("Resultado (Aprobado/Reprobado): ")
            tec = input("Tu nombre: ")
            cursor = conexion.cursor()
            cursor.execute('UPDATE gages SET ultima_calibracion = ? WHERE id_medicion = ?', (n_f, id_u))
            cursor.execute('INSERT INTO historial (id_gage, fecha_cal, resultado, tecnico) VALUES (?,?,?,?)', 
                           (id_u, n_f, res_val, tec))
            conexion.commit()
            print(f"{VERDE}Actualizado correctamente.{RESET}")
        input("\nEnter para continuar...")

    elif op == "8":
        id_h = input("ID para ver historial: ")
        hist = pd.read_sql_query("SELECT * FROM historial WHERE id_gage = ?", conexion, params=(id_h,))
        print(hist if not hist.empty else "Sin historial.")
        input("\nEnter para continuar...")

    elif op == "9":
        clear()
        print(f"{ROJO}ALERTA: EQUIPOS VENCIDOS{RESET}")
        print(df[df['dias_faltantes'] <= 0][['id_medicion', 'cliente', 'fecha_vence']])
        input("\nEnter para continuar...")

    elif op == "10":
        conexion.close()
        break