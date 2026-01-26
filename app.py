import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("📊 Reporte con Contador por Taller")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        df.columns = df.columns.str.strip()
        
        # --- FILTRADO ESTRICTO ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = df['Repuestos'].astype(str).str.len() > 2 
        cond_estado = cond_solicita | (es_proceso & tiene_datos)

        # Exclusión definitiva de GO, STDIGICENT, STBMDIGI, TCLCUE, TCLCUENC
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        df_filtrado = df[cond_estado].copy()
        df_filtrado = df_filtrado[~df_filtrado['Técnico'].str.upper().str.contains(patron_excluir, na=False)]
        
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        # Columnas finales
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        cols_disp = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[cols_disp]

        if not df_filtrado.empty:
            st.success(f"✅ Reporte listo: {len(df_filtrado)} órdenes encontradas.")

            # --- GENERACIÓN DE EXCEL ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                # Estilos
                header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid') 
                sep_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')    
                white_font = Font(color='FFFFFF', bold=True)
                black_bold = Font(color='000000', bold=True)
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = white_font
                    cell.alignment = Alignment(horizontal='center')
                    cell.border = border

                # Lógica para insertar FILA con NOMBRE y CONTEO
                idx_tech = cols_disp.index('Técnico') + 1
                row = 2
                while row <= ws.max_row:
                    curr_tech = ws.cell(row=row, column=idx_tech).value
                    prev_tech = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                    
                    if prev_tech and curr_tech != prev_tech and prev_tech != "Técnico":
                        # Contar cuántas órdenes tiene este nuevo taller
                        conteo = len(df_filtrado[df_filtrado['Técnico'] == curr_tech])
                        
                        ws.insert_rows(row)
                        for col in range(1, len(cols_disp) + 1):
                            cell = ws.cell(row=row, column=col)
                            cell.fill = sep_fill
                            cell.border = border
                            if col == 1: 
                                cell.value = f"TALLER: {curr_tech} | TOTAL ÓRDENES: {conteo}"
                                cell.font = black_bold
                        row += 1
                    row += 1

            st.download_button("📥 Descargar Excel con Contadores", output.getvalue(), "Reporte_Repuestos_Contador.xlsx")

            # Vista previa web
            st.divider()
            for taller in sorted(df_filtrado['Técnico'].unique()):
                num = len(df_filtrado[df_filtrado['Técnico'] == taller])
                with st.expander(f"📍 {taller} ({num} órdenes)"):
                    st.table(df_filtrado[df_filtrado['Técnico'] == taller][cols_disp])
        else:
            st.warning("No se encontraron datos con los filtros aplicados.")

    except Exception as e:
        st.error(f"Error: {e}")
