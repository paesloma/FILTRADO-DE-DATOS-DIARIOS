import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Gestión de Repuestos Pro", layout="wide")

# --- BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center;">
        <h1>🛠️ GESTIÓN DE REPUESTOS</h1>
        <p>Reporte Consolidado al <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div><br>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Sube el archivo", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. CARGA AUTOMÁTICA
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            # Detecta automáticamente si usa coma o punto y coma
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')

        df.columns = df.columns.str.strip()
        
        # 2. FILTROS FIJOS (Según tu lógica)
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_repuestos = df['Repuestos'].astype(str).str.strip().apply(lambda x: len(str(x)) > 2 and str(x).lower() != 'nan')
        
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        
        mask_estado = cond_solicita | (es_proceso & tiene_repuestos)
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_filtrado = df[mask_estado & mask_tecnico].copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN POR TALLER (SIDEBAR)
            st.sidebar.header("Filtros")
            talleres = sorted(df_filtrado['Técnico'].unique())
            seleccion = st.sidebar.multiselect("Seleccionar Talleres", talleres, default=talleres)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion)].sort_values('Técnico')

            # 4. PREPARAR COLUMNAS PARA INGRESO DE DATOS
            df_final['Enviado'] = "[  ]"
            columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', 'Repuestos']
            # Solo mostramos las que existen en tu archivo
            cols_ok = [c for c in columnas if c in df_final.columns or c == 'Enviado']
            df_final = df_final[cols_ok]

            # MÉTRICAS
            st.metric("Total Órdenes Filtradas", len(df_final))

            # 5. DESCARGA EXCEL (DATOS PUROS)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Repuestos')
            
            st.download_button(
                label="📥 DESCARGAR EXCEL DE DATOS",
                data=output.getvalue(),
                file_name="reporte_repuestos.xlsx",
                use_container_width=True
            )

            # VISTA PREVIA
            st.dataframe(df_final, hide_index=True, use_container_width=True)

        else:
            st.warning("No hay datos que coincidan con los filtros de Repuestos.")

    except Exception as e:
        st.error(f"Error: {e}")
