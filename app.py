import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="Control de Despachos Pro", layout="wide")

# --- INICIALIZAR ESTADO DE SESIÓN ---
if 'df_gestion' not in st.session_state:
    st.session_state.df_gestion = None
if 'enviados_ids' not in st.session_state:
    st.session_state.enviados_ids = set()

# --- FUNCIONES DE EXCEL ---
def generar_excel_estilizado(df_input, titulo_reporte):
    output = BytesIO()
    if df_input.empty: return None
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_input.to_excel(writer, index=False, sheet_name='Reporte')
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

        # Solo aplicamos separadores si hay columna Técnico y más de un taller
        if 'Técnico' in df_input.columns:
            idx_tech = list(df_input.columns).index('Técnico') + 1
            row = 2
            while row <= ws.max_row:
                curr = ws.cell(row=row, column=idx_tech).value
                prev = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                if prev and curr != prev and prev != "Técnico":
                    num = len(df_input[df_input['Técnico'] == curr])
                    ws.insert_rows(row)
                    for col in range(1, len(df_input.columns) + 1):
                        cell = ws.cell(row=row, column=col)
                        cell.fill = sep_fill
                        cell.border = border
                        if col == 1:
                            cell.value = f"TALLER: {curr} | {num} ÓRDENES"
                            cell.font = Font(bold=True)
                    row += 1
                row += 1
    return output.getvalue()

# --- BANNER ---
fecha_hoy = datetime.now().strftime("%d/%m/%Y")
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1>🛠️ SISTEMA DE DESPACHOS Y REPUESTOS</h1>
        <p>Fecha de Operación: <b>{fecha_hoy}</b></p>
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("Cargar Archivo Maestro", type=["xls", "xlsx", "csv"])

if uploaded_file and st.session_state.df_gestion is None:
    try:
        if uploaded_file.name.endswith('.xls'): df = pd.read_excel(uploaded_file, engine='xlrd')
        elif uploaded_file.name.endswith('.xlsx'): df = pd.read_excel(uploaded_file, engine='openpyxl')
        else: df = pd.read_csv(uploaded_file, sep=';', engine='python', encoding='latin-1')
        
        df.columns = df.columns.str.strip()
        # Filtros de exclusión (GO, STDIGICENT, etc.)
        patron = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron, na=False)
        
        st.session_state.df_gestion = df[mask_tecnico].copy().sort_values(by='Técnico')
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.df_gestion is not None:
    # Separación de datos
    df_pendientes = st.session_state.df_gestion[~st.session_state.df_gestion['#Orden'].isin(st.session_state.enviados_ids)]
    df_despachados = st.session_state.df_gestion[st.session_state.df_gestion['#Orden'].isin(st.session_state.enviados_ids)]

    # DASHBOARD
    c1, c2, c3 = st.columns(3)
    c1.metric("📦 PENDIENTES", len(df_pendientes))
    c2.metric("✅ DESPACHADOS", len(df_despachados))
    c3.metric("🧑‍🔧 TALLERES", df_pendientes['Técnico'].nunique() if not df_pendientes.empty else 0)

    st.divider()

    # DESCARGAS EN SIDEBAR
    st.sidebar.subheader("📥 Descargas")
    if not df_pendientes.empty:
        xlsx_pen = generar_excel_estilizado(df_pendientes, "Pendientes")
        st.sidebar.download_button("📂 Descargar Pendientes", xlsx_pen, f"Pendientes_{fecha_hoy}.xlsx", use_container_width=True)
    
    if not df_despachados.empty:
        xlsx_des = generar_excel_estilizado(df_despachados, "Despachados")
        st.sidebar.download_button("🟢 Descargar Despachados", xlsx_des, f"Despachados_{fecha_hoy}.xlsx", use_container_width=True)

    # LISTADO INTERACTIVO
    if not df_pendientes.empty:
        for taller in sorted(df_pendientes['Técnico'].unique()):
            sub_df = df_pendientes[df_pendientes['Técnico'] == taller]
            with st.expander(f"📍 {taller} ({len(sub_df)} pendientes)"):
                # Columnas de visualización
                for _, row in sub_df.iterrows():
                    col_check, col_data = st.columns([0.5, 9.5])
                    if col_check.checkbox("Marcar", key=f"check_{row['#Orden']}"):
                        st.session_state.enviados_ids.add(row['#Orden'])
                        st.rerun()
                    col_data.write(f"**Orden:** {row['#Orden']} | **Cliente:** {row['Cliente']} | **Repuesto:** {row['Repuestos']}")
    else:
        st.success("¡Excelente! No quedan órdenes pendientes.")

    if st.sidebar.button("🗑️ Reiniciar Todo"):
        st.session_state.df_gestion = None
        st.session_state.enviados_ids = set()
        st.rerun()
