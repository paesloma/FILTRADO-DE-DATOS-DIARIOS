import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("🛠️ Reporte con Separadores por Taller")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        df.columns = df.columns.str.strip()
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- FILTRADO ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = (df['Repuestos'].str.lower() != 'nan') & (df['Repuestos'] != '') & (df['Repuestos'] != '0')
        
        cond_proceso_valido = es_proceso & tiene_datos
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        excluidos = ['STDIGICENT', 'STBMDIGI', 'TCLCUE', 'TCLCUENC']
        cond_no_lista_negra = ~df['Técnico'].str.upper().isin([e.upper() for e in excluidos])
        
        df_filtrado = df[(cond_solicita | cond_proceso_valido) & cond_no_go & cond_no_lista_negra].copy()
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        columnas_disponibles = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[columnas_disponibles]

        if not df_filtrado.empty:
            st.success(f"✅ Reporte listo. Los talleres están agrupados y separados por color.")

            # --- GENERACIÓN DE EXCEL CON FILAS SEPARADORAS ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                
                workbook = writer.book
                worksheet = writer.sheets['Reporte']
                
                # Estilos
                header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid') # Azul
                header_font = Font(color='FFFFFF', bold=True)
                separator_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid') # Gris
                thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), 
                                    top=Side(style='thin'), bottom=Side(style='thin'))

                # Formatear encabezado
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                    cell.border = thin_border

                # Insertar filas de separación
                current_row = 2
                last_tech = None
                
                # Iteramos sobre los datos (usamos una lista de filas para no modificar el objeto mientras iteramos)
                tech_column_index = columnas_disponibles.index('Técnico') + 1
                
                row_idx = 2
                while row_idx <= worksheet.max_row:
                    tech_name = worksheet.cell(row=row_idx, column=tech_column_index).value
                    
                    if last_tech is not None and tech_name != last_tech:
                        # Insertar fila antes del nuevo técnico
                        worksheet.insert_rows(row_idx)
                        # Pintar la fila insertada
                        for col in range(1, len(columnas_disponibles) + 1):
                            cell = worksheet.cell(row=row_idx, column=col)
                            cell.fill = separator_fill
                            cell.border = thin_border
                        row_idx += 1 # Saltamos la fila que acabamos de insertar
                    
                    last_tech = tech_name
                    row_idx += 1

            st.download_button(
                label="📥 Descargar Excel con Separadores",
                data=output.getvalue(),
                file_name="Reporte_Repuestos_Separado.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- VISTA PREVIA ---
            st.divider()
            for taller in sorted(df_filtrado['Técnico'].unique()):
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                with st.expander(f"📍 {taller}"):
                    st.table(datos_taller[columnas_disponibles])
            
    except Exception as e:
        st.error(f"Error: {e}")
