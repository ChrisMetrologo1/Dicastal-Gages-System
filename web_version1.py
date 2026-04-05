import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime

# 1. Configuración de pantalla
st.set_page_config(page_title="Dicastal Gages Piso", layout="wide")
st.title("📲 Control de Gages - Piso Dicastal")

# 2. Función de carga con ESTANDARIZACIÓN
def cargar_datos():
    if not os.path.exists('inventario_gages.db'):
        st.error("❌ No se encuentra 'inventario_gages.db'")
        return pd.DataFrame()
        
    try:
        conn = sqlite3.connect('inventario_gages.db')
        df = pd.read_sql_query("SELECT id_medicion, cliente, descripcion, ultima_calibracion FROM gages", conn)
        conn.close()
        
        # Limpieza de fechas
        df['ultima_calibracion'] = pd.to_datetime(df['ultima_calibracion'], errors='coerce')
        df = df.dropna(subset=['ultima_calibracion']) 
        
        # Cálculos de días
        df['vence'] = df['ultima_calibracion'] + pd.DateOffset(years=1)
        df['dias'] = (df['vence'] - pd.Timestamp.now().normalize()).dt.days
        
        # --- ESTANDARIZACIÓN CRÍTICA ---
        # Creamos una columna invisible 'id_limpio' sin ningún espacio para buscar mejor
        df['id_busqueda'] = df['id_medicion'].astype(str).str.upper().str.replace(" ", "")
        df['cliente_busqueda'] = df['cliente'].astype(str).str.upper().str.replace(" ", "")
        
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

df_maestro = cargar_datos()

if not df_maestro.empty:
    # 3. BUSCADOR INTELIGENTE
    st.subheader("🔍 Buscador General (Sin importar espacios)")
    # Limpiamos lo que el usuario escribe también (quitamos espacios y pasamos a mayúsculas)
    entrada_usuario = st.text_input("Ingresa ID o Cliente").strip().upper()
    busqueda_limpia = entrada_usuario.replace(" ", "")
    
    df_vista = df_maestro.copy()
    
    if busqueda_limpia:
        # Buscamos en las columnas estandarizadas
        mask = (
            df_maestro['id_busqueda'].str.contains(busqueda_limpia, na=False) | 
            df_maestro['cliente_busqueda'].str.contains(busqueda_limpia, na=False)
        )
        df_vista = df_maestro[mask]

    st.write(f"📊 **Resultados: {len(df_vista)} equipos**")
    
    # 4. TABLA CON COLORES
    def color_vencido(val):
        color = '#FF4B4B' if val <= 0 else ('#FFA500' if val <= 15 else '#00FF00')
        return f'color: {color}; font-weight: bold'

    # Mostramos las columnas originales (con espacios) pero filtradas por la búsqueda limpia
    columnas_a_mostrar = ['id_medicion', 'cliente', 'descripcion', 'ultima_calibracion', 'vence', 'dias']
    st.dataframe(
        df_vista[columnas_a_mostrar].style.map(color_vencido, subset=['dias']), 
        use_container_width=True
    )

    # 5. ACTUALIZACIÓN RÁPIDA
    st.divider()
    st.subheader("📝 Actualizar Calibración")
    
    with st.form("form_piso"):
        col1, col2 = st.columns(2)
        with col1:
            id_sel = st.selectbox("Gage a actualizar", df_maestro['id_medicion'].unique())
        with col2:
            f_nueva = st.date_input("Fecha nueva", datetime.now())
        
        if st.form_submit_button("💾 GUARDAR CAMBIOS"):
            try:
                conn = sqlite3.connect('inventario_gages.db')
                conn.execute("UPDATE gages SET ultima_calibracion=? WHERE id_medicion=?", 
                             (f_nueva.strftime("%Y-%m-%d"), id_sel))
                conn.commit()
                conn.close()
                st.success(f"¡{id_sel} actualizado!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")