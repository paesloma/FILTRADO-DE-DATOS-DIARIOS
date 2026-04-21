import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador por Talleres", layout="wide")

# --- BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ CONSOLIDADOR: AGRUPACIÓN POR TALLERES</h1>
        <p style="margin:0;">Reporte unificado al <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

archivos = st.file_uploader("Sube los archivos Excel o CSV", type=["xls", "xlsx", "csv"], accept_multiple_files=True)

if archivos:
    lista_df = []
    for arc in archivos:
        try:
            if arc.name.endswith(('.xls', '.xlsx')):
                temp = pd.read_excel(arc, engine='openpyxl')
            else:
                temp = pd.read_csv(arc, sep=None, engine='python', encoding='latin-1')
            lista_df.append(temp)
        except Exception as e:
            st.error(f"Error en {arc.name}: {e}")

    if lista_df:
        # 1. UNIFICAR Y LIMPIAR
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Rellenar nulos y limpiar textos
        cols_limpiar = ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']
        for col in cols_limpiar:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTRADO DE ESTADOS (Solicita / Proceso)
        mask_estado = df_total['Estado'].str.contains('Solicita|Proceso', case=False, na=False)
        # Eliminamos duplicados por número de orden para que el conteo de los 14 sea exacto
        df_filtrado = df_total[mask_estado].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN EN INTERFAZ
            st.sidebar.header("Filtros de Taller")
            todos_talleres = sorted(df_filtrado['Técnico'].unique())
            seleccionados = st.sidebar.multiselect("Selecciona Talleres", todos_talleres, default=todos_talleres)
            
            df_segmentado = df_filtrado[df_filtrado['Técnico'].isin(seleccionados)].sort_values('Técnico')

            # 4. PREPARACIÓN DE DATOS
            df_segmentado['Enviado'] = "[  ]"
            col_serie = 'Serie' if 'Serie' in df_segmentado.columns else 'Serie/Artículo'
            columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            cols_ok = [c for c in columnas if c in df_segmentado.columns or c == 'Enviado']
            
            # MÉTRICAS
            st.metric("Total Órdenes Únicas", len(df_segmentado))

            # 5. GENERAR EXCEL CON FILAS DE AGRUPACIÓN (Separadores)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Creamos una lista para construir el reporte final con separadores
                datos_con_separador = []
                
                for taller, grupo in df_segmentado.groupby('Técnico'):
                    # Añadir fila de encabezado de Taller
                    separador = {c: '' for c in cols_ok}
                    separador['Enviado'] = f"📍 TALLER: {taller.upper()}"
                    datos_con_separador.append(separador)
                    
                    # Añadir las órdenes de ese taller
                    datos_con_separador.extend(grupo[cols_ok].to_dict('records'))
                    
                    # Añadir fila vacía de respiro
                    datos_con_separador.append({c: '' for c in cols_ok})

                df_final_excel = pd.DataFrame(datos_con_separador)
                df_final_excel.to_excel(writer, index=False, sheet_name='Reporte_Agrupado')

            st.download_button(
                label="📥 DESCARGAR REPORTE AGRUPADO POR TALLER",
                data=output.getvalue(),
                file_name=f"Consolidado_Talleres_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            # VISTA WEB POR EXPANDERS (Segmentación Visual)
            st.write("### 📋 Vista Detallada por Segmento")
            for taller in seleccionados:
                df_taller = df_segmentado[df_segmentado['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"Taller: {taller} ({len(df_taller)} órdenes)"):
                        st.dataframe(df_taller[cols_ok], hide_index=True, use_container_width=True)

        else:
            st.warning("No se encontraron órdenes con los estados 'Solicita' o 'Proceso'.")
