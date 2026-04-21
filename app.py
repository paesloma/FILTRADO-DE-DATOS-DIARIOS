import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Gestión de Repuestos Pro", layout="wide")

# --- DISEÑO DEL BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ GESTIÓN DE REPUESTOS</h1>
        <p style="margin:0;">Reporte Consolidado al <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

archivo = st.file_uploader("Sube tu archivo (Excel o CSV)", type=["xls", "xlsx", "csv"])

if archivo is not None:
    try:
        # 1. CARGA DE DATOS (Detección automática de separador)
        if archivo.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(archivo)
        else:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')

        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # --- LA SOLUCIÓN: Limpiar espacios ocultos dentro de las celdas ---
        if 'Técnico' in df.columns:
            df['Técnico'] = df['Técnico'].astype(str).str.strip()
        # ------------------------------------------------------------------

        # 2. LÓGICA DE FILTRADO
        mask_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        mask_proceso = (df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)) & \
                       (df['Repuestos'].astype(str).str.len() > 2)
        
        # Filtro de técnicos a excluir (Internos)
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_tecnico_valido = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        # Aplicar filtros
        df_filtrado = df[(mask_solicita | mask_proceso) & mask_tecnico_valido].copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN POR TALLER EN PANTALLA
            st.sidebar.header("Segmentación")
            lista_talleres = sorted(df_filtrado['Técnico'].unique())
            seleccionados = st.sidebar.multiselect("Filtrar por Taller", lista_talleres, default=lista_talleres)
            
            # Aplicar filtro de la barra lateral
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccionados)].sort_values('Técnico')

            # 4. PREPARACIÓN DE COLUMNAS FINALES
            df_final['Enviado'] = "[  ]"
            columnas_ordenadas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', 'Repuestos']
            
            cols_finales = [c for c in columnas_ordenadas if c in df_final.columns or c == 'Enviado']
            df_final = df_final[cols_finales]

            # MÉTRICAS
            st.metric("Órdenes para Repuestos", len(df_final))

            # 5. BOTÓN DE DESCARGA (Excel plano sin errores de formato)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Repuestos')
            
            st.download_button(
                label="📥 DESCARGAR EXCEL",
                data=output.getvalue(),
                file_name=f"Repuestos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            # MOSTRAR TABLA EN WEB
            st.dataframe(df_final, hide_index=True, use_container_width=True)

        else:
            st.warning("No se encontraron órdenes que necesiten repuestos según los filtros.")

    except Exception as e:
        st.error(f"Se produjo un error al leer el archivo: {e}")
