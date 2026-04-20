import os
import shutil
import re
from datetime import datetime, timedelta

# =========================================================
# CONFIGURACIÓN ÚNICA POR MÁQUINA
# =========================================================
ORIGEN = r'D:\Zeiss_excel' 
DESTINO_BASE = r'D:\OTRA' 
MAQUINA_DEFAULT = "Sin Maquina" 
# =========================================================

MAPEO_MODELOS = [
    ("G45_Front_Knuckle_Finish_LH_Minus", "BMW G45 Front Knuckle MINUS"),
    ("G45_Front_Knuckle_Finish_RH_Minus", "BMW G45 Front Knuckle MINUS"),
    ("GM_L232_Rear_kunckle_Finish_LH_Assembly", "GM L232 Rear Assembly"),
    ("GM_L232_Rear_kunckle_Finish_RH_Assembly", "GM L232 Rear Assembly"),
    ("DT_Lower_Control_Arm_ASSEMBLE", "Stellantis DT Control Arm ASSEMBLY"),
    ("Ford_S650_HP1_Rear_Knuckle_Assembly", "Ford S650 HP1 Rear ASSEMBLY"),
    ("BMW_G45_Rear", "BMW G45 Rear Knuckle"),
    ("BMW_G45_Front", "BMW G45 Front Knuckle"),
    ("BMW_G65_Front", "BMW G65 Front Knuckle"),
    ("BMW_G65_ICE_PHEV_Rear", "BMW G65 Rear Knuckle"),
    ("GM_L232_Rear", "GM L232 Rear Knuckle"),
    ("GM_L234_RS_Rear", "GM L234 RS Rear Knuckle"),
    ("GM_L234N_rear", "GM L234N Rear Knuckle"),
    ("GM_BEV3_rear", "GM BEV3 Rear Knuckle"),
    ("GM_BEV3_YOKE", "GM BEV3 Yoke Susp"),
    ("GM_LUX3_rear", "GM LUX3 Rear Knuckle"),
    ("GM_LUX4_rear", "GM LUX4 Rear Knuckle"),
    ("HONDA_DG8B", "HONDA_DG8B_Bracket"),
    ("Tesla_Everest_Front", "Tesla EVEREST Front"),
    ("HIGHLAND BASE_Front", "Tesla HIGHLAND BASE Front"),
    ("Highland_Base_Rear", "Tesla HIGHLAND BASE Rear"),
    ("HIGHLAND Performance_Front", "Tesla HIGHLAND Performance Front"),
    ("Highland_Performance_Rear", "Tesla HIGHLAND Performance Rear"),
    ("Tesla_MX_Rear", "Tesla MX Rear Knuckle"),
    ("Tesla_W68_Front", "Tesla W68 Front Knuckle"),
    ("Tesla_W68_Pilot_Rear", "Tesla W68 Pilot Rear Knuckle"),
    ("Ford_CX727_Rear", "Ford CX727 Rear Knuckle"),
    ("Ford_S650_HP1_Rear_Knuckle_Finish", "Ford S650 HP1 Rear Finish"),
    ("Ford_U71X_Rear", "Ford U71X Rear Knuckle"),
    ("Nissan_P33C_Front", "Nissan P33C Front Knuckle"),
    ("Nissan_P33C_rear", "Nissan P33C Rear Knuckle"),
    ("Nissan_P42QR_Rear", "Nissan P42QR Rear Knuckle"),
    ("KM74_FR_AWD_Front", "Stellantis KM74 Front"),
    ("KM74_AWD_Rear", "Stellantis KM74 Rear"),
    ("Stellantis_EJ_rear", "Stellantis EJ Rear Knuckle"),
    ("Stellantis_KM74TH_Rear", "Stellantis KM74TH Rear Knuckle"),
    ("Stellantis_DT_Lower_Control_Arm_Finish", "Stellantis DT Control Arm Finish"),
    ("VW_BSUV_knuckle", "VW BSUV Knuckle"),
    ("MEB31_Rear", "VW MEB31 Rear Knuckle"),
    ("MEB_A_SUVe_Front", "VW MEB A SUVe Front Knuckle"),
    ("VW_MEB31B_Front", "VW MEB31B Front Knuckle")
]

def organizar_por_turno():
    if not os.path.exists(ORIGEN): return

    for archivo in os.listdir(ORIGEN):
        ruta_archivo = os.path.join(ORIGEN, archivo)
        
        if os.path.isfile(ruta_archivo) and (archivo.lower().endswith('.xls') or archivo.lower().endswith('.xlsx')):
            
            # 1. Lógica de Tiempo (Corte 7:00 AM)
            mtime = datetime.fromtimestamp(os.path.getmtime(ruta_archivo))
            if mtime.hour < 7:
                fecha_final = mtime - timedelta(days=1)
            else:
                fecha_final = mtime

            anio, mes, dia = str(fecha_final.year), f"{fecha_final.month:02d}", f"{fecha_final.day:02d}"
            
            # 2. Identificar Modelo
            modelo_folder = "Otros"
            for kw, folder in MAPEO_MODELOS:
                if kw.lower() in archivo.lower():
                    modelo_folder = folder
                    break
            
            # 3. Identificar Máquina
            match_m = re.search(r'_([a-zA-Z][0-9])_', archivo)
            maquina_folder = match_m.group(1).upper() if match_m else MAQUINA_DEFAULT
            
            # 4. Lado
            lado = "LH" if "_LH" in archivo.upper() else "RH" if "_RH" in archivo.upper() else "NA"
            
            # 5. Ruta y Movimiento
            destino = os.path.join(DESTINO_BASE, modelo_folder, maquina_folder, lado, anio, mes, dia)
            os.makedirs(destino, exist_ok=True)
            
            try:
                # Verificar si el archivo está libre
                os.rename(ruta_archivo, ruta_archivo)
                shutil.move(ruta_archivo, os.path.join(destino, archivo))
                print(f"Movido: {archivo}")
            except OSError:
                print(f"Archivo en uso: {archivo}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    organizar_por_turno()