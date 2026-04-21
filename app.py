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
        # 1. CARGA DE DATOS
        if archivo.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(archivo, engine='openpyxl')
        else:
            df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')

        # Limpiar nombres de columnas (quitar espacios en los títulos)
        df.columns = df.columns.str.strip()
        
        # --- LIMPIEZA DE DATOS Y COLUMNA SERIE ---
        # Definimos las columnas que queremos limpiar de nulos
        columnas_a_limpiar = ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']
        for col in columnas_a_limpiar:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip()
                
        # 2. LÓGICA DE FILTRADO
        mask_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        mask_proceso = (df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)) & \
                       (df['Repuestos'].str.len() > 2)
        
        # Filtro de técnicos a excluir (Internos)
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_tecnico_valido = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        # Aplicar filtros
        df_filtrado = df[(mask_solicita | mask_proceso) & mask_tecnico_valido].copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN POR TALLER
            st.sidebar.header("Segmentación")
            lista_talleres = sorted(df_filtrado['Técnico'].unique())
            seleccionados = st.sidebar.multiselect("Filtrar por Taller", lista_talleres, default=lista_talleres)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccionados)].sort_values('Técnico')

            # 4. PREPARACIÓN DE COLUMNAS INCLUYENDO SERIE
            df_final['Enviado'] = "[  ]"
            
            # Intentamos buscar 'Serie' o 'Serie/Artículo' según lo que venga en tu archivo
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            
            columnas_ordenadas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            
            # Filtramos solo las columnas que existan realmente
            cols_finales = [c for c in columnas_ordenadas if c in df_final.columns or c == 'Enviado']
            df_final = df_final[cols_finales]

            # MÉTRICAS
            st.metric("Órdenes para Repuestos", len(df_final))

            # 5. BOTÓN DE DESCARGA (Usando openpyxl)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Repuestos')
            
            st.download_button(
                label="📥 DESCARGAR EXCEL CON SERIE",
                data=output.getvalue(),
                file_name=f"Repuestos_Completo_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            # MOSTRAR TABLA EN WEB
            st.dataframe(df_final, hide_index=True, use_container_width=True)

        else:
            st.warning("No se encontraron órdenes que necesiten repuestos.")

    except Exception as e:
        st.error(f"Error detectado: {e}")
