import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Intentar importar librerías de Excel
try:
    from openpyxl.styles import Font, PatternFill, Alignment
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
        # 1. LECTURA DE DATOS
        if uploaded_file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(uploaded_file)
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin-1')

        df.columns = df.columns.str.strip()
        
        # 2. LIMPIEZA Y FILTRADO ESTRICTO
        # Aseguramos que las columnas clave existan
        columnas_req = ['Estado', 'Técnico', 'Repuestos']
        if not all(col in df.columns for col in columnas_req):
            st.error(f"Faltan columnas necesarias. El archivo debe tener: {columnas_req}")
            st.stop()

        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_repuestos = df['Repuestos'].astype(str).str.strip().apply(lambda x: len(x) > 2 and x.lower() != 'nan')
        
        patron_excluir = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_estado = cond_solicita | (es_proceso & tiene_repuestos)
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron_excluir, na=False, regex=True)
        
        df_base = df[mask_estado & mask_tecnico].copy()

        # 3. SEGMENTACIÓN EN LA INTERFAZ (SIDEBAR)
        st.sidebar.header("⚙️ Segmentación")
        tecnicos_disponibles = sorted(df_base['Técnico'].dropna().unique())
        tecnicos_sel = st.sidebar.multiselect("Filtrar Talleres", tecnicos_disponibles, default=tecnicos_disponibles)
        
        df_filtrado = df_base[df_base['Técnico'].isin(tecnicos_sel)].sort_values(by='Técnico')

        if not df_filtrado.empty:
            # MÉTRICAS
            m1, m2, m3 = st.columns(3)
            m1.metric("📦 Órdenes", len(df_filtrado))
            m2.metric("🧑‍🔧 Talleres", df_filtrado['Técnico'].nunique())
            m3.metric("🚩 Más carga", df_filtrado['Técnico'].value_counts().idxmax())

            # PREPARACIÓN DE COLUMNAS
            df_filtrado['Enviado'] = "[  ]" 
            columnas_finales = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', 'Repuestos']
            cols_disp = [c for c in columnas_finales if c in df_filtrado.columns or c == 'Enviado']
            
            # --- GENERAR EXCEL CON SEGMENTADORES ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_filtrado[cols_disp].to_excel(writer, index=False, sheet_name='Reporte')
                ws = writer.sheets['Reporte']
                
                if EXCEL_STYLING:
                    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
                    sep_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
                    
                    # Estilo Encabezado
                    for cell in ws[1]:
                        cell.fill = header_fill
                        cell.font = Font(color='FFFFFF', bold=True)

                    # INSERCIÓN DE FILAS SEPARADORAS (Lógica corregida)
                    idx_tech = cols_disp.index('Técnico') + 1
                    row = 2
                    while row <= ws.max_row:
                        curr_val = ws.cell(row=row, column=idx_tech).value
                        prev_val = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                        
                        # Si cambia el técnico, insertamos fila de segmentación
                        if prev_val and curr_val != prev_val and row > 2:
                            ws.insert_rows(row)
                            # Formatear separador
                            ws.cell(row=row, column=1).value = f"─── TALLER: {curr_val} ───"
                            ws.cell(row=row, column=1).font = Font(bold=True, color='1F4E78')
                            for c in range(1, len(cols_disp) + 1):
                                ws.cell(row=row, column=c).fill = sep_fill
                            row += 1
                        row += 1

            st.download_button(
                label="📥 Descargar Reporte Segmentado",
                data=output.getvalue(),
                file_name=f"Reporte_Repuestos_{fecha_hoy.replace('/','-')}.xlsx",
                use_container_width=True
            )

            # VISTA WEB POR TALLER
            for taller in tecnicos_sel:
                df_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"📍 {taller} ({len(df_taller)} órdenes)"):
                        st.dataframe(df_taller[cols_disp], hide_index=True)

        else:
            st.warning("No hay datos para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error crítico: {e}")
