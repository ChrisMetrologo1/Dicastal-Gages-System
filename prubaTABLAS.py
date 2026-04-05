# importar la liberia pandas para manejo de datos
import pandas as pd
import os
import sqlite3
#creacion de base de datos
def crear_base_datos():
    conexion = sqlite3.connect('inventario_gages.db')
    cursor = conexion.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS gages(
        ID del Gage TEXT PRIMARY KEY,
        Tipo TEXT,
        Fecha de Calibración DATE,
        Próxima Calibración DATE,
        Técnico TEXT
        )
    ''')
    # Tabla de Historial corregida al 100%
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_gage TEXT,
        fecha_calibracion DATE,
        resultado TEXT,
        tecnico TEXT,
        FOREIGN KEY(id_gage) REFERENCES gages("ID del Gage")
        )''')
    conexion.commit()
    conexion.close()

crear_base_datos()
#le damos al sistema el tiempo de hoy
hoy = pd.Timestamp.now()
#aqui estamos llamando nuestro excel o csv dependiendo el caso
#df = pd.read_excel(r'C:\Users\ZEISS-CMM\Pictures\Chris Informacion\gages.xlsx')
#se cambio la ruta ahora una de servidor 
conexion = sqlite3.connect('inventario_gages.db')
df = pd.read_sql_query("SELECT * FROM gages", conexion)
conexion.close
df['Próxima Calibración'] = pd.to_datetime(df['Próxima Calibración'])
df['Fecha de Calibración'] = pd.to_datetime(df['Fecha de Calibración'])
#pasar la info a la base de datos
#conexion = sqlite3.connect('inventario_gages.db')
#df.to_sql('gages',conexion, if_exists='replace', index=False)
#conexion.close()
#print("datos migrados de excel a base de datos con exito")

# creamos la columna dias faltantes, restando la proxima claibracion con hoy y convirtiendo en un texto libre con.dt.days que solo lea dias
df['dias faltantes'] = (df['Próxima Calibración'] - hoy).dt.days
df['dias de retraso'] = df['dias faltantes']
gages_vencidos = df.loc[(df['dias faltantes'] < 0)].copy()
gages_vencidos['dias de retraso'] = gages_vencidos['dias de retraso'].abs()
df['Próxima Calibración'] = df['Próxima Calibración'].dt.date
df['Fecha de Calibración'] = df['Fecha de Calibración'].dt.date

VERDE = '\033[92m'
AMARILLO = '\033[93m'
ROJO = '\033[91m'
AZUL = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'
RESET = '\033[0m'

def obtener_color_estado(dias):
    if dias <= 0:
        return ROJO, "VENCIDO"
    elif dias <= 15:
        return AMARILLO, "PROXIMO"
    else:
        return VERDE, "OK"
    
        
