import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración estética
st.set_page_config(page_title="Control de Repuestos", layout="wide")

st.title("🛠️ Monitor de Órdenes y Repuestos")
st.markdown("Filtro aplicado: **Estados específicos** y **Con Repuestos registrados**.")

# 1. Carga de Datos
uploaded_file = st.file_uploader("Subir archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file:
    # Leer el archivo con codificación estándar
    df = pd.read_csv(uploaded_file)
    
    # --- PROCESAMIENTO DE DATOS ---
    
    # 2. Filtro por Estados específicos
    estados_objetivo = ["Proceso/Repuestos", "Solicita Repuestos"]
    df_filtrado = df[df['Estado'].isin(estados_objetivo)].copy()
    
    # 3. Filtro: Columna Repuestos NO vacía (quitamos nulos y espacios en blanco)
    df_filtrado = df_filtrado.dropna(subset=['Repuestos'])
    df_filtrado = df_filtrado[df_filtrado['Repuestos'].astype(str).str.strip() != ""]
    
    if not df_filtrado.empty:
        # --- VISUALIZACIÓN ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.metric("Total Órdenes Filtradas", len(df_filtrado))
            # Agrupar por Técnico
            resumen_tecnico = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            st.write("**Conteo por Técnico:**")
            st.table(resumen_tecnico)

        with col2:
            st.subheader("Órdenes por Técnico")
            fig, ax = plt.subplots(figsize=(8, 4))
            resumen_tecnico.plot(kind='bar', ax=ax, color='skyblue', edgecolor='navy')
            ax.set_ylabel("Cantidad de Órdenes")
            ax.set_xlabel("Técnico")
            plt.xticks(rotation=45)
            # Etiquetas de datos
            for i, v in enumerate(resumen_tecnico):
                ax.text(i, v + 0.1, str(v), ha='center')
            st.pyplot(fig)

        # Mostrar tabla detallada al final
        st.divider()
        st.subheader("Detalle de Órdenes Seleccionadas")
        st.dataframe(df_filtrado[['#Orden', 'Técnico', 'Estado', 'Repuestos', 'Producto']], use_container_width=True)
        
    else:
        st.warning("No hay datos que coincidan con los filtros (Estado 'Proceso/Repuestos' o 'Solicita Repuestos' con la columna 'Repuestos' llena).")
else:
    st.info("Esperando archivo CSV...")
