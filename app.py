import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador de Repuestos", layout="wide")

# --- BANNER DE LA APLICACIÓN ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ GESTIÓN DE REPUESTOS: FILTRO ESTRICTO</h1>
        <p style="margin:0;">Excluyendo Técnicos "GO" y Estado "Envio" - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

archivos = st.file_uploader("Sube tus archivos Excel o CSV", type=["xls", "xlsx", "csv"], accept_multiple_files=True)

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
            st.error(f"Error al leer {arc.name}: {e}")

    if lista_df:
        # 1. UNIFICAR Y LIMPIAR
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Limpiar celdas vacías y normalizar textos
        for col in ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTROS DE PRECISIÓN
        # A. Debe ser un estado de Repuestos pero NO "Envio"
        mask_estado = df_total['Estado'].str.contains('Repuestos', case=False, na=False)
        mask_no_envio = ~df_total['Estado'].str.contains('Envio', case=False, na=False)
        
        # B. EXCLUSIÓN DE TÉCNICOS "GO"
        mask_no_go = ~df_total['Técnico'].str.upper().str.startswith('GO', na=False)
        
        # C. REPUESTOS CON INFORMACIÓN (Evita órdenes vacías)
        mask_con_texto = df_total['Repuestos'].str.len() > 0
        
        # Aplicar todos los filtros y eliminar duplicados por #Orden
        df_filtrado = df_total[mask_estado & mask_no_envio & mask_no_go & mask_con_texto].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # 3. MÉTRICAS Y SEGMENTACIÓN
            st.sidebar.header("Opciones de Taller")
            talleres_finales = sorted(df_filtrado['Técnico'].unique())
            seleccion = st.sidebar.multiselect("Talleres a mostrar", talleres_finales, default=talleres_finales)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion)].sort_values('Técnico')
            
            st.metric("Órdenes para Gestión", len(df_final))

            # 4. PREPARACIÓN DE COLUMNAS
            df_final['Enviado'] = "[  ]"
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            cols_ok = [c for c in columnas if c in df_final.columns or c == 'Enviado']

            # 5. GENERACIÓN DE EXCEL (Usando openpyxl)
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                reporte_agrupado = []
                for taller, grupo in df_final.groupby('Técnico'):
                    # Fila estética de separación
                    reporte_agrupado.append({c: '' for c in cols_ok})
                    reporte_agrupado.append({cols_ok[0]: f"📍 TALLER: {taller.upper()}"})
                    reporte_agrupado.extend(grupo[cols_ok].to_dict('records'))
                
                pd.DataFrame(reporte_agrupado).to_excel(writer, index=False, sheet_name='Repuestos_Sin_Envios')

            st.download_button(
                label="📥 DESCARGAR REPORTE LIMPIO (EXCEL)",
                data=output.getvalue(),
                file_name=f"Reporte_Repuestos_Final_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            # VISTA EN PANTALLA (Agrupada)
            for taller in seleccion:
                df_taller = df_final[df_final['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"📍 {taller} ({len(df_taller)} órdenes)"):
                        st.dataframe(df_taller[cols_ok], hide_index=True, use_container_width=True)
        else:
            st.warning("No se encontraron órdenes que coincidan con los filtros (Sin Envios, Sin Técnicos GO).")
