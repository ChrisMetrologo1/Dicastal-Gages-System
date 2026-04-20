import streamlit as st
import requests

# Desactivar advertencias de seguridad de red interna
requests.packages.urllib3.disable_warnings()

st.set_page_config(page_title="Dicastal Trazabilidad", layout="centered")
st.title("🛡️ Validador de Calidad")

# --- CONFIGURACIÓN VALIDADA POR CMD ---
# Usamos el puerto 8100 que dio 'True' en tu prueba
API_URL = "https://10.43.246.117:8100/api/TR/PartsRecord/GetSPTRAudit"
TOKEN = "osiezrpb511oniqqw1urjuwi"

def consultar_sistema(dmc):
    headers = {
        "Authorization_Token": TOKEN,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    
    params = {"qrCode": dmc}

    try:
        # Usamos un timeout corto porque el ping fue de apenas 8ms
        response = requests.get(API_URL, headers=headers, params=params, verify=False, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            return f"Error del servidor: {response.status_code}"
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# --- INTERFAZ ---
qr = st.text_input("👇 ESCANEA EL DMC:")

if qr:
    with st.spinner('Consultando...'):
        datos = consultar_sistema(qr)
        
        if isinstance(datos, (dict, list)):
            st.success("✅ Datos recuperados")
            st.json(datos)
        else:
            st.error(datos)
            st.info("Si sale '401', es necesario renovar el Token desde el navegador.")