import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("🛠️ Generador de Reporte de Repuestos")
st.markdown("Sube tu archivo para generar el Excel filtrado con las columnas específicas.")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura inteligente del archivo
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de nombres de columnas y datos
        df.columns = df.columns.str.strip()
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- LÓGICA DE FILTRADO ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = (df['Repuestos'].str.lower() != 'nan') & (df['Repuestos'] != '') & (df['Repuestos'] != '0')
        
        cond_proceso_valido = es_proceso & tiene_datos
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        
        excluidos = ['STDIGICENT', 'STBMDIGI', 'TCLCUE', 'TCLCUENC']
        cond_no_lista_negra = ~df['Técnico'].str.upper().isin([e.upper() for e in excluidos])
        
        # Filtro final
        df_filtrado = df[(cond_solicita | cond_proceso_valido) & cond_no_go & cond_no_lista_negra].copy()
        
        # --- SELECCIÓN DE COLUMNAS ESPECÍFICAS ---
        # Solo estas columnas aparecerán en el archivo final
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        # Nos aseguramos de que existan en el archivo original
        columnas_disponibles = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[columnas_disponibles]

        if not df_filtrado.empty:
            st.success(f"✅ Se han procesado {len(df_filtrado)} registros con éxito.")

            # --- BOTÓN DE DESCARGA ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Repuestos_Filtrados')
            
            st.download_button(
                label="📥 Descargar Excel Limpio",
                data=output.getvalue(),
                file_name="Reporte_Repuestos_Final.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()

            # --- VISTA PREVIA POR TALLER ---
            talleres = sorted(df_filtrado['Técnico'].unique())
            for taller in talleres:
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                with st.expander(f"📍 {taller} - ({len(datos_taller)} órdenes)"):
                    st.dataframe(datos_taller[columnas_disponibles], use_container_width=True, hide_index=True)
            
        else:
            st.warning("No se encontraron datos con los filtros aplicados.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
