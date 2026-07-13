import streamlit as st
import plotly.graph_objects as go

def render_dashboard(analysis_data, profile_data, history_data=None):
    if history_data is None:
        history_data = []
    
    # ==========================================
    # 1. BLOQUE DE ESTILOS CSS PERSONALIZADOS (INCLUYE REDUCCIÓN DE HUECOS)
    # ==========================================
    custom_css = """
    <style>
    /* Estilos para reducir márgenes por defecto de Streamlit */
    .block-container { padding-top: 0.5rem; padding-bottom: 0rem; }
    .element-container { margin-bottom: 0.2rem !important; }
    .stColumn { padding: 0.2rem !important; }
    .stContainer { margin-bottom: 0.2rem !important; }
    
    /* Estilos Generales para Tarjetas (Cards) */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 20px;
        text-align: center;
        margin-bottom: 0.2rem;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    /* Textos dentro de las métricas */
    .metric-title {
        color: #7f8c8d;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .metric-subtitle {
        font-size: 0.9rem;
        color: #95a5a6;
        margin-top: 5px;
    }

    /* Colores Dinámicos según el Riesgo */
    .risk-green { color: #2ecc71; border-bottom: 4px solid #2ecc71; }
    .risk-yellow { color: #f1c40f; border-bottom: 4px solid #f1c40f; }
    .risk-orange { color: #e67e22; border-bottom: 4px solid #e67e22; }
    .risk-red { color: #e74c3c; border-bottom: 4px solid #e74c3c; }

    /* Tarjetas Inferiores (Alertas y Objetivos) */
    .bottom-card {
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        padding: 15px;
        height: 100%;
        margin-bottom: 0.2rem;
    }
    .alerts-card {
        border-left: 5px solid #e74c3c; /* Borde rojo para llamar atención */
    }
    .goals-card {
        border-left: 5px solid #3498db; /* Borde azul para objetivos */
    }
    
    /* Títulos de sección */
    h3 {
        color: #2c3e50;
        margin-top: 0;
        margin-bottom: 0.5rem;
    }
    
    /* Chips para condiciones crónicas y genética */
    .chip {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 16px;
        background-color: #f0f2f6;
        color: #2c3e50;
        font-size: 0.9rem;
    }
    
    /* Modo Oscuro Soporte Básico */
    @media (prefers-color-scheme: dark) {
        .metric-card, .bottom-card {
            background-color: #1e1e1e;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            color: #ecf0f1;
        }
        h3 { color: #ecf0f1; }
        .chip {
            background-color: #3a3a3a;
            color: #ecf0f1;
        }
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
    
    st.title("📊 Panel de Salud Inteligente")
    
    # ==========================================
    # VALIDACIÓN DE SEGURIDAD (Restricción clínica)
    # ==========================================
    chronic_diseases = profile_data.get("chronic_diseases", [])
    genetic_factors = profile_data.get("genetic_risk_factors", [])
    health_risk = analysis_data.get("health_risk", "Sin Evaluación Completa")
    
    if health_risk == "Sin Evaluación Completa":
        st.warning("⚠️ Actualiza tu perfil médico (Historial de Enfermedades y Genética) para ver tu análisis completo.")
        return # Detiene el renderizado del dashboard

    # ==========================================
    # 2. PERFIL COMPACTO EN HORIZONTAL
    # ==========================================
    st.markdown("👤 **Resumen Clínico:** Evaluación basada en biometría, comorbilidades y riesgo genético.")
    
    # Fila 1: Edad | Peso | Altura | Género
    row1_col1, row1_col2, row1_col3, row1_col4 = st.columns(4)
    with row1_col1:
        st.metric("Edad", f"{profile_data.get('age', 0)} años")
    with row1_col2:
        st.metric("Peso", f"{profile_data.get('weight', 0)} kg")
    with row1_col3:
        st.metric("Altura", f"{profile_data.get('height', 0)} cm")
    with row1_col4:
        st.metric("Género", profile_data.get('gender', 'N/A'))
    
    # Fila 2: Actividad | Sueño | Genética
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    with row2_col1:
        st.metric("Nivel de Actividad", profile_data.get('activity_level', 'N/A').replace('_', ' ').title())
    with row2_col2:
        st.metric("Sueño Promedio", f"{profile_data.get('sleep_hours', 0)} hrs")
    with row2_col3:
        st.metric("Factores Genéticos", f"{len(genetic_factors)}")

    # ==========================================
    # 3. MÉTRICAS PRINCIPALES (3 columnas)
    # ==========================================
    with st.container():
        score = analysis_data.get("health_score", 0)
        bmi = analysis_data.get("bmi", 0)
        calories = analysis_data.get("health_plan", {}).get("nutrition", {}).get("daily_calories", 0)
        
        # Lógica de colores Dinámicos basada en Score
        if score < 40:
            risk_class = "risk-red"
        elif score <= 60:
            risk_class = "risk-orange"
        elif score <= 80:
            risk_class = "risk-yellow"
        else:
            risk_class = "risk-green"
            
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card {risk_class}">
                <div class="metric-title">Health Score</div>
                <div class="metric-value {risk_class}">{score}<span style="font-size:1.2rem">/100</span></div>
                <div class="metric-subtitle">Puntuación global penalizada</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Índice Masa Corporal</div>
                <div class="metric-value" style="color: #3498db;">{bmi}</div>
                <div class="metric-subtitle">Categoría: {analysis_data.get("bmi_category", "").replace('_', ' ').title()}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Calorías Sugeridas</div>
                <div class="metric-value" style="color: #9b59b6;">{calories}</div>
                <div class="metric-subtitle">kcal/día adaptadas a objetivo</div>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # 4. SECCIÓN INFERIOR: 70% - 30%
    # ==========================================
    col_left, col_right = st.columns([7, 3])
    
    with col_left:
        # Columna izquierda (70%): Alertas + Fumador + Condiciones crónicas
        with st.container():
            # Alertas
            alerts = analysis_data.get("alerts", [])
            alerts_html = ""
            if alerts:
                for alert in alerts:
                    icon = "🚨" if "high" in alert.get("priority", "") or "Clínica" in alert.get("message", "") else "⚠️"
                    alerts_html += f"<p style='margin-bottom: 8px;'>{icon} {alert.get('message', '')}</p>"
            else:
                alerts_html = "<p>✅ No tienes alertas médicas críticas en este momento.</p>"
                
            st.markdown(f"""
            <div class="bottom-card alerts-card">
                <h3>Atención Médica y Alertas</h3>
                <div>{alerts_html}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Fumador
            smoker = profile_data.get("smoker", False)
            st.markdown(f"""
            <div class="bottom-card" style="margin-top: 0.2rem;">
                <h3>Fumador</h3>
                <p>{'🚬 Sí' if smoker else '✅ No'}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Condiciones crónicas
            chips_html = "".join([f'<span class="chip">{disease}</span>' for disease in chronic_diseases])
            st.markdown(f"""
            <div class="bottom-card" style="margin-top: 0.2rem;">
                <h3>Condiciones Crónicas</h3>
                <div>{chips_html if chips_html else '<p>Ninguna</p>'}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        # Columna derecha (30%): Objetivos de salud + Objetivos semanales
        with st.container():
            # Objetivos de salud
            health_goals = profile_data.get("health_goals", [])
            health_goals_html = "".join([f'<span class="chip">{goal.replace("_", " ").title()}</span>' for goal in health_goals])
            st.markdown(f"""
            <div class="bottom-card goals-card">
                <h3>Objetivos de Salud</h3>
                <div>{health_goals_html if health_goals_html else '<p>Ninguno</p>'}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Objetivos semanales
            weekly_goals = analysis_data.get("weekly_goals", [])
            goals_html = ""
            if weekly_goals:
                for goal in weekly_goals:
                    goals_html += f"<p style='margin-bottom: 8px;'>🎯 {goal}</p>"
            else:
                goals_html = "<p>No hay objetivos asignados.</p>"
                
            st.markdown(f"""
            <div class="bottom-card" style="margin-top: 0.2rem;">
                <h3>Objetivos Semanales</h3>
                <div>{goals_html}</div>
            </div>
            """, unsafe_allow_html=True)

    # ==========================================
    # 5. ANÁLISIS VISUAL AVANZADO Y EXPORTACIÓN
    # ==========================================
    st.subheader("📈 Análisis Visual y Exportación")
    
    col_chart1, col_chart2 = st.columns(2, gap="large")
    
    # Colores para gráficos
    chart_color = "#e74c3c" if score < 40 else "#e67e22" if score <= 60 else "#f1c40f" if score <= 80 else "#2ecc71"
    
    with col_chart1:
        st.markdown("**Comparativa de Health Score**")
        age = profile_data.get('age', 30)
        avg_score = 75 if age < 40 else 65
        
        fig_bar = go.Figure(data=[
            go.Bar(name='Tu Puntuación', x=['Health Score'], y=[score], marker_color=chart_color),
            go.Bar(name='Promedio Población', x=['Health Score'], y=[avg_score], marker_color='#3498db')
        ])
        fig_bar.update_layout(barmode='group', template="plotly_white", height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_chart2:
        st.markdown("**Evolución Histórica**")
        if history_data:
            dates = [h.get('analyzed_at', '')[:10] for h in history_data][::-1]
            scores = [h.get('health_score', 0) for h in history_data][::-1]
            
            fig_line = go.Figure(go.Scatter(
                x=dates, y=scores, mode='lines+markers',
                line=dict(color=chart_color, width=3),
                marker=dict(size=8)
            ))
            fig_line.update_layout(template="plotly_white", height=300, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No hay suficiente historial para mostrar la evolución.")
            fig_line = go.Figure()
            
    # EXPORTACIÓN
    try:
        from advanced_reports import generate_risk_report_pdf, generate_risk_report_excel, generate_risk_report_word
        
        try:
            img_bytes = fig_line.to_image(format="png", scale=3, engine="kaleido")
        except Exception:
            img_bytes = None
            
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            pdf_file = generate_risk_report_pdf(analysis_data, profile_data, history_data, img_bytes)
            st.download_button("📥 PDF", pdf_file, "riesgo_clinico.pdf", "application/pdf", use_container_width=True)
        with col_btn2:
            excel_file = generate_risk_report_excel(analysis_data, profile_data, history_data)
            st.download_button("📥 Excel", excel_file, "riesgo.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        with col_btn3:
            word_file = generate_risk_report_word(analysis_data, profile_data, img_bytes)
            st.download_button("📥 Word", word_file, "riesgo.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    except ImportError:
        st.warning("⚠️ Faltan instalar módulos de exportación.")
