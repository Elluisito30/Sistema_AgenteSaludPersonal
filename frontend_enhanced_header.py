# app.py - Streamlit Frontend with Enhanced Reports
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
import export_reports
import io

# ============================================
# IMPORTS DE NUEVOS MÓDULOS
# ============================================
from frontend_styles import get_custom_css
from ui_components import *
from plotly_themes import *

# ============================================
# CONFIGURACIÓN
# ============================================
st.set_page_config(
    page_title="Health AI - Tu Asistente Personal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://backend:8000/api"

# ============================================
# APLICAR ESTILOS PERSONALIZADOS
# ============================================
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ============================================
# FUNCIONES API
# ============================================

