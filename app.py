import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de página
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("📊 Dashboard de Órdenes y Repuestos")
st.markdown("Filtros activos: Estado **'Proceso/Repuestos'** o **'Solicita Repuestos'** + Columna **'Repuestos'** con datos.")

# Subida de archivo
uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file is not None:
    # Leer datos
    df = pd.read_csv(uploaded_file)
    
    # Limpiar espacios en nombres de columnas
    df.columns = df.columns.str.strip()

    # --- LÓGICA DE FILTRADO ---
    # 1. Filtrar por los dos estados solicitados
    estados_validos = ["Proceso/Repuestos", "Solicita Repuestos"]
    
    # 2. Filtrar que la columna 'Repuestos' no esté vacía ni sea nula
    df_filtrado = df[
        (df['Estado'].isin(estados_validos)) & 
        (df['Repuestos'].notna()) & 
        (df['Repuestos'].astype(str).str.strip() != "")
    ].copy()

    if not df_filtrado.empty:
        # Agrupar por Técnico y contar número de órdenes
        resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)

        # Visualización en columnas
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Gráfico de Órdenes por Técnico")
            fig, ax = plt.subplots(figsize=(10, 6))
            resumen.plot(kind='bar', ax=ax, color='#ff4b4b')
            ax.set_ylabel("Cantidad de Órdenes")
            ax.set_xlabel("Técnicos")
            
            # Etiquetas sobre las barras
            for i, v in enumerate(resumen):
                ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            
            st.pyplot(fig)

        with col2:
            st.subheader("Resumen Numérico")
            st.dataframe(resumen.rename("Total Órdenes"), use_container_width=True)

        st.divider()
        st.subheader("📋 Detalle de Datos Filtrados")
        st.dataframe(df_filtrado[['#Orden', 'Técnico', 'Estado', 'Repuestos', 'Producto']], use_container_width=True)
    else:
        st.warning("No se encontraron registros que cumplan los criterios.")
else:
    st.info("👋 Por favor, carga el archivo CSV extraído de tu base de datos para comenzar.")
