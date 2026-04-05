import pandas as pd
import sqlite3
import os

def cargar_desde_excel_maestro():
    # 1. Nombre del archivo que subiste (debe estar en la misma carpeta)
    archivo_excel = 'Libro2.xlsx' 
    
    if not os.path.exists(archivo_excel):
        print(f"Error: No se encuentra el archivo {archivo_excel}")
        return

    print("Leyendo lista de 811 elementos desde Excel...")
    
    # 2. Leemos el archivo Excel directamente (sin problemas de codificación)
    try:
        # Nota: Si el archivo tiene varias hojas, asegúrate que sea 'Hoja1'
        df = pd.read_excel(archivo_excel)
    except Exception as e:
        print(f"Error al leer Excel: {e}")
        return
    
    # Limpiamos nombres de columnas
    df.columns = [str(c).strip() for c in df.columns]

    # 3. Conexión a la base de datos
    conexion = sqlite3.connect('inventario_gages.db')
    cursor = conexion.cursor()

    # Borramos y recreamos la tabla con el mapeo de Libro2
    cursor.execute('DROP TABLE IF EXISTS gages')
    cursor.execute('''CREATE TABLE gages (
        id_medicion TEXT PRIMARY KEY,
        nombre TEXT,
        cliente TEXT,
        descripcion TEXT,
        ultima_calibracion DATE
    )''')

    # 4. Mapeo de columnas según tu archivo
    df_db = pd.DataFrame()
    df_db['id_medicion'] = df['ID']
    df_db['nombre'] = df['Nombre']
    df_db['cliente'] = df['Cliente']
    df_db['descripcion'] = df['DESCRIPCION']
    
    # Formateamos la fecha correctamente para SQL
    df_db['ultima_calibracion'] = pd.to_datetime(df['Fecha de Ultima calibracion'], errors='coerce').dt.strftime('%Y-%m-%d')

    # 5. Guardar en la DB
    df_db.to_sql('gages', conexion, if_exists='replace', index=False)
    
    # Aseguramos la tabla de historial
    cursor.execute('''CREATE TABLE IF NOT EXISTS historial (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_gage TEXT,
        fecha_cal DATE,
        resultado TEXT,
        tecnico TEXT
    )''')
    
    conexion.commit()
    conexion.close()
    
    print(f"✅ ¡LISTO! Se cargaron {len(df_db)} registros desde el archivo Excel.")

if __name__ == "__main__":
    cargar_desde_excel_maestro()