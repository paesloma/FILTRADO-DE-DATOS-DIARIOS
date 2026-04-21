import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

st.set_page_config(page_title="Consolidador Pro", layout="wide")

st.markdown(f"""
    <div style="background: linear-gradient(90deg, #1F4E78 0%, #2E75B6 100%); padding: 20px; border-radius: 15px; color: white; text-align: center; margin-bottom: 20px;">
        <h1 style="margin:0;">🛠️ CONSOLIDADOR DE REPUESTOS</h1>
        <p style="margin:0;">Revisión de {datetime.now().strftime("%d/%m/%Y")}</p>
    </div>
    """, unsafe_allow_html=True)

archivos = st.file_uploader("Sube los archivos", type=["xls", "xlsx", "csv"], accept_multiple_files=True)

if archivos:
    lista_df = []
    for arc in archivos:
        if arc.name.endswith(('.xls', '.xlsx')):
            temp = pd.read_excel(arc, engine='openpyxl')
        else:
            temp = pd.read_csv(arc, sep=None, engine='python', encoding='latin-1')
        lista_df.append(temp)

    df_total = pd.concat(lista_df, ignore_index=True)
    df_total.columns = df_total.columns.str.strip()

    # Limpieza básica
    for col in ['Estado', 'Técnico', 'Repuestos', 'Serie', 'Serie/Artículo']:
        if col in df_total.columns:
            df_total[col] = df_total[col].fillna('').astype(str).str.strip()

    # --- FILTRO AJUSTADO PARA EVITAR PÉRDIDAS ---
    # 1. Traemos TODO lo que diga Solicita o Proceso
    mask_estado = df_total['Estado'].str.contains('Solicita|Proceso', case=False, na=False)
    
    # 2. Eliminamos duplicados por número de orden para que el conteo sea real
    df_filtrado = df_total[mask_estado].drop_duplicates(subset=['#Orden']).copy()

    if not df_filtrado.empty:
        # SEGMENTACIÓN EN BARRA LATERAL
        st.sidebar.header("Segmentar Datos")
        
        # Aquí puedes ver si GOMAQUIN o GOELECTR estaban causando la diferencia
        todos_los_tecnicos = sorted(df_filtrado['Técnico'].unique())
        seleccionados = st.sidebar.multiselect("Talleres (Revisa si faltaba alguno)", todos_los_tecnicos, default=todos_los_tecnicos)
        
        df_final = df_filtrado[df_filtrado['Técnico'].isin(seleccionados)].sort_values('Técnico')

        # MÉTRICAS
        c1, c2, c3 = st.columns(3)
        c1.metric("Órdenes Únicas", len(df_final))
        c2.metric("Archivos", len(archivos))
        c3.info("Se eliminaron duplicados por #Orden")

        # COLUMNAS
        df_final['Enviado'] = "[  ]"
        col_serie = 'Serie' if 'Serie' in df_final.columns else 'Serie/Artículo'
        columnas = ['Enviado', '#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Producto', col_serie, 'Repuestos']
        cols_ok = [c for c in columnas if c in df_final.columns or c == 'Enviado']
        
        st.dataframe(df_final[cols_ok], hide_index=True, use_container_width=True)

        # DESCARGA
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_final[cols_ok].to_excel(writer, index=False, sheet_name='Repuestos')
        
        st.download_button("📥 Descargar Consolidado", output.getvalue(), "reporte.xlsx", use_container_width=True)
    else:
        st.warning("No se encontraron órdenes con esos estados.")
