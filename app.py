import streamlit as st
import pandas as pd
import re
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="Control de Repuestos - Filtro Final", layout="wide")

st.title("📊 Reporte de Repuestos (Filtro Anti-Errores)")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()
        
        # --- LIMPIEZA ATÓMICA DE DATOS ---
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                # Quitamos espacios, saltos de línea y caracteres invisibles
                df[col] = df[col].astype(str).str.replace(r'[\r\n\t]', '', regex=True).str.strip()

        # --- REGLA DE ESTADOS ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        # Una columna Repuestos tiene datos si no es "nan", no está vacía y no es solo un guión o 0
        tiene_datos = df['Repuestos'].apply(lambda x: len(str(x)) > 2 and str(x).lower() != 'nan')
        
        cond_estado = cond_solicita | (es_proceso & tiene_datos)

        # --- FILTRO DE EXCLUSIÓN TOTAL (Regex) ---
        # Esta regla elimina cualquier cosa que tenga GO, STDIGICENT, etc., 
        # sin importar si tiene espacios antes o después.
        palabras_prohibidas = r'GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        
        # Filtramos: El técnico NO debe coincidir con el patrón de prohibidos
        df_filtrado = df[cond_estado].copy()
        df_filtrado = df_filtrado[~df_filtrado['Técnico'].str.contains(palabras_prohibidas, case=False, na=False)]
        
        # Ordenar por Técnico
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        # Columnas finales
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        cols_disp = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[cols_disp]

        if not df_filtrado.empty:
            st.success(f"✅ ¡Filtro aplicado con éxito! {len(df_filtrado)} órdenes encontradas.")

            # --- GENERACIÓN DE EXCEL CON SEPARADORES ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                # Estilos
                header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                sep_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
                white_font = Font(color='FFFFFF', bold=True)
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = white_font
                    cell.border = border
                
                # Insertar filas de separación
                idx_tech = cols_disp.index('Técnico') + 1
                row = 2
                while row <= ws.max_row:
                    curr = ws.cell(row=row, column=idx_tech).value
                    prev = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                    if prev and curr != prev and prev != "Técnico":
                        ws.insert_rows(row)
                        for col in range(1, len(cols_disp) + 1):
                            cell = ws.cell(row=row, column=col)
                            cell.fill = sep_fill
                            cell.border = border
                        row += 1
                    row += 1

            st.download_button("📥 Descargar Excel Reporte Final", output.getvalue(), "Reporte_Repuestos_Limpio.xlsx")

            # --- VISTA PREVIA Y VALIDACIÓN ---
            st.divider()
            st.subheader("🛠️ Técnicos Incluidos en este Reporte")
            # Esto te permite ver si se coló alguno y bajo qué nombre exacto
            st.info(f"Técnicos detectados: {', '.join(df_filtrado['Técnico'].unique())}")
            
            for taller in sorted(df_filtrado['Técnico'].unique()):
                with st.expander(f"📍 Taller: {taller}"):
                    st.table(df_filtrado[df_filtrado['Técnico'] == taller][cols_disp])
        else:
            st.warning("No se encontraron órdenes. Todos los técnicos del archivo fueron excluidos.")

    except Exception as e:
        st.error(f"Error crítico: {e}")
