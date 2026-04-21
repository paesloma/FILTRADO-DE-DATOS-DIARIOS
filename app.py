import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador 14 Órdenes", layout="wide")

# --- BANNER ---
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ CONSOLIDADOR: REPORTE DE 14 ÓRDENES</h1>
        <p style="margin:0;">Filtro de técnicos "GO" excluido - <b>{datetime.now().strftime("%d/%m/%Y")}</b></p>
    </div>
    """, unsafe_allow_html=True)

archivos = st.file_uploader("Sube tus archivos", type=["xls", "xlsx", "csv"], accept_multiple_files=True)

if archivos:
    lista_df = []
    for arc in archivos:
        try:
            if arc.name.endswith(('.xls', '.xlsx')):
                temp = pd.read_excel(arc, engine='openpyxl')
            else:
                temp = pd.read_csv(arc, sep=None, engine='python', encoding='latin-1')
            lista_df.append(temp)
        except Exception as e:
            st.error(f"Error en {arc.name}: {e}")

    if lista_df:
        # 1. UNIFICAR Y LIMPIAR
        df_total = pd.concat(lista_df, ignore_index=True)
        df_total.columns = df_total.columns.str.strip()

        # Limpiar nulos y espacios
        for col in ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']:
            if col in df_total.columns:
                df_total[col] = df_total[col].fillna('').astype(str).str.strip()

        # 2. FILTRO PARA LLEGAR A LAS 14 ÓRDENES
        # A. El estado debe tener la palabra "Repuestos"
        mask_estado = df_total['Estado'].str.contains('Repuestos', case=False, na=False)
        
        # B. El campo Repuestos NO debe estar vacío (esto quita las 50 órdenes sobrantes)
        mask_con_repuestos = df_total['Repuestos'].str.len() > 0
        
        # C. EXCLUSIÓN: No deben aparecer los que empiezan con "GO"
        mask_no_go = ~df_total['Técnico'].str.upper().str.startswith('GO', na=False)
        
        # Aplicamos filtros y eliminamos duplicados por #Orden
        df_filtrado = df_total[mask_estado & mask_con_repuestos & mask_no_go].drop_duplicates(subset=['#Orden']).copy()

        if not df_filtrado.empty:
            # 3. MÉTRICAS Y SEGMENTACIÓN
            st.sidebar.header("Segmentar por Taller")
            talleres_lista = sorted(df_filtrado['Técnico'].unique())
            seleccion = st.sidebar.multiselect("Talleres", talleres_lista, default=talleres_lista)
            
            df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccion)].sort_values('Técnico')
            
            st.metric("Órdenes Identificadas", len(df_final))

            # 4. COLUMNAS Y EXPORTACIÓN
            df_final['Enviado'] = "[  ]"
            col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
            columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
            cols_ok = [c for c in columnas if c in df_final.columns or c == 'Enviado']

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                reporte_excel = []
                for taller, grupo in df_final.groupby('Técnico'):
                    # Fila de agrupación por taller
                    reporte_excel.append({c: '' for c in cols_ok})
                    reporte_excel.append({cols_ok[0]: f"📍 TALLER: {taller.upper()}"})
                    reporte_excel.extend(grupo[cols_ok].to_dict('records'))
                
                pd.DataFrame(reporte_excel).to_excel(writer, index=False, sheet_name='Repuestos')

            st.download_button("📥 Descargar Reporte (14 Órdenes)", output.getvalue(), "reporte_14_ordenes.xlsx", use_container_width=True)

            # VISTA EN WEB (Agrupada por Taller)
            for taller in seleccion:
                df_taller = df_final[df_final['Técnico'] == taller]
                if not df_taller.empty:
                    with st.expander(f"📍 {taller} ({len(df_taller)} órdenes)"):
                        st.dataframe(df_taller[cols_ok], hide_index=True, use_container_width=True)
        else:
            st.warning("No se encontraron las 14 órdenes con los filtros aplicados.")
