import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración visual
st.set_page_config(page_title="Dashboard Repuestos", layout="wide")

st.title("📊 Control de Órdenes y Repuestos")
st.markdown("Filtro: Estados **'Proceso/Repuestos'** o **'Solicita Repuestos'** con repuestos asignados.")

# Carga de archivo
uploaded_file = st.file_uploader("Sube tu base de datos (CSV)", type=["csv"])

if uploaded_file:
    # Leer el CSV (ajustado a tu estructura)
    df = pd.read_csv(uploaded_file)
    
    # --- FILTRADO DE DATOS ---
    # 1. Filtro por Estado
    estados_objetivo = ["Proceso/Repuestos", "Solicita Repuestos"]
    df_filtrado = df[df['Estado'].isin(estados_objetivo)].copy()
    
    # 2. Filtro: Columna Repuestos no vacía
    # Eliminamos nulos y espacios en blanco
    df_filtrado = df_filtrado.dropna(subset=['Repuestos'])
    df_filtrado = df_filtrado[df_filtrado['Repuestos'].astype(str).str.strip() != ""]
    
    if not df_filtrado.empty:
        # Agrupación por Técnico
        conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
        
        # --- VISUALIZACIÓN ---
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Órdenes por Técnico")
            fig, ax = plt.subplots(figsize=(10, 5))
            conteo_tecnicos.plot(kind='bar', ax=ax, color='#007bff', edgecolor='black')
            ax.set_ylabel("Número de Órdenes")
            ax.set_xlabel("Técnico")
            
            # Etiquetas de datos sobre las barras
            for i, v in enumerate(conteo_tecnicos):
                ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            
            st.pyplot(fig)
            
        with col2:
            st.subheader("Resumen Numérico")
            st.write(conteo_tecnicos)
            st.metric("Total Órdenes Filtradas", len(df_filtrado))

        # Tabla detallada
        st.divider()
        st.subheader("📋 Detalle de Órdenes")
        st.dataframe(df_filtrado[['#Orden', 'Técnico', 'Estado', 'Repuestos', 'Producto']], use_container_width=True)
        
    else:
        st.warning("No se encontraron órdenes con esos estados y repuestos registrados.")
else:
    st.info("Esperando carga de archivo CSV...")
