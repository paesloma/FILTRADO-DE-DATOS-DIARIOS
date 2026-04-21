import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador Total", layout="wide")

# --- BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ CONSOLIDADOR: REVISIÓN TOTAL</h1>
        <p style="margin:0;">Reporte sin restricciones de texto - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
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
        # 1. UNIFICAR
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Limpieza de textos y nulos
        cols_limpiar = ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']
        for col in cols_limpiar:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTRADO FLEXIBLE (Sin restricción de caracteres en Repuestos)
        # Esto asegura que si el estado es "Proceso" o "Solicita", la orden pase SIEMPRE
        mask_estado = df_total['Estado'].str.contains('Solicita|Proceso', case=False, na=False)
        
        # Eliminamos duplicados por #Orden para no contar dos veces lo mismo entre archivos
        df_filtrado = df_total[mask_estado].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN VISUAL
            st.sidebar.header("Segmentar por Taller")
            todos_talleres = sorted(df_filtrado['Técnico'].unique())
            seleccionados = st.sidebar.multiselect("Talleres detectados", todos_talleres, default=todos_talleres)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccionados)].sort_values('Técnico')

            # 4. PREPARACIÓN DE COLUMNAS
            df_final['Enviado'] = "[  ]"
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            columnas_orden = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            cols_ok = [c for c in columnas_orden if c in df_final.columns or c == 'Enviado']

            # MÉTRICAS
            st.metric("Órdenes Únicas Encontradas", len(df_final))

            # 5. GENERAR EXCEL AGRUPADO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                datos_reporte = []
                for taller, grupo in df_final.groupby('Técnico'):
                    # Fila de Taller
                    separador = {c: '' for c in cols_ok}
                    separador['Enviado'] = f"📍 TALLER: {taller.upper()}"
                    datos_reporte.append(separador)
                    # Datos
                    datos_reporte.extend(grupo[cols_ok].to_dict('records'))
                    # Espacio
                    datos_reporte.append({c: '' for c in cols_ok})
                
                pd.DataFrame(datos_reporte).to_excel(writer, index=False, sheet_name='Repuestos')

            st.download_button(
                label="📥 DESCARGAR REPORTE CON LOS 14 REGISTROS",
                data=output.getvalue(),
                file_name="consolidado_final.xlsx",
                use_container_width=True
            )

            # VISTA EN WEB
            for taller in seleccionados:
                df_taller = df_final[df_final['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"📍 {taller} ({len(df_taller)} órdenes)"):
                        st.dataframe(df_taller[cols_ok], hide_index=True, use_container_width=True)
        else:
            st.warning("No se encontraron órdenes con los estados indicados.")
