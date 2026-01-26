import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Dashboard de Órdenes - Repuestos", layout="wide")

st.title("📊 Gestión de Órdenes: Filtro de Repuestos por Técnico")

# Carga de archivo
uploaded_file = st.file_uploader("Sube tu archivo CSV de órdenes", type=["csv"])

if uploaded_file is not None:
    # Leer el CSV
    df = pd.read_csv(uploaded_file)
    
    # 1. Filtro por Estado (Proceso/Repuestos y Solicita Repuestos)
    # Ajustamos a los nombres exactos que suelen aparecer en tus reportes
    estados_validos = ["Proceso/Repuestos", "Solicita Repuestos"]
    df_filtrado = df[df['Estado'].isin(estados_validos)].copy()
    
    # 2. Filtro: Columna 'Repuestos' NO debe estar vacía
    # Eliminamos nulos y strings vacíos
    df_filtrado = df_filtrado[df_filtrado['Repuestos'].notna() & (df_filtrado['Repuestos'].str.strip() != "")]
    
    if not df_filtrado.empty:
        st.subheader(f"✅ Órdenes Encontradas: {len(df_filtrado)}")
        
        # Mostrar tabla filtrada
        st.dataframe(df_filtrado[['#Orden', 'Técnico', 'Estado', 'Repuestos']])
        
        # 3. Agrupar por Técnico y contar órdenes
        conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
        
        # 4. Mostrar Gráfico de Barras
        st.subheader("📈 Órdenes con Repuestos Pendientes por Técnico")
        
        fig, ax = plt.subplots(figsize=(10, 5))
        conteo_tecnicos.plot(kind='bar', ax=ax, color='#3498db')
        ax.set_ylabel("Número de Órdenes")
        ax.set_xlabel("Técnico")
        plt.xticks(rotation=45)
        
        # Añadir etiquetas de valor sobre las barras
        for i, v in enumerate(conteo_tecnicos):
            ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            
        st.pyplot(fig)
        
    else:
        st.warning("No se encontraron órdenes que cumplan con los criterios (Estados específicos y con repuestos asignados).")
else:
    st.info("Por favor, sube el archivo CSV para comenzar el análisis.")
