import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("🛠️ Monitor de Repuestos + Descarga Excel")

# Aceptamos formatos de Excel y CSV
uploaded_file = st.file_uploader("Sube tu archivo de órdenes (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # --- DETECCIÓN DE FORMATO ---
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # Limpieza de nombres de columnas y celdas
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
        
        # Filtrar
        df_filtrado = df[(cond_solicita | cond_proceso_valido) & cond_no_go & cond_no_lista_negra].copy()
        
        if not df_filtrado.empty:
            st.success(f"✅ {len(df_filtrado)} órdenes listas para procesar.")

            # --- BOTÓN DE DESCARGA GLOBAL ---
            # Creamos el archivo Excel en memoria
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado.to_excel(writer, index=False, sheet_name='Reporte_Filtrado')
            
            st.download_button(
                label="📥 Descargar Reporte Filtrado (Excel)",
                data=output.getvalue(),
                file_name="reporte_repuestos_filtrado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.divider()

            # --- LISTAS POR TALLER ---
            talleres = sorted(df_filtrado['Técnico'].unique())
            for taller in talleres:
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                with st.expander(f"📍 {taller} - ({len(datos_taller)} órdenes)"):
                    cols = ['#Orden', 'Fecha', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
                    st.dataframe(datos_taller[[c for c in cols if c in df.columns]], use_container_width=True, hide_index=True)
            
        else:
            st.warning("No hay datos que coincidan con los filtros.")

    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
