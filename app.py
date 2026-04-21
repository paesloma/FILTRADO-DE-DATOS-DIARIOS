import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

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
        # 1. LECTURA DE DATOS
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')

        df.columns = df.columns.str.strip()
        
        # 2. VALIDACIÓN Y FILTRADO
        columnas_req = ['Estado', 'Técnico', 'Repuestos']
        if not all(col in df.columns for col in columnas_req):
            st.error(f"Faltan columnas necesarias. El archivo debe tener: {columnas_req}")
            st.stop()

        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_repuestos = df['Repuestos'].astype(str).str.strip().apply(lambda x: len(x) > 2 and x.lower() != 'nan')
        
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_estado = cond_solicita | (es_proceso & tiene_repuestos)
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_base = df[mask_estado & mask_tecnico].copy()

        # 3. SEGMENTACIÓN EN LA INTERFAZ
        st.sidebar.header("⚙️ Segmentación")
        tecnicos_disponibles = sorted(df_base['Técnico'].dropna().unique())
        tecnicos_sel = st.sidebar.multiselect("Filtrar Talleres", tecnicos_disponibles, default=tecnicos_disponibles)
        
        df_filtrado = df_base[df_base['Técnico'].isin(tecnicos_sel)].sort_values(by='Técnico')

        if not df_filtrado.empty:
            # MÉTRICAS Y GRÁFICOS WEB
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Órdenes", len(df_filtrado))
            m2.metric("🧑‍🔧 Talleres Activos", df_filtrado['Técnico'].nunique())
            m3.metric("🚩 Mayor carga", df_filtrado['Técnico'].value_counts().idxmax())

            st.write("### 📊 Volumen de Órdenes")
            st.bar_chart(df_filtrado['Técnico'].value_counts())

            # 4. PREPARACIÓN DE EXCEL EXCLUSIVAMENTE CON DATOS
            df_filtrado['Enviado'] = "[  ]" 
            columnas_finales = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', 'Repuestos']
            cols_disp = [c for c in columnas_finales if c in df_filtrado.columns or c == 'Enviado']
            
            df_export = df_filtrado[cols_disp]
            
            # Exportación con motor por defecto de Pandas (sin OpenPyXL)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Datos_Limpios')

            st.download_button(
                label="📥 Descargar Base de Datos Limpia",
                data=output.getvalue(),
                file_name=f"Base_Repuestos_{fecha_hoy.replace('/','-')}.xlsx",
                use_container_width=True
            )

            # VISTA WEB
            st.write("### 📋 Vista Previa de la Matriz")
            st.dataframe(df_export, hide_index=True)

        else:
            st.warning("No hay datos para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
