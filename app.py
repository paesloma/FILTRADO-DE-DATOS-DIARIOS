import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import re

# Intentar importar librerías de Excel de forma segura
try:
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    EXCEL_STYLING = True
except ImportError:
    EXCEL_STYLING = False

st.set_page_config(page_title="Gestión de Repuestos Pro", layout="wide")

# --- BANNER SUPERIOR ---
fecha_hoy = datetime.now().strftime("%d/%m/%Y")
st.markdown(f"""
    <style>
    .main-banner {{
        background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 20px;
    }}
    </style>
    <div class="main-banner">
        <h1>🛠️ DASHBOARD DE GESTIÓN DE REPUESTOS</h1>
        <p>Reporte Consolidado al <b>{fecha_hoy}</b></p>
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.file_uploader("Sube el archivo de órdenes", type=["xls", "xlsx", "csv"])

if uploaded_file is not None:
    try:
        # --- LECTURA FLEXIBLE ---
        if uploaded_file.name.endswith('.xls'):
            df = pd.read_excel(uploaded_file, engine='xlrd')
        elif uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        else:
            # Para CSV, probamos con punto y coma primero
            df = pd.read_csv(uploaded_file, sep=';', engine='python', encoding='latin-1')
            if 'Técnico' not in df.columns:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, sep=',', engine='python', encoding='latin-1')

        # Limpieza de columnas
        df.columns = df.columns.str.strip()
        
        # --- FILTRADO ESTRICTO ---
        # 1. Estados
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_repuestos = df['Repuestos'].astype(str).str.strip().apply(lambda x: len(x) > 2 and x.lower() != 'nan')
        
        # 2. Exclusión de Técnicos (REGEX)
        # Filtra GOQUITO, GOMAQUIN, STDIGICENT, etc.
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        
        mask_estado = cond_solicita | (es_proceso & tiene_repuestos)
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_filtrado = df[mask_estado & mask_tecnico].copy()
        df_filtrado = df_filtrado.sort_values(by='Técnico')

        if not df_filtrado.empty:
            # DASHBOARD METRICS
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Órdenes", len(df_filtrado))
            m2.metric("🧑‍🔧 Talleres", df_filtrado['Técnico'].nunique())
            m3.metric("🚩 Principal", df_filtrado['Técnico'].value_counts().idxmax())

            # --- GENERAR EXCEL ---
            columnas_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
            cols_disp = [c for c in columnas_finales if c in df_filtrado.columns]
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado[cols_disp].to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                if EXCEL_STYLING:
                    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                    sep_fill = PatternFill(start_color='E7E6E6', end_color='E7E6E6', fill_type='solid')
                    
                    for cell in ws[1]:
                        cell.fill = header_fill
                        cell.font = Font(color='FFFFFF', bold=True)

                    # Inserción de separadores con nombre y contador
                    row = 2
                    while row <= ws.max_row:
                        curr = ws.cell(row=row, column=cols_disp.index('Técnico')+1).value
                        prev = ws.cell(row=row-1, column=cols_disp.index('Técnico')+1).value if row > 2 else None
                        
                        if prev and curr != prev and prev != "Técnico":
                            num = len(df_filtrado[df_filtrado['Técnico'] == curr])
                            ws.insert_rows(row)
                            for col in range(1, len(cols_disp) + 1):
                                cell = ws.cell(row=row, column=col)
                                cell.fill = sep_fill
                                if col == 1:
                                    cell.value = f"📍 TALLER: {curr} | {num} ÓRDENES"
                                    cell.font = Font(bold=True)
                            row += 1
                        row += 1

            st.download_button("📥 Descargar Reporte Excel", output.getvalue(), f"Reporte_{fecha_hoy}.xlsx", use_container_width=True)

            # Vista detallada
            for taller in sorted(df_filtrado['Técnico'].unique()):
                with st.expander(f"📍 {taller}"):
                    st.table(df_filtrado[df_filtrado['Técnico'] == taller][cols_disp])
        else:
            st.warning("No hay datos que coincidan con los filtros.")

    except Exception as e:
        st.error(f"Error al leer el archivo. Asegúrate de subir el archivo correcto. Detalle: {e}")
