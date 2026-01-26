import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Control de Repuestos", layout="wide")

st.title("📊 Gestión de Órdenes y Repuestos")
st.markdown("Filtros automáticos: Estados **'Proceso/Repuestos'** y **'Solicita Repuestos'** con columna **Repuestos** llena.")

# --- CARGA DE ARCHIVO ---
uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # LECTURA DEL CSV CON PUNTO Y COMA
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # Limpieza de nombres de columnas (quita espacios invisibles)
        df.columns = df.columns.str.strip()
        
        # --- FILTROS ---
        estados_validos = ["Proceso/Repuestos", "Solicita Repuestos"]
        
        # Aplicamos la lógica de filtro
        # 1. Estado coincidente
        # 2. Repuestos no vacíos (ni nulos, ni texto vacío, ni "0" solitario)
        df_filtrado = df[
            (df['Estado'].isin(estados_validos)) & 
            (df['Repuestos'].notna()) & 
            (df['Repuestos'].astype(str).str.strip() != "") &
            (df['Repuestos'].astype(str).str.strip() != "0")
        ].copy()
        
        if not df_filtrado.empty:
            # --- MÉTRICAS ---
            st.metric("Total Órdenes Pendientes", len(df_filtrado))
            
            # --- GRÁFICO ---
            conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Carga de Trabajo por Técnico")
                fig, ax = plt.subplots(figsize=(10, 5))
                conteo_tecnicos.plot(kind='bar', ax=ax, color='#2ecc71', edgecolor='black')
                ax.set_ylabel("Cantidad de Órdenes")
                plt.xticks(rotation=45, ha='right')
                
                # Números sobre barras
                for i, v in enumerate(conteo_tecnicos):
                    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
                
                st.pyplot(fig)
            
            with col2:
                st.subheader("Resumen Numérico")
                st.dataframe(conteo_tecnicos, use_container_width=True)
            
            st.divider()
            
            # --- TABLA DE DETALLES (AQUÍ AGREGUÉ LA COLUMNA) ---
            st.subheader("📋 Detalle de Órdenes Filtradas")
            
            # Definimos las columnas que queremos ver, INCLUYENDO Serie/Artículo
            cols_mostrar = [
                '#Orden', 
                'Fecha', 
                'Técnico', 
                'Cliente', 
                'Estado', 
                'Serie/Artículo',  # <--- NUEVA COLUMNA AGREGADA
                'Repuestos', 
                'Producto'
            ]
            
            # Verificamos que las columnas existan antes de mostrarlas para evitar errores
            cols_finales = [c for c in cols_mostrar if c in df.columns]
            
            st.dataframe(df_filtrado[cols_finales], use_container_width=True)
            
        else:
            st.warning("No se encontraron órdenes que cumplan con los criterios.")
            
    except Exception as e:
        st.error(f"Error al procesar el archivo. Verifica el formato. Detalle: {e}")
else:
    st.info("Sube el archivo CSV para ver los resultados.")