#inicio de bucle
while True:
    print("*****bienvenido a la app de verificacion de gages DICASTAL***** ")
        # CALCULAMOS ALERTAS RÁPIDAS
    vencidos_count = len(df[df['dias faltantes'] <= 0])
    proximos_7_dias = len(df[(df['dias faltantes'] > 0) & (df['dias faltantes'] <= 7)])

    print(f"\n{AMARILLO}--- RESUMEN DE ESTADO ---{RESET}")
    if vencidos_count > 0:
        print(f"{ROJO}[!] ATENCIÓN: Tienes {vencidos_count} equipos VENCIDOS.{RESET}")
    else:
        print(f"{VERDE}[OK] No hay equipos vencidos.{RESET}")
        
    if proximos_7_dias > 0:
        print(f"{AMARILLO}[!] AVISO: {proximos_7_dias} equipos vencen en menos de una semana.{RESET}")
    print(f"{AMARILLO}--------------------------{RESET}\n")
    
    print("1.- Lista completa ")
    print("2.- Ver lista de proximos a vencer ")
    print("3.- ver lista de vencidos y exportar ")
    print("4.- Buscar gage por ID ")
    print("5.- Agregar nuevo Gage ")
    print("6.- Actualizar Calibraciónes ")
    print("7.- Registrar Calibraciónes ")
    print("8.- Historial ")
    print("9.- Detalle de Alertas ")
    print("10.- Salir ")
    opcion = input("que opcion eliges? ")
    if opcion == "1":
        os.system('cls')
        os.system('cls')
        print(f"{AMARILLO}===== Inventario Actual=====(BASE DE DATOS) ==={RESET}")
        vista_limpia = df[['ID del Gage','Tipo','Próxima Calibración','dias faltantes']]
        print(vista_limpia.to_string(index=False))
        input("presiona enter para volver al menu")
    elif opcion == "2":
        try:
            dias_limite = int(input("¿De cuántos días quieres ver el reporte? "))
            os.system('cls')
            
            # Filtramos los datos
            proximos = df.loc[(df['dias faltantes'] > 0) & (df['dias faltantes'] < dias_limite)]
            
            # Imprimimos un encabezado manual para que se vea ordenado
            print(f"{'ID GAGE':<15} | {'DÍAS':<6} | {'ESTADO':<10}")
            print("-" * 40)

            # Recorremos cada fila del filtro
            for index, fila in proximos.iterrows():
                d = fila['dias faltantes']
                
                # USAMOS TU FUNCIÓN AQUÍ
                color, estado = obtener_color_estado(d)
                
                # Imprimimos la fila con su color correspondiente
                # El :<15 es para que las columnas no se muevan
                print(f"{fila['ID del Gage']:<15} | {color}{d:<6}{RESET} | {color}{estado}{RESET}")
                
            input("\nPresiona Enter para volver al menú...")
            
        except ValueError:
            print(f"{ROJO}Error: Por favor digitalice solo números.{RESET}")
            input("\nPresiona Enter para continuar...")
    elif opcion == "3":
        os.system('cls')
        print(f"{ROJO}--- GENERANDO REPORTE EJECUTIVO DICASTAL ---{RESET}\n")
        
        vencidos = df[df['dias faltantes'] <= 0].copy()
        
        if not vencidos.empty:
            fecha_hoy_str = pd.Timestamp.now().strftime('%d_%m_%Y')
            fecha_letras = pd.Timestamp.now().strftime('%d de %B, %Y')
            nombre_archivo = f"Reporte_Vencidos_{fecha_hoy_str}.xlsx"
            
            writer = pd.ExcelWriter(nombre_archivo, engine='xlsxwriter')
            
            # --- AJUSTE CLAVE: Insertamos los datos a partir de la fila 4 (fila 3 en Python) ---
            # Dejamos las filas 0, 1 y 2 para el logo y el título
            vencidos.to_excel(writer, sheet_name='Vencidos', index=False, startrow=3)
            
            workbook  = writer.book
            worksheet = writer.sheets['Vencidos']

            # --- DEFINICIÓN DE FORMATOS ---
            # Estilo para el Título Principal
            titulo_fmt = workbook.add_format({
                'bold': True, 'font_size': 18, 'font_name': 'Calibri',
                'align': 'left', 'valign': 'vcenter'
            })
            
            # Estilo para la Fecha
            fecha_fmt = workbook.add_format({
                'font_size': 10, 'font_name': 'Calibri',
                'align': 'left', 'valign': 'vcenter'
            })

            # Estilo para los Encabezados de la Tabla
            encabezado_fmt = workbook.add_format({
                'bold': True, 'font_name': 'Calibri', 'text_wrap': True, 'valign': 'vcenter',
                'fg_color': '#D7E4BC', 'border': 1
            })
            
            # Estilo para celdas rojas (Vencidos)
            rojo_fmt = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})

            # --- INSERTAR IMAGEN Y TEXTO ---
            # 1. Insertamos el Logo. Ajusta 'x_scale' e 'y_scale' para cambiar el tamaño
            worksheet.insert_image('A1', 'logo_dicastal.png', {'x_scale': 0.5, 'y_scale': 0.5})
            
            # 2. Escribimos el Título y la Fecha
            worksheet.write('B1', 'INFORME DE EQUIPOS DE MEDICIÓN VENCIDOS', titulo_fmt)
            worksheet.write('B2', f'Dicastal Ramos Arizpe - Generado el: {fecha_letras}', fecha_fmt)

            # --- APLICAR FORMATO A LA TABLA ---
            # Ocultamos la fila 3 que .to_excel() usa para los encabezados por defecto
            worksheet.set_row(3, None, None, {'hidden': True})
            
            # Ajustar ancho de columnas automáticamente
            for i, col in enumerate(vencidos.columns):
                column_len = max(vencidos[col].astype(str).str.len().max(), len(col)) + 2
                worksheet.set_column(i, i, column_len)

            # Formato condicional: Si días faltantes es <= 0, pintar rojo
            col_idx = vencidos.columns.get_loc('dias faltantes')
            
            # La tabla empieza en la fila 4, pero como ocultamos la 3, el conditional empieza en fila 4 real
            worksheet.conditional_format(4, col_idx, len(vencidos) + 4, col_idx, {
                'type':     'cell',
                'criteria': '<=',
                'value':    0,
                'format':   rojo_fmt
            })

            writer.close()
            print(f"\n{VERDE}¡Reporte profesional Dicastal generado!{RESET}")
            print(f"Archivo: {nombre_archivo}")
        else:
            print(f"\n{AMARILLO}No hay equipos vencidos para reportar.{RESET}")
            
        input("\nPresiona Enter para volver al menú...")
    elif opcion == "4":
        os.system('cls')
        busqueda = input("ingresa el ID del gage ").strip().upper()
        Resultado = df[df['ID del Gage'].str.upper() == busqueda]
        if not Resultado.empty:
            print(f"{VERDE} -- Informacion encontrada --{RESET}")
            for index, fila in Resultado.iterrows():
                d = fila['dias faltantes']
                color, estado = obtener_color_estado(d)
                print(f"ID: {fila['ID del Gage']}")
                print(f"Tipo: {fila['Tipo']}")
                print(F"Próxima Calibración: {fila['Próxima Calibración']}")
                print(F"Dias por vencer: {color}{d}{RESET}({estado})")
                input("presiona Entrer para volver al menu ")
                os.system('cls')
        else:
            print(F" {ROJO}ERROR: El ID {'busqueda'} no existe en la base de datos. {RESET}")
            input("presiona Entrer para volver al menu ")
    elif opcion == "5":
        os.system('cls')
        print("--- REGISTRO DE NUEVO INSTRUMENTO ---")
        
        # Pedimos los datos al usuario
        nuevo_id = input("ID del Gage: ").strip().upper()
        tipo = input("Tipo de instrumento: ")
        f_cal = input("Fecha de última calibración (YYYY-MM-DD): ")
        p_cal = input("Fecha de próxima calibración (YYYY-MM-DD): ")
        tecnico = input("Nombre del técnico: ")

        # Conectamos a la base de datos para insertar
        conexion = sqlite3.connect('inventario_gages.db')
        cursor = conexion.cursor()
        
        try:
            # Usamos INSERT INTO para guardar los nuevos datos
            # Los nombres de las columnas deben ser EXACTOS a como los creaste en la def crear_base_datos
            cursor.execute('''
                INSERT INTO gages ("ID del Gage", "Tipo", "Fecha de Calibración", "Próxima Calibración", "Técnico")
                VALUES (?, ?, ?, ?, ?)
            ''', (nuevo_id, tipo, f_cal, p_cal, tecnico))
            
            conexion.commit() # ¡Muy importante! Sin el commit no se guardan los cambios
            print(f"\n{VERDE}¡Éxito! El gage {nuevo_id} ha sido registrado.{RESET}")
            
            # REFRESCAMOS EL DATAFRAME para que el nuevo gage aparezca en las listas
            df = pd.read_sql_query("SELECT * FROM gages", conexion)
            # Volvemos a calcular los días (esto es clave)
            df['Próxima Calibración'] = pd.to_datetime(df['Próxima Calibración'])
            df['dias faltantes'] = (df['Próxima Calibración'] - hoy).dt.days
            
        except sqlite3.IntegrityError:
            print(f"\n{ROJO}ERROR: El ID {nuevo_id} ya existe en la base de datos.{RESET}")
        except Exception as e:
            print(f"\n{ROJO}Error inesperado: {e}{RESET}")
        
        conexion.close()
        input("\nPresiona Enter para volver al menú...")
    elif opcion == "6":
        os.system('cls')
        print("--- REGISTRAR NUEVA CALIBRACIÓN ---")
        id_buscado = input("Introduce el ID del Gage que acabas de calibrar: ").upper()
        
        # 1. Pedimos los nuevos datos
        nueva_fecha = input("Nueva fecha de vencimiento (YYYY-MM-DD): ")
        resultado = input("¿Cuál fue el resultado? (Aprobado/Reprobado): ")
        tecnico = input("Nombre del técnico que calibró: ")

        conexion = sqlite3.connect('inventario_gages.db')
        cursor = conexion.cursor()

        # Actualizamos la tabla principal
        cursor.execute('''UPDATE gages 
                          SET "Próxima Calibración" = ? 
                          WHERE "ID del Gage" = ?''', (nueva_fecha, id_buscado))

        # Insertamos en el historial
        cursor.execute('''INSERT INTO historial (id_gage, fecha_calibracion, resultado, tecnico) 
                          VALUES (?, ?, ?, ?)''', (id_buscado, pd.Timestamp.now().strftime('%Y-%m-%d'), resultado, tecnico))

        conexion.commit()
        conexion.close()
        
        print(f"\n{VERDE}¡Historial actualizado y fecha reprogramada!{RESET}")
        input("\nPresiona Enter para continuar...")
    elif opcion == "7":
        os.system('cls')
        print(f"{AMARILLO}--- REGISTRAR RESULTADO DE CALIBRACIÓN ---{RESET}\n")
        id_buscado = input("ID del Gage calibrado: ").strip().upper()
        
        # Verificamos si el Gage existe antes de seguir
        if id_buscado in df['ID del Gage'].values:
            nueva_fecha_vencimiento = input("Nueva fecha de PRÓXIMA calibración (YYYY-MM-DD): ")
            resultado = input("Resultado (Aprobado/Reprobado/Ajuste): ")
            tecnico_cal = input("Nombre del técnico que realizó la prueba: ")
            notas = input("Notas adicionales: ")

            conexion = sqlite3.connect('inventario_gages.db')
            cursor = conexion.cursor()

            try:
                # 1. Actualizamos la fecha en la tabla principal (GAGES)
                cursor.execute('''UPDATE gages 
                                  SET "Próxima Calibración" = ? 
                                  WHERE "ID del Gage" = ?''', (nueva_fecha_vencimiento, id_buscado))

                # 2. Guardamos el registro eterno en la tabla HISTORIAL
                # La fecha de hoy se pone automáticamente para el registro
                fecha_hoy_registro = pd.Timestamp.now().strftime('%Y-%m-%d')
                
                cursor.execute('''INSERT INTO historial (id_gage, fecha_calibracion, resultado, tecnico) 
                                  VALUES (?, ?, ?, ?)''', 
                               (id_buscado, fecha_hoy_registro, resultado, tecnico_cal))

                conexion.commit()
                print(f"\n{VERDE}¡Éxito! Fecha actualizada e historial guardado.{RESET}")
                
                # REFRESCAMOS EL DF PARA EL SEMÁFORO
                df = pd.read_sql_query("SELECT * FROM gages", conexion)
                df['Próxima Calibración'] = pd.to_datetime(df['Próxima Calibración'])
                df['dias faltantes'] = (df['Próxima Calibración'] - hoy).dt.days

            except Exception as e:
                print(f"\n{ROJO}Error al actualizar: {e}{RESET}")
            
            conexion.close()
        else:
            print(f"\n{ROJO}El ID {id_buscado} no existe en el sistema.{RESET}")
            
        input("\nPresiona Enter para volver al menú...")
    elif opcion == "8":
        os.system('cls')
        print(f"{AMARILLO}--- CONSULTAR HISTORIAL DE CALIBRACIONES ---{RESET}\n")
        id_buscado = input("Introduce el ID del Gage para ver su historia: ").strip().upper()
        
        conexion = sqlite3.connect('inventario_gages.db')
        
        # Usamos read_sql_query para traer los datos del historial de ese ID específico
        query = "SELECT fecha_calibracion, resultado, tecnico FROM historial WHERE id_gage = ?"
        
        try:
            # El parámetro se pasa como una tupla (id_buscado,)
            historial_df = pd.read_sql_query(query, conexion, params=(id_buscado,))
            
            if not historial_df.empty:
                print(f"\nResultados encontrados para: {VERDE}{id_buscado}{RESET}")
                print("-" * 50)
                # Mostramos la tabla de historial
                print(historial_df.to_string(index=False))
                print("-" * 50)
            else:
                print(f"\n{ROJO}No se encontró historial para el ID: {id_buscado}{RESET}")
                print("Asegúrate de haber registrado al menos una calibración en la Opción 7.")
                
        except Exception as e:
            print(f"\n{ROJO}Error al consultar la base de datos: {e}{RESET}")
            
        conexion.close()
        input("\nPresiona Enter para volver al menú...")
    elif opcion == "9":
        os.system('cls')
        print(f"{AMARILLO}==========================================={RESET}")
        print(f"      TABLERO DE ALERTAS DE CALIBRACIÓN    ")
        print(f"==========================================={RESET}\n")

        # Filtros de tiempo
        hoy_dt = pd.Timestamp.now().normalize()
        df['Próxima Calibración'] = pd.to_datetime(df['Próxima Calibración'])
        df['dias faltantes'] = (df['Próxima Calibración'] - hoy_dt).dt.days

        # 1. CRÍTICOS (Ya pasaron o son hoy)
        criticos = df[df['dias faltantes'] <= 0]
        # 2. PREVENTIVOS (7 días)
        semanales = df[(df['dias faltantes'] > 0) & (df['dias faltantes'] <= 7)]

        if not criticos.empty:
            print(f"{ROJO}--- CRÍTICOS (URGE CALIBRAR) ---{RESET}")
            # Solo mostramos columnas importantes para no amontonar
            print(criticos[['ID del Gage', 'Tipo', 'Próxima Calibración', 'dias faltantes']].to_string(index=False))
            print("\n")

        if not semanales.empty:
            print(f"{AMARILLO}--- PREVENTIVOS (PRÓXIMOS 7 DÍAS) ---{RESET}")
            print(semanales[['ID del Gage', 'Tipo', 'Próxima Calibración', 'dias faltantes']].to_string(index=False))
        
        if criticos.empty and semanales.empty:
            print(f"{VERDE}Felicidades, Chris. No hay alertas pendientes por ahora.{RESET}")

        print(f"\n{CYAN}Tip: Usa la Opción 3 para exportar el reporte formal para Dicastal.{RESET}")
        input("\nPresiona Enter para volver al menú...")       
        
        
    elif opcion == "10":
      break
print("hasta luego")