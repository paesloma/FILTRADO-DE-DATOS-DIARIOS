import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos - Listado Completo", layout="wide")

st.title("📊 Reporte de Repuestos (Todos los Técnicos)")
st.markdown("""
**Reglas del Reporte:**
* ✅ **Estado 'Solicita Repuestos'**: Incluidos todos.
* ✅ **Estado 'Proceso/Repuestos'**: Incluidos solo si la columna 'Repuestos' tiene información.
* 👥 **Técnicos**: Se muestran todos los que existan en el archivo subido.
""")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura de archivos
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # Limpieza de nombres de columnas y celdas
        df.columns = df.columns.str.strip()
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- LÓGICA DE FILTRADO ÚNICAMENTE POR ESTADO ---
        
        # Filtro para "Solicita Repuestos" (Flexible a mayúsculas/minúsculas)
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        
        # Filtro para "Proceso/Repuestos" que SÍ tengan datos escritos
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = (
            (df['Repuestos'].str.lower() != 'nan') & 
            (df['Repuestos'] != '') & 
            (df['Repuestos'] != '0')
        )
        cond_proceso_valido = es_proceso & tiene_datos
        
        # Aplicamos el filtro y ordenamos alfabéticamente por técnico
        df_filtrado = df[cond_solicita | cond_proceso_valido].copy()
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        # Definición de columnas finales para el Excel y la Web
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        columnas_disponibles = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[columnas_disponibles]

        if not df_filtrado.empty:
            st.success(f"✅ Se han procesado {len(df_filtrado)} órdenes sin exclusiones de técnicos.")

            # --- GENERACIÓN DE EXCEL ESTILIZADO CON SEPARADORES ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                # Estilos para el Excel
                header_style = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid') # Azul
                sep_style = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')    # Gris
                white_font = Font(color='FFFFFF', bold=True)
                bold_font = Font(bold=True)
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                # Aplicar estilo al encabezado
                for cell in ws[1]:
                    cell.fill = header_style
                    cell.font = white_font
                    cell.border = border
                    cell.alignment = Alignment(horizontal='center')

                # Inserción de filas de separación por taller
                idx_tech = columnas_disponibles.index('Técnico') + 1
                row = 2
                while row <= ws.max_row:
                    curr_tech = ws.cell(row=row, column=idx_tech).value
                    prev_tech = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                    
                    if prev_tech and curr_tech != prev_tech and prev_tech != "Técnico":
                        ws.insert_rows(row)
                        for col in range(1, len(columnas_disponibles) + 1):
                            cell = ws.cell(row=row, column=col)
                            cell.fill = sep_style
                            cell.border = border
                            if col == idx_tech:
                                cell.value = f"--- SECCIÓN: {curr_tech} ---"
                                cell.font = bold_font
                        row += 1
                    row += 1

            st.download_button(
                label="📥 Descargar Reporte Completo (Excel)",
                data=output.getvalue(),
                file_name="Reporte_Final_Sin_Exclusiones.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- VISTA PREVIA WEB ---
            st.divider()
            for taller in sorted(df_filtrado['Técnico'].unique()):
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                with st.expander(f"📍 Taller: {taller} ({len(datos_taller)} órdenes)"):
                    st.dataframe(datos_taller[columnas_disponibles], hide_index=True, use_container_width=True)
            
        else:
            st.warning("No se encontraron órdenes con los estados 'Solicita' o 'Proceso' (con datos).")

    except Exception as e:
        st.error(f"Error técnico al procesar el archivo: {e}")
