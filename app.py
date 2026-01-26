import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import re

# Configuración de página
st.set_page_config(page_title="Gestión de Despachos", layout="wide")

# --- INICIALIZAR ESTADO DE SESIÓN ---
if 'df_gestion' not in st.session_state:
    st.session_state.df_gestion = None
if 'enviados' not in st.session_state:
    st.session_state.enviados = set()

# --- BANNER SUPERIOR ---
fecha_hoy = datetime.now().strftime("%d/%m/%Y")
st.markdown(f"""
    <style>
    .main-banner {{
        background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%);
        padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;
    }}
    </style>
    <div class="main-banner">
        <h1>🛠️ PANEL DE CONTROL DE REPUESTOS</h1>
        <p>Gestión de Despachos en Tiempo Real - {fecha_hoy}</p>
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("1. Cargar Archivo", type=["xls", "xlsx", "csv"])

if uploaded_file is not None and st.session_state.df_gestion is None:
    try:
        # Lectura
        if uploaded_file.name.endswith('.xls'): df = pd.read_excel(uploaded_file, engine='xlrd')
        elif uploaded_file.name.endswith('.xlsx'): df = pd.read_excel(uploaded_file, engine='openpyxl')
        else: df = pd.read_csv(uploaded_file, sep=';', engine='python', encoding='latin-1')

        df.columns = df.columns.str.strip()
        
        # Filtros de Estado y Exclusión de GO/Talleres
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_rep = df['Repuestos'].astype(str).str.strip().apply(lambda x: len(x) > 2 and x.lower() != 'nan')
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        
        mask = (cond_solicita | (es_proceso & tiene_rep)) & (~df['Técnico'].str.upper().str.contains(patron_excluir, na=False))
        
        st.session_state.df_gestion = df[mask].copy().sort_values(by='Técnico')
    except Exception as e:
        st.error(f"Error al cargar: {e}")

if st.session_state.df_gestion is not None:
    # Filtrar las que ya fueron marcadas como enviadas
    df_actual = st.session_state.df_gestion[~st.session_state.df_gestion['#Orden'].isin(st.session_state.enviados)]

    # --- DASHBOARD BANNER ---
    if not df_actual.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 Pendientes", len(df_actual))
        c2.metric("✅ Enviados hoy", len(st.session_state.enviados))
        c3.metric("🧑‍🔧 Talleres", df_actual['Técnico'].nunique())
    else:
        st.balloons()
        st.success("¡Todas las órdenes han sido despachadas!")

    st.divider()

    # --- LISTADO INTERACTIVO ---
    for taller in sorted(df_actual['Técnico'].unique()):
        df_taller = df_actual[df_actual['Técnico'] == taller]
        with st.expander(f"📍 {taller} ({len(df_taller)} pendientes)"):
            # Crear encabezados de tabla manuales para incluir el checkbox
            cols = st.columns([1, 2, 2, 4, 4, 3])
            cols[0].write("**Enviar**")
            cols[1].write("**# Orden**")
            cols[2].write("**Fecha**")
            cols[3].write("**Cliente**")
            cols[4].write("**Repuestos**")
            cols[5].write("**Producto**")

            for _, row in df_taller.iterrows():
                c = st.columns([1, 2, 2, 4, 4, 3])
                # El checkbox usa el número de orden como llave única
                enviado = c[0].checkbox("📦", key=f"check_{row['#Orden']}")
                if enviado:
                    st.session_state.enviados.add(row['#Orden'])
                    st.rerun() # Recarga para actualizar el dashboard y quitar la fila
                
                c[1].write(row['#Orden'])
                c[2].write(row['Fecha'])
                c[3].write(row['Cliente'][:30]) # Recorte para estética
                c[4].write(row['Repuestos'])
                c[5].write(row['Producto'])

    # --- BOTÓN PARA DESCARGAR EL RESTO ---
    if not df_actual.empty:
        st.sidebar.divider()
        output = BytesIO()
        df_actual.to_excel(output, index=False)
        st.sidebar.download_button("📥 Descargar Pendientes (Excel)", output.getvalue(), "pendientes.xlsx")
    
    if st.sidebar.button("🗑️ Reiniciar todo"):
        st.session_state.df_gestion = None
        st.session_state.enviados = set()
        st.rerun()
