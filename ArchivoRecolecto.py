import os
import shutil

# --- CONFIGURACIÓN ---
# La carpeta "madre" donde están todas las subcarpetas de modelos/fechas
CARPETA_ESTRUCTURA = r'\\10.43.234.42\Calidad\05 Lab CMM\CMM\CMM1\Otros' 

# A dónde quieres que regresen todos los archivos
CARPETA_DESTINO_RAIZ = r'D:\Zeiss_excel'

def recolectar_archivos():
    if not os.path.exists(CARPETA_DESTINO_RAIZ):
        os.makedirs(CARPETA_DESTINO_RAIZ)
        
    print(f"Iniciando recolección desde: {CARPETA_ESTRUCTURA}")
    
    # os.walk recorre absolutamente todas las subcarpetas
    for carpeta_actual, subcarpetas, archivos in os.walk(CARPETA_ESTRUCTURA):
        for nombre_archivo in archivos:
            # Filtramos solo por archivos de Excel
            if nombre_archivo.lower().endswith(('.xls', '.xlsx')):
                ruta_completa = os.path.join(carpeta_actual, nombre_archivo)
                ruta_destino = os.path.join(CARPETA_DESTINO_RAIZ, nombre_archivo)
                
                # Manejo de nombres duplicados (opcional pero recomendado)
                if os.path.exists(ruta_destino):
                    # Si ya existe uno igual en la raíz, le agrega un prefijo de tiempo
                    base, ext = os.path.splitext(nombre_archivo)
                    ruta_destino = os.path.join(CARPETA_DESTINO_RAIZ, f"COPIA_{nombre_archivo}")

                try:
                    shutil.move(ruta_completa, ruta_destino)
                    print(f"Recuperado: {nombre_archivo}")
                except Exception as e:
                    print(f"No se pudo mover {nombre_archivo}: {e}")

    print("\n--- Recolección terminada ---")

if __name__ == "__main__":
    recolectar_archivos()