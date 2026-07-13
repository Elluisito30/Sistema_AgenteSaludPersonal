import streamlit as st
import requests

API_URL = "http://backend:8000/api"

# 1. Modifica tu función get_predictions para que use caché, pero se pueda limpiar
@st.cache_data(ttl=300, show_spinner=False)
def get_predictions(token):
    """Obtiene la última predicción desde el backend."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/predictions/latest", headers=headers)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

# 2. Modifica el flujo del botón donde haces el POST del nuevo análisis
def handle_new_analysis(token):
    with st.spinner("Analizando tu salud..."):
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{API_URL}/analyze", headers=headers)
        
        if response.status_code == 200:
            st.success("¡Análisis completado con éxito!")
            
            # Limpiar caché y forzar recarga
            st.cache_data.clear()
            
            # Actualizamos el session_state
            st.session_state['latest_analysis'] = response.json()
            st.session_state['needs_refresh'] = False
            
            # Forzamos a Streamlit a redibujar
            st.rerun()
        else:
            st.error("Hubo un error al realizar el análisis.")
