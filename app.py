import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="Filtro de Repuestos Estricto", layout="wide")

st.title("📊 Reporte de Repuestos (Limpieza Total)")

uploaded_file = st.file_uploader("Sube tu archivo (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de columnas (Eliminar espacios locos)
        df.columns = df.columns.str.strip()
        
        # Limpieza de datos en celdas
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- FILTRO DE ESTADOS ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = (df['Repuestos'].str.lower() != 'nan') & (df['Repuestos'] != '') & (df['Repuestos'] != '0')
        cond_estado = cond_solicita | (es_proceso & tiene_datos)

        # --- FILTRO DE TÉCNICOS (MÁXIMA RESTRICCIÓN) ---
        # 1. Convertimos a mayúsculas y quitamos TODO espacio en blanco
        tech_to_check = df['Técnico'].str.upper().str.replace(r'\s+', '', regex=True)
        
        # 2. Definimos las "Palabras Prohibidas"
        prohibidos = ['GO', 'STDIGICENT', 'STBMDIGI', 'TCLCUE', 'TCLCUENC']
        
        # 3. Solo pasan los que NO empiezan con GO y NO son iguales a los prohibidos
        # Usamos una función lambda para mayor seguridad
        mask_tecnicos = tech_to_check.apply(lambda x: not any(p in x for p in prohibidos) if 'GO' not in x[:2] else False)
        
        # APLICAR FILTRO FINAL
        df_filtrado = df[cond_estado & mask_tecnicos].copy()
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        # Columnas finales
        columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
        cols_disp = [c for c in columnas_finales if c in df_filtrado.columns]
        df_export = df_filtrado[cols_disp]

        if not df_filtrado.empty:
            st.success(f"✅ Se han filtrado {len(df_filtrado)} órdenes. Los técnicos excluidos han sido eliminados.")

            # --- EXCEL CON FORMATO ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                # Estilos (Azul y Gris)
                header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                sep_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
                white_font = Font(color='FFFFFF', bold=True)
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = white_font
                    cell.border = border

                # Insertar separadores
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

            st.download_button("📥 Descargar Excel Filtrado", output.getvalue(), "Reporte_Limpio.xlsx")

            # --- VISTA PREVIA Y AUDITORÍA ---
            st.divider()
            st.subheader("🔍 Auditoría de Técnicos en este Reporte")
            st.write("Técnicos que pasaron el filtro:", df_filtrado['Técnico'].unique())
            
            for taller in sorted(df_filtrado['Técnico'].unique()):
                with st.expander(f"📍 Taller: {taller}"):
                    st.dataframe(df_filtrado[df_filtrado['Técnico'] == taller][cols_disp], hide_index=True)
        else:
            st.warning("No hay datos. Todos los registros fueron excluidos por los filtros.")
            st.write("Técnicos detectados en el archivo original:", df['Técnico'].unique())

    except Exception as e:
        st.error(f"Error: {e}")
