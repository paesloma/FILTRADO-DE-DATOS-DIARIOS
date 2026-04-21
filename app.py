import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Configuración de estilos para Excel
try:
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_STYLING = True
except ImportError:
    EXCEL_STYLING = False

st.set_page_config(page_title="Gestión de Repuestos Pro", layout="wide")

# --- BANNER SUPERIOR ---
fecha_hoy = datetime.now().strftime("%d/%m/%Y")
st.markdown(f"""
    <style>
    .main-banner {{
        background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }}
    </style>
    <div class="main-banner">
        <h1>🛠️ DASHBOARD DE GESTIÓN DE REPUESTOS</h1>
        <p>Reporte Consolidado al <b>{fecha_hoy}</b></p>
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Sube el archivo de órdenes", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # Carga de datos
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=',', engine='python', encoding='utf-8')

        df.columns = df.columns.str.strip()
        
        # --- LÓGICA DE LIMPIEZA INICIAL ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_repuestos = df['Repuestos'].astype(str).str.strip().apply(lambda x: len(x) > 2 and x.lower() != 'nan')
        
        # Exclusión de técnicos internos según tu patrón
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        
        mask_estado = cond_solicita | (es_proceso & tiene_repuestos)
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_base = df[mask_estado & mask_tecnico].copy()

        # --- PANEL DE SEGMENTACIÓN (SIDEBAR) ---
        st.sidebar.header("🔍 Segmentar Datos")
        
        # Segmentación por Técnico
        tecnicos_selected = st.sidebar.multiselect(
            "Filtrar por Taller/Técnico",
            options=sorted(df_base['Técnico'].unique()),
            default=sorted(df_base['Técnico'].unique())
        )
        
        # Segmentación por Estado
        estados_selected = st.sidebar.multiselect(
            "Filtrar por Estado",
            options=sorted(df_base['Estado'].unique()),
            default=sorted(df_base['Estado'].unique())
        )

        # Aplicar filtros de segmentación
        df_filtrado = df_base[
            (df_base['Técnico'].isin(tecnicos_selected)) & 
            (df_base['Estado'].isin(estados_selected))
        ].sort_values(by='Técnico')

        if not df_filtrado.empty:
            # MÉTRICAS DINÁMICAS
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Órdenes Filtradas", len(df_filtrado))
            m2.metric("🧑‍🔧 Talleres Activos", df_filtrado['Técnico'].nunique())
            m3.metric("🚩 Mayor Carga", df_filtrado['Técnico'].value_counts().idxmax())

            # Preparación de columnas para exportación
            df_filtrado['Enviado'] = "[ ]" 
            columnas_finales = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', 'Repuestos']
            cols_disp = [c for c in columnas_finales if c in df_filtrado.columns or c == 'Enviado']

            # --- BOTÓN DE DESCARGA ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado[cols_disp].to_excel(writer, index=False, sheet_name='Reporte_Segmentado')
                ws = writer.sheets['Reporte_Segmentado']
                
                if EXCEL_STYLING:
                    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                    for cell in ws[1]:
                        cell.fill = header_fill
                        cell.font = Font(color='FFFFFF', bold=True)

            st.download_button(
                label="📥 Descargar Segmentación Actual",
                data=output.getvalue(),
                file_name=f"Reporte_Segmentado_{fecha_hoy.replace('/','-')}.xlsx",
                use_container_width=True
            )

            # --- VISUALIZACIÓN POR GRUPOS (SEGMENTOS) ---
            st.subheader("📋 Detalle por Segmento")
            for taller in tecnicos_selected:
                df_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"📍 {taller} - {len(df_taller)} órdenes"):
                        st.dataframe(df_taller[cols_disp], hide_index=True, use_container_width=True)
        else:
            st.warning("No hay datos para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
