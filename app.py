import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la interfaz
st.set_page_config(page_title="Filtro de Órdenes y Repuestos", layout="wide")

st.title("📊 Control de Repuestos por Técnico")
st.markdown("Filtros: Estados **'Proceso/Repuestos'** y **'Solicita Repuestos'** + Columna **'Repuestos'** con datos.")

# Cargador de archivos
uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file:
    # Leer el archivo (usamos error_bad_lines=False por si hay comas extra en observaciones)
    df = pd.read_csv(uploaded_file)
    
    # 1. Limpieza de nombres de columnas (quitar espacios en blanco)
    df.columns = df.columns.str.strip()
    
    # 2. Definir los parámetros de filtro
    estados_validos = ["Proceso/Repuestos", "Solicita Repuestos"]
    
    # Aplicar Filtros:
    # - Que el estado esté en la lista
    # - Que la columna Repuestos no sea nula ni esté vacía
    mask = (df['Estado'].isin(estados_validos)) & (df['Repuestos'].notna()) & (df['Repuestos'].astype(str).str.strip() != "")
    df_filtrado = df[mask].copy()

    if not df_filtrado.empty:
        # Agrupar por Técnico y contar número de órdenes
        conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)

        # Mostrar métricas rápidas
        st.metric("Total Órdenes Encontradas", len(df_filtrado))

        # Crear dos columnas para visualización
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("Gráfico de Carga por Técnico")
            fig, ax = plt.subplots()
            conteo_tecnicos.plot(kind='bar', ax=ax, color='#1f77b4', edgecolor='black')
            ax.set_ylabel("Cantidad de Órdenes")
            ax.set_xlabel("Técnicos")
            plt.xticks(rotation=45, ha='right')
            
            # Añadir etiquetas de número sobre las barras
            for i, v in enumerate(conteo_tecnicos):
                ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            
            st.pyplot(fig)

        with col2:
            st.subheader("Resumen Numérico")
            st.write(conteo_tecnicos)

        # Mostrar la tabla de datos completa al final
        st.divider()
        st.subheader("📋 Detalle de Órdenes Filtradas")
        st.dataframe(df_filtrado[['#Orden', 'Técnico', 'Estado', 'Repuestos']], use_container_width=True)
    else:
        st.warning("No se encontraron registros que cumplan con los filtros: Estados específicos y repuestos no vacíos.")
else:
    st.info("Por favor, sube el archivo CSV para procesar los datos.")
