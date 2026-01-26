import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("🛠️ ARCHIVOS PENDIENTES PARA ENVIO ")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura del archivo
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza
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
        
        # Filtro y Agrupamiento (Ordenamos por Técnico)
        df_filtrado = df[(cond_solicita | cond_proceso_valido) & cond_no_go & cond_no_lista_negra].copy()
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        # Selección de columnas
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        columnas_disponibles = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[columnas_disponibles]

        if not df_filtrado.empty:
            st.success(f"✅ {len(df_filtrado)} registros organizados por taller.")

            # --- GENERACIÓN DE EXCEL CON COLORES ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                
                # Acceder a la hoja para dar formato
                workbook = writer.book
                worksheet = writer.sheets['Reporte']
                
                # Definir estilo del encabezado (Azul oscuro, letras blancas)
                from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
                
                header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                header_font = Font(color='FFFFFF', bold=True)
                alignment = Alignment(horizontal='center', vertical='center')
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                                    top=Side(style='thin'), bottom=Side(style='thin'))

                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = alignment
                    cell.border = thin_border

            st.download_button(
                label="📥 DESCARGAR LISTA PENDIENTE",
                data=output.getvalue(),
                file_name="Reporte_Repuestos_Colores.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- VISTA PREVIA ---
            st.divider()
            talleres = sorted(df_filtrado['Técnico'].unique())
            for taller in talleres:
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                with st.expander(f"📍 {taller} - ({len(datos_taller)} órdenes)"):
                    st.dataframe(datos_taller[columnas_disponibles], use_container_width=True, hide_index=True)
            
        else:
            st.warning("No hay datos que coincidan con los filtros.")

    except Exception as e:
        st.error(f"Error: {e}")
