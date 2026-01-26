import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Reporte por Talleres", layout="wide")

st.title("🧑‍🔧 Órdenes por Taller (Solicita Repuestos)")

uploaded_file = st.file_uploader("Sube tu archivo ordenes.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Leer archivo con punto y coma
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de nombres de columnas y datos
        df.columns = df.columns.str.strip()
        for col in ['Estado', 'Técnico']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- FILTRADO ---
        # Buscamos "Solicita" y excluimos técnicos "GO"
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        
        df_filtrado = df[cond_solicita & cond_no_go].copy()
        
        if not df_filtrado.empty:
            # Métricas generales
            st.metric("Total General de Órdenes", len(df_filtrado))
            
            # --- SECCIÓN DE LISTAS POR TALLER ---
            st.divider()
            st.header("📋 Listas por Servicio Técnico (ST)")
            
            # Obtenemos la lista única de técnicos/talleres
            talleres = sorted(df_filtrado['Técnico'].unique())
            
            # Crear pestañas o secciones por cada taller
            for taller in talleres:
                with st.expander(f"📍 Taller / ST: {taller} ({len(df_filtrado[df_filtrado['Técnico'] == taller])} órdenes)"):
                    # Filtrar datos del taller actual
                    datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                    
                    # Columnas importantes para la lista pequeña
                    cols_lista = ['#Orden', 'Fecha', 'Cliente', 'Serie/Artículo', 'Producto']
                    cols_finales = [c for c in cols_lista if c in datos_taller.columns]
                    
                    st.table(datos_taller[cols_finales])
            
            # --- GRÁFICO RESUMEN AL FINAL ---
            st.divider()
            st.subheader("📈 Resumen Comparativo de Carga")
            resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(10, 4))
            resumen.plot(kind='bar', ax=ax, color='#2ecc71')
            st.pyplot(fig)
            
        else:
            st.warning("No se encontraron órdenes en estado 'Solicita' para técnicos válidos.")

    except Exception as e:
        st.error(f"Error al procesar: {e}")
