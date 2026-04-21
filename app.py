import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador Pro - Gestión Repuestos", layout="wide")

# --- BANNER PRINCIPAL ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ CONSOLIDADOR DE REPUESTOS</h1>
        <p style="margin:0;">Filtros: Sin Técnicos "GO", Sin Estado "Envio" y Opción de Ocultar TVs - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

# 1. CARGA DE ARCHIVOS
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
        # UNIFICAR Y LIMPIAR
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Normalizar textos y rellenar vacíos
        for col in ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo', 'Producto']:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTROS DE SEGURIDAD (Para llegar a las 14 órdenes clave)
        mask_estado = df_total['Estado'].str.contains('Repuestos', case=False, na=False)
        mask_no_envio = ~df_total['Estado'].str.contains('Envio', case=False, na=False)
        mask_no_go = ~df_total['Técnico'].str.upper().str.startswith('GO', na=False)
        mask_con_repuesto = df_total['Repuestos'].str.len() > 0
        
        df_filtrado = df_total[mask_estado & mask_no_envio & mask_no_go & mask_con_repuesto].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # --- PANEL DE CONTROL (BARRA LATERAL) ---
            st.sidebar.header("⚙️ OPCIONES DE VISTA")
            
            # BOTÓN PARA OCULTAR TELEVISORES
            ocultar_tvs = st.sidebar.checkbox("🚫 Ocultar Televisores / TVs", value=False)
            
            if ocultar_tvs:
                # Excluimos cualquier producto que diga TELEVISOR o TV
                df_filtrado = df_filtrado[~df_filtrado['Producto'].str.contains('TELEVISOR|TV', case=False, na=False)]

            # Segmentación por Taller
            talleres_finales = sorted(df_filtrado['Técnico'].unique())
            seleccion = st.sidebar.multiselect("Filtrar por Taller", talleres_finales, default=talleres_finales)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion)].sort_values('Técnico')
            
            # MÉTRICAS DINÁMICAS
            st.metric("Órdenes en Pantalla", len(df_final))

            # 3. PREPARACIÓN DE COLUMNAS
            df_final['Enviado'] = "[  ]"
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            cols_ok = [c for c in columnas if c in df_final.columns or c == 'Enviado']

            # 4. BOTÓN DE DESCARGA
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                reporte_excel = []
                for taller, grupo in df_final.groupby('Técnico'):
                    reporte_excel.append({c: '' for c in cols_ok})
                    reporte_excel.append({cols_ok[0]: f"📍 TALLER: {taller.upper()}"})
                    reporte_excel.extend(grupo[cols_ok].to_dict('records'))
                
                pd.DataFrame(reporte_excel).to_excel(writer, index=False, sheet_name='Repuestos')

            st.download_button(
                label="📥 DESCARGAR EXCEL FILTRADO",
                data=output.getvalue(),
                file_name=f"Reporte_Repuestos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            # 5. VISTA POR TALLER (SEGMENTACIÓN)
            st.write("### 📋 Detalle de Órdenes por Taller")
            for taller in seleccion:
                df_taller = df_final[df_final['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"📍 {taller} ({len(df_taller)} órdenes)"):
                        st.dataframe(df_taller[cols_ok], hide_index=True, use_container_width=True)
        else:
            st.warning("No hay órdenes que coincidan con los filtros actuales.")
