import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="Repuestos Dashboard", layout="wide")

# --- ESTILOS PERSONALIZADOS PARA EL BANNER ---
st.markdown("""
    <style>
    .main-banner {
        background-color: #1F4E78;
        padding: 20px;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
    }
    </style>
    <div class="main-banner">
        <h1>🛠️ DASHBOARD DE GESTIÓN DE REPUESTOS</h1>
        <p>Control de solicitudes y procesos a Nivel Nacional</p>
    </div>
    """, unsafe_allow_stdio=True)

uploaded_file = st.file_uploader("Sube tu archivo de órdenes (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"])

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

        # --- FILTRADO ESTRICTO ---
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = df['Repuestos'].astype(str).str.len() > 2 
        cond_estado = cond_solicita | (es_proceso & tiene_datos)

        # Exclusión de GO y otros técnicos mencionados
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        df_filtrado = df[cond_estado].copy()
        df_filtrado = df_filtrado[~df_filtrado['Técnico'].str.upper().str.contains(patron_excluir, na=False)]
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        if not df_filtrado.empty:
            # --- DASHBOARD BANNER (MÉTRICAS) ---
            total_ordenes = len(df_filtrado)
            total_tecnicos = df_filtrado['Técnico'].nunique()
            taller_top = df_filtrado['Técnico'].value_counts().idxmax()
            cant_top = df_filtrado['Técnico'].value_counts().max()

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📦 Total Órdenes", total_ordenes)
            with col2:
                st.metric("🧑‍🔧 Técnicos Activos", total_tecnicos)
            with col3:
                st.metric("🚩 Mayor Carga", taller_top, f"{cant_top} órdenes")

            st.divider()

            # --- GENERACIÓN DE EXCEL ---
            columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
            cols_disp = [c for c in columnas_finales if c in df_filtrado.columns]
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado[cols_disp].to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                # Estilos Excel
                header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid') 
                sep_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')    
                white_font = Font(color='FFFFFF', bold=True)
                black_bold = Font(color='000000', bold=True)
                border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

                for cell in ws[1]:
                    cell.fill = header_fill
                    cell.font = white_font
                    cell.border = border

                # Inserción de filas con nombre y conteo
                row = 2
                while row <= ws.max_row:
                    curr_tech = ws.cell(row=row, column=cols_disp.index('Técnico')+1).value
                    prev_tech = ws.cell(row=row-1, column=cols_disp.index('Técnico')+1).value if row > 2 else None
                    
                    if prev_tech and curr_tech != prev_tech and prev_tech != "Técnico":
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

            st.download_button("📥 Descargar Reporte Excel", output.getvalue(), "Reporte_Dashboard.xlsx", use_container_width=True)

            # --- LISTADOS WEB ---
            for taller in sorted(df_filtrado['Técnico'].unique()):
                num = len(df_filtrado[df_filtrado['Técnico'] == taller])
                with st.expander(f"📍 {taller} ({num} órdenes)"):
                    st.table(df_filtrado[df_filtrado['Técnico'] == taller][cols_disp])
        else:
            st.warning("No se encontraron datos.")

    except Exception as e:
        st.error(f"Error: {e}")
