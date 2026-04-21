import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador de Repuestos", layout="wide")

# --- BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ GESTIÓN MULTI-ARCHIVO DE REPUESTOS</h1>
        <p style="margin:0;">Unificación y Segmentación de Reportes - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

# 1. CARGA MULTIPLE (Puedes arrastrar los 4 archivos a la vez)
archivos_cargados = st.file_uploader("Sube tus 4 archivos Excel o CSV", type=["xls", "xlsx", "csv"], accept_multiple_files=True)

if archivos_cargados:
    lista_df = []
    
    for archivo in archivos_cargados:
        try:
            if archivo.name.endswith(('.xls', '.xlsx')):
                temp_df = pd.read_excel(archivo, engine='openpyxl')
            else:
                temp_df = pd.read_csv(archivo, sep=None, engine='python', encoding='latin-1')
            
            # Limpiar nombres de columnas al importar
            temp_df.columns = temp_df.columns.str.strip()
            lista_df.append(temp_df)
        except Exception as e:
            st.error(f"Error cargando {archivo.name}: {e}")

    if lista_df:
        # UNIFICAR TODOS LOS ARCHIVOS
        df_total = pd.concat(lista_df, ignore_index=True)
        
        # --- LIMPIEZA DE DATOS ---
        columnas_criticas = ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']
        for col in columnas_criticas:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. LÓGICA DE FILTRADO (Reglas de Repuestos)
        mask_solicita = df_total['Estado'].str.contains('Solicita', case=False, na=False)
        mask_proceso = (df_total['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)) & \
                       (df_total['Repuestos'].str.len() > 2)
        
        # Filtro de técnicos a excluir (Internos)
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_tecnico_valido = ~df_total['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_filtrado = df_total[(mask_solicita | mask_proceso) & mask_tecnico_valido].copy()

        if not df_filtrado.empty:
            # 3. SEGMENTACIÓN UNIFICADA (Barra Lateral)
            st.sidebar.header("Opciones de Segmentación")
            
            # Buscamos la columna de Serie correcta
            col_serie = 'Serie' if 'Serie' in df_filtrado.columns else 'Serie/Artículo'
            
            # Filtro por Taller
            talleres = sorted(df_filtrado['Técnico'].unique())
            seleccion_talleres = st.sidebar.multiselect("Filtrar por Técnico/Taller", talleres, default=talleres)
            
            # Filtro por Estado (opcional)
            estados = sorted(df_filtrado['Estado'].unique())
            seleccion_estados = st.sidebar.multiselect("Filtrar por Estado", estados, default=estados)

            # Aplicar segmentación final
            df_final = df_filtrado[
                (df_filtrado['Técnico'].isin(seleccion_talleres)) & 
                (df_filtrado['Estado'].isin(seleccion_estados))
            ].sort_values('Técnico')

            # 4. PREPARACIÓN DE TABLA FINAL
            df_final['Enviado'] = "[  ]"
            columnas_orden = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            
            cols_visibles = [c for c in columnas_orden if c in df_final.columns or c == 'Enviado']
            df_final = df_final[cols_visibles]

            # MÉTRICAS GENERALES
            c1, c2 = st.columns(2)
            c1.metric("Archivos Procesados", len(archivos_cargados))
            c2.metric("Órdenes Totales Filtradas", len(df_final))

            # 5. DESCARGA CONSOLIDADA
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False, sheet_name='Repuestos_Unificados')
            
            st.download_button(
                label="📥 DESCARGAR REPORTE CONSOLIDADO (EXCEL)",
                data=output.getvalue(),
                file_name=f"Consolidado_Repuestos_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )

            # VISTA PREVIA
            st.dataframe(df_final, hide_index=True, use_container_width=True)

        else:
            st.warning("No se encontraron datos que cumplan los criterios en ninguno de los archivos.")
