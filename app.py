import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

st.set_page_config(page_title="Control de Despachos Pro", layout="wide")

# --- INICIALIZAR ESTADO DE SESIÓN ---
if 'df_gestion' not in st.session_state:
    st.session_state.df_gestion = None
if 'despachados_data' not in st.session_state:
    st.session_state.despachados_data = []

# --- FUNCION EXCEL MEJORADA ---
def generar_excel_estilizado(df_input, es_despacho=False):
    output = BytesIO()
    if df_input.empty: return None
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_input.to_excel(writer, index=False, sheet_name='Reporte')
        ws = writer.sheets['Reporte']
        
        header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
        sep_fill = PatternFill(start_color='D9D9D9', end_color='D9D9D9', fill_type='solid')
        
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = Font(color='FFFFFF', bold=True)
            cell.alignment = Alignment(horizontal='center')

        # Separadores solo para Pendientes
        if not es_despacho and 'Técnico' in df_input.columns:
            idx_tech = list(df_input.columns).index('Técnico') + 1
            row = 2
            while row <= ws.max_row:
                curr = ws.cell(row=row, column=idx_tech).value
                prev = ws.cell(row=row-1, column=idx_tech).value if row > 2 else None
                if prev and curr != prev and prev != "Técnico":
                    num = len(df_input[df_input['Técnico'] == curr])
                    ws.insert_rows(row)
                    ws.cell(row=row, column=1).value = f"📍 TALLER: {curr} | {num} ÓRDENES"
                    ws.cell(row=row, column=1).font = Font(bold=True)
                    for col in range(1, len(df_input.columns) + 1):
                        ws.cell(row=row, column=col).fill = sep_fill
                    row += 1
                row += 1
    return output.getvalue()

# --- BANNER ---
fecha_actual = datetime.now().strftime("%d/%m/%Y")
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1>🛠️ PANEL DE DESPACHO NACIONAL</h1>
        <p>Control de Salida de Repuestos - <b>{fecha_actual}</b></p>
    </div>
    """, unsafe_allow_html=True)

uploaded_file = st.sidebar.file_uploader("1. Cargar Reporte Maestro", type=["xls", "xlsx", "csv"])

if uploaded_file and st.session_state.df_gestion is None:
    try:
        if uploaded_file.name.endswith('.xls'): df = pd.read_excel(uploaded_file, engine='xlrd')
        elif uploaded_file.name.endswith('.xlsx'): df = pd.read_excel(uploaded_file, engine='openpyxl')
        else: df = pd.read_csv(uploaded_file, sep=';', engine='python', encoding='latin-1')
        
        df.columns = df.columns.str.strip()
        # Filtros de exclusión total
        patron = r'^GO|STDIGICENT|STBMDIGI|TCLCUE|TCLCUENC'
        mask_tecnico = ~df['Técnico'].str.upper().str.contains(patron, na=False)
        
        # Crear un ID único real (Orden + Técnico) para evitar errores de duplicidad
        df['UID'] = df['#Orden'].astype(str) + "_" + df['Técnico'].astype(str)
        st.session_state.df_gestion = df[mask_tecnico].copy().sort_values(by='Técnico')
    except Exception as e: st.error(f"Error: {e}")

if st.session_state.df_gestion is not None:
    # Identificar ids ya despachados
    enviados_uids = [d['UID'] for d in st.session_state.despachados_data]
    
    df_pendientes = st.session_state.df_gestion[~st.session_state.df_gestion['UID'].isin(enviados_uids)]
    df_despachados = pd.DataFrame(st.session_state.despachados_data)

    # MÉTRICAS
    m1, m2, m3 = st.columns(3)
    m1.metric("📦 PENDIENTES", len(df_pendientes))
    m2.metric("✅ ENVIADOS HOY", len(df_despachados))
    m3.metric("🧑‍🔧 TALLERES", df_pendientes['Técnico'].nunique() if not df_pendientes.empty else 0)

    st.divider()

    # SIDEBAR: DESCARGAS
    st.sidebar.subheader("📥 Exportar")
    if not df_pendientes.empty:
        st.sidebar.download_button("📂 Descargar Pendientes", generar_excel_estilizado(df_pendientes), f"Pendientes_{fecha_actual}.xlsx", use_container_width=True)
    
    if not df_despachados.empty:
        st.sidebar.download_button("🟢 Descargar Despachados", generar_excel_estilizado(df_despachados, True), f"Despachados_{fecha_actual}.xlsx", use_container_width=True)

    # LISTADO INTERACTIVO
    if not df_pendientes.empty:
        for taller in sorted(df_pendientes['Técnico'].unique()):
            sub = df_pendientes[df_pendientes['Técnico'] == taller]
            with st.expander(f"📍 {taller} ({len(sub)} pendientes)"):
                for _, row in sub.iterrows():
                    col_check, col_txt = st.columns([1, 9])
                    # USAMOS UID COMO KEY PARA QUE NO SE REPITAN
                    if col_check.checkbox("Enviar", key=f"btn_{row['UID']}"):
                        nuevo_despacho = row.to_dict()
                        nuevo_despacho['Fecha_Envio'] = datetime.now().strftime("%H:%M:%S")
                        st.session_state.despachados_data.append(nuevo_despacho)
                        st.rerun()
                    col_txt.write(f"**Orden {row['#Orden']}** - {row['Cliente']} | **Repuesto:** {row['Repuestos']}")
    else:
        st.success("¡Meta cumplida! Todas las órdenes han sido despachadas.")

    if st.sidebar.button("🗑️ Reiniciar Tablero"):
        st.session_state.df_gestion = None
        st.session_state.despachados_data = []
        st.rerun()
