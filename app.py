import streamlit as st
import pd as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador Pro - Gestión Repuestos", layout="wide")

# --- BANNER PRINCIPAL ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ CONSOLIDADOR DE REPUESTOS</h1>
        <p style="margin:0;">Control de Procesados y Filtros Especiales - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
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
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Limpiar y Normalizar
        for col in ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo', 'Producto']:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTROS RIGUROSOS
        mask_estado = df_total['Estado'].str.contains('Repuestos', case=False, na=False)
        mask_no_envio = ~df_total['Estado'].str.contains('Envio', case=False, na=False)
        mask_no_go = ~df_total['Técnico'].str.upper().str.startswith('GO', na=False)
        mask_con_repuesto = df_total['Repuestos'].str.len() > 0
        
        df_filtrado = df_total[mask_estado & mask_no_envio & mask_no_go & mask_con_repuesto].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # --- PANEL DE CONTROL (BARRA LATERAL) ---
            st.sidebar.header("⚙️ OPCIONES DE VISTA")
            
            # Opción Ocultar Televisores
            ocultar_tvs = st.sidebar.checkbox("🚫 Ocultar Televisores / TVs", value=False)
            if ocultar_tvs:
                df_filtrado = df_filtrado[~df_filtrado['Producto'].str.contains('TELEVISOR|TV', case=False, na=False)]

            # Filtro por Taller
            talleres_finales = sorted(df_filtrado['Técnico'].unique())
            seleccion = st.sidebar.multiselect("Filtrar por Taller", talleres_finales, default=talleres_finales)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion)].sort_values('Técnico')

            # 3. COLUMNAS DE CONTROL (Checkboxes en la tabla)
            # Añadimos la columna interactiva al dataframe
            df_final['Procesado/Enviado'] = False
            
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            columnas_vista = ['Procesado/Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            
            st.metric("Órdenes para Gestión", len(df_final))

            # 4. TABLA INTERACTIVA CON CHECKBOXES
            st.write("### 📋 Listado de Control de Repuestos")
            st.info("Puedes marcar el checkbox en la columna 'Procesado/Enviado' para llevar el control manual.")
            
            # Usamos st.data_editor para permitir que los checkboxes sean clicables
            df_editado = st.data_editor(
                df_final[columnas_vista],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Procesado/Enviado": st.column_config.CheckboxColumn(
                        "Pedido Procesado",
                        help="Marca si ya gestionaste este pedido",
                        default=False,
                    )
                },
                disabled=[col for col in columnas_vista if col != "Procesado/Enviado"] # Solo el checkbox es editable
            )

            # 5. DESCARGA DE EXCEL
            # El excel incluirá el estado de los checkboxes marcados
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_editado.to_excel(writer, index=False, sheet_name='Control_Repuestos')

            st.download_button(
                label="📥 DESCARGAR EXCEL (Incluye estado de Checkboxes)",
                data=output.getvalue(),
                file_name=f"Control_Repuestos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )
        else:
            st.warning("No hay órdenes con los filtros aplicados.")
