import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Control de Repuestos", layout="wide")

st.title("📊 Gestión de Órdenes y Repuestos")
st.markdown("Filtros automáticos: Estados **'Proceso/Repuestos'** y **'Solicita Repuestos'** con información en la columna **Repuestos**.")

# Carga de archivo
uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # ---------------------------------------------------------
        # CORRECCIÓN CLAVE: Agregamos sep=';' para leer tu archivo
        # También usamos engine='python' para mayor compatibilidad
        # ---------------------------------------------------------
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # Limpiamos los nombres de las columnas (quitamos espacios extra)
        df.columns = df.columns.str.strip()
        
        # Verificamos que existan las columnas necesarias
        columnas_necesarias = ['#Orden', 'Técnico', 'Estado', 'Repuestos']
        if not all(col in df.columns for col in columnas_necesarias):
            st.error(f"El archivo no tiene las columnas correctas. Se detectaron: {list(df.columns)}")
        else:
            # --- FILTROS ---
            # 1. Filtro por Estados
            estados_validos = ["Proceso/Repuestos", "Solicita Repuestos"]
            
            # 2. Aplicar lógica: Estado correcto Y columna Repuestos con texto
            df_filtrado = df[
                (df['Estado'].isin(estados_validos)) & 
                (df['Repuestos'].notna()) & 
                (df['Repuestos'].astype(str).str.strip() != "") &
                (df['Repuestos'].astype(str).str.strip() != "0") # A veces aparece 0 en nulos
            ].copy()
            
            if not df_filtrado.empty:
                # Métricas generales
                st.metric("Total Órdenes Pendientes de Repuestos", len(df_filtrado))
                
                # Agrupar por Técnico
                conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.subheader("Carga de Trabajo por Técnico")
                    fig, ax = plt.subplots(figsize=(10, 5))
                    conteo_tecnicos.plot(kind='bar', ax=ax, color='#e74c3c', edgecolor='black')
                    ax.set_ylabel("Cantidad de Órdenes")
                    plt.xticks(rotation=45, ha='right')
                    
                    # Poner números encima de las barras
                    for i, v in enumerate(conteo_tecnicos):
                        ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
                    
                    st.pyplot(fig)
                
                with col2:
                    st.subheader("Tabla Resumen")
                    st.dataframe(conteo_tecnicos, use_container_width=True)
                
                st.divider()
                st.subheader("📋 Detalle de Órdenes Filtradas")
                # Mostramos columnas clave
                cols_mostrar = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Repuestos', 'Producto']
                # Filtramos solo las columnas que existen en el df para evitar errores si falta alguna
                cols_finales = [c for c in cols_mostrar if c in df.columns]
                st.dataframe(df_filtrado[cols_finales], use_container_width=True)
                
            else:
                st.warning("No se encontraron órdenes que cumplan con los criterios (Estado correcto y Repuestos llenos).")
                
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Esperando archivo CSV...")
