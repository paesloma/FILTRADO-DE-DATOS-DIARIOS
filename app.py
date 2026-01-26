import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos - Filtrado", layout="wide")

st.title("📊 Reporte de Repuestos (Técnicos Autorizados)")
st.markdown("""
**Filtros de Exclusión Aplicados:**
* 🚫 **Prefijos:** No se muestran técnicos que inicien con 'GO'.
* 🚫 **Específicos:** Se excluyen STDIGICENT, STBMDIGI, TCLCUE y TCLCUENC.
""")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura inteligente
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
        
        # Estados
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = (df['Repuestos'].str.lower() != 'nan') & (df['Repuestos'] != '') & (df['Repuestos'] != '0')
        cond_estado = cond_solicita | (es_proceso & tiene_datos)

        # Exclusiones de técnicos
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        lista_negra = ['STDIGICENT', 'STBMDIGI', 'TCLCUE', 'TCLCUENC']
        cond_no_lista = ~df['Técnico'].str.upper().isin([e.upper() for e in lista_negra])
        
        # Aplicar filtros
        df_filtrado = df[cond_estado & cond_no_go & cond_no_lista].copy()
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        # Columnas específicas
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        cols_disp = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[cols_disp]

        if not df_filtrado.empty:
            st.success(f"✅ Se han filtrado {len(df_filtrado)} registros (Exclusiones aplicadas).")

            # --- EXCEL ESTILIZADO ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                header_style = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                sep_style = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
                white_font = Font(color='FFFFFF', bold=True)
                bold_font = Font(bold=True)
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                for cell in ws[1]:
                    cell.fill = header_style
                    cell.font = white_font
                    cell.border = border

                # Insertar filas separadoras
                idx_tech = cols_disp.index('Técnico') + 1
                row = 2
                while row <= ws.max_row:
                    curr_tech = ws.cell(row=row, column=idx_tech).value
                    prev_tech = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                    if prev_tech and curr_tech != prev_tech and prev_tech != "Técnico":
                        ws.insert_rows(row)
                        for col in range(1, len(cols_disp) + 1):
                            cell = ws.cell(row=row, column=col)
                            cell.fill = sep_style
                            cell.border = border
                            if col == idx_tech:
                                cell.value = f"SECCIÓN: {curr_tech}"
                                cell.font = bold_font
                        row += 1
                    row += 1

            st.download_button(
                label="📥 Descargar Excel Filtrado",
                data=output.getvalue(),
                file_name="Reporte_Filtrado_Técnicos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # --- VISTA PREVIA WEB ---
            st.divider()
            for taller in sorted(df_filtrado['Técnico'].unique()):
                with st.expander(f"📍 Taller: {taller}"):
                    st.dataframe(df_filtrado[df_filtrado['Técnico'] == taller][cols_disp], hide_index=True)
        else:
            st.warning("No hay registros que coincidan tras las exclusiones.")

    except Exception as e:
        st.error(f"Error: {e}")
