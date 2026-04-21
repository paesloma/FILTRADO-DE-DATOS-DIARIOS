import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador por Talleres", layout="wide")

# --- BANNER PRINCIPAL ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ GESTIÓN DE REPUESTOS POR TALLER</h1>
        <p style="margin:0;">Control interactivo y segmentación por centros de servicio - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
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
        # UNIFICAR Y NORMALIZAR COLUMNAS
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Limpiar datos nulos
        for col in ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo', 'Producto']:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTROS ESTRICTOS (PARA LLEGAR A LAS 14 ÓRDENES)
        # Estados que contienen 'Repuestos' pero NO 'Envio'
        mask_estado = df_total['Estado'].str.contains('Repuestos', case=False, na=False)
        mask_no_envio = ~df_total['Estado'].str.contains('Envio', case=False, na=False)
        
        # Exclusión de técnicos que empiezan con "GO"
        mask_no_go = ~df_total['Técnico'].str.upper().str.startswith('GO', na=False)
        
        # Solo órdenes que tienen texto en el campo Repuestos
        mask_con_texto = df_total['Repuestos'].str.len() > 0
        
        # Aplicar filtros y eliminar duplicados por número de orden
        df_filtrado = df_total[mask_estado & mask_no_envio & mask_no_go & mask_con_texto].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # --- BARRA LATERAL (FILTROS ADICIONALES) ---
            st.sidebar.header("⚙️ OPCIONES DE FILTRADO")
            
            # Botón para ocultar Televisores
            ocultar_tvs = st.sidebar.checkbox("🚫 Ocultar Televisores / TVs", value=False)
            if ocultar_tvs:
                df_filtrado = df_filtrado[~df_filtrado['Producto'].str.contains('TELEVISOR|TV', case=False, na=False)]

            # Lista de talleres para segmentar
            talleres_detectados = sorted(df_filtrado['Técnico'].unique())
            seleccion_talleres = st.sidebar.multiselect("Talleres a mostrar", talleres_detectados, default=talleres_detectados)
            
            # Filtrado final por selección de talleres
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion_talleres)].sort_values(['Técnico', 'Fecha'])
            
            # Agregar columna de Checkbox interactivo
            df_final.insert(0, 'Procesado', False)
            
            # Definir columna de Serie
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            columnas_vista = ['Procesado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']

            st.metric("Total Órdenes Únicas", len(df_final))

            # 3. AGRUPACIÓN POR TALLERES (VISTA EN PESTAÑAS)
            st.write("### 📋 Órdenes Agrupadas por Taller")
            
            if seleccion_talleres:
                # Crear una pestaña por cada taller
                tabs = st.tabs([f"📍 {t}" for t in seleccion_talleres])
                
                # Diccionario para guardar los cambios de los editores
                for i, taller in enumerate(seleccion_talleres):
                    with tabs[i]:
                        df_taller = df_final[df_final['Técnico'] == taller]
                        if not df_taller.empty:
                            st.data_editor(
                                df_taller[columnas_vista],
                                key=f"editor_{taller}",
                                hide_index=True,
                                use_container_width=True,
                                column_config={
                                    "Procesado": st.column_config.CheckboxColumn("¿Listo?", default=False)
                                },
                                disabled=[col for col in columnas_vista if col != "Procesado"]
                            )
                        else:
                            st.info("No hay órdenes pendientes para este taller.")

            # 4. BOTÓN DE DESCARGA
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Guardar cada taller en una hoja diferente de Excel
                for taller, grupo in df_final.groupby('Técnico'):
                    grupo[columnas_vista].to_excel(writer, index=False, sheet_name=taller[:30])

            st.download_button(
                label="📥 DESCARGAR EXCEL AGRUPADO POR TALLER",
                data=output.getvalue(),
                file_name=f"Reporte_Repuestos_Talleres_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )
        else:
            st.warning("No se encontraron órdenes con los criterios aplicados.")
