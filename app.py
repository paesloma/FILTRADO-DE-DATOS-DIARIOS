import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Gestión de Repuestos Pro", layout="wide")

# --- BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ GESTIÓN DE REPUESTOS</h1>
        <p style="margin:0;">Reporte Consolidado al <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

archivo = st.file_uploader("Sube tu archivo (Excel o CSV)", type=["xls", "xlsx", "csv"])

if archivo is not None:
    try:
        # 1. CARGA DE DATOS
        if archivo.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(archivo)
        else:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')

        df.columns = df.columns.str.strip()
        
        # Limpieza de nulos y espacios
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip()
                
        # 2. FILTRADO ESTRICTO
        mask_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        mask_proceso = (df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)) & \
                       (df['Repuestos'].str.len() > 2)
        
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_tecnico_valido = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_filtrado = df[(mask_solicita | mask_proceso) & mask_tecnico_valido].copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN
            st.sidebar.header("Filtros")
            talleres = sorted(df_filtrado['Técnico'].unique())
            seleccion = st.sidebar.multiselect("Talleres a incluir", talleres, default=talleres)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion)].sort_values('Técnico')

            # 4. COLUMNAS DE DATOS
            df_final['Enviado'] = "[  ]"
            columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', 'Repuestos']
            cols_ok = [c for c in columnas if c in df_final.columns or c == 'Enviado']
            df_final = df_final[cols_ok]

            st.metric("Órdenes Filtradas", len(df_final))

            # 5. EXPORTACIÓN (Usa xlsxwriter si lo agregaste, sino usa openpyxl)
            output = BytesIO()
            motor = 'xlsxwriter' # Cambiar a 'openpyxl' si no puedes instalar xlsxwriter
            with pd.ExcelWriter(output, engine=motor) as writer:
                df_final.to_excel(writer, index=False, sheet_name='Repuestos')
            
            st.download_button(
                label="📥 DESCARGAR DATOS SEGMENTADOS",
                data=output.getvalue(),
                file_name=f"Repuestos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            st.dataframe(df_final, hide_index=True, use_container_width=True)
        else:
            st.warning("No hay datos que coincidan.")

    except Exception as e:
        st.error(f"Error: {e}")
