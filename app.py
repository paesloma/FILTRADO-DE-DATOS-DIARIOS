import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Control de Repuestos", layout="wide")

st.title("📊 Gestión de Órdenes y Repuestos")
st.markdown("Filtros: **Solicita Repuestos** (Todos) y **Proceso/Repuestos** (Con detalle). Excluye técnicos **'GO'**.")

uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # Leer con el separador de tu archivo
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # --- LIMPIEZA PROFUNDA ---
        # 1. Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # 2. Limpiar espacios en blanco dentro de las celdas de texto
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- LÓGICA DE FILTRADO ---
        
        # Regla 1: Estado es "Solicita Repuestos" (sin importar la columna repuestos)
        cond_solicita = (df['Estado'] == "Solicita Repuestos")
        
        # Regla 2: Estado es "Proceso/Repuestos" Y tiene algo escrito en Repuestos
        # (Filtramos que no sea 'nan', ni vacío, ni '0')
        cond_proceso = (
            (df['Estado'] == "Proceso/Repuestos") & 
            (df['Repuestos'] != "nan") & 
            (df['Repuestos'] != "") & 
            (df['Repuestos'] != "0")
        )
        
        # Regla 3: El técnico NO empieza con "GO"
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO')
        
        # Aplicar todo
        df_filtrado = df[(cond_solicita | cond_proceso) & cond_no_go].copy()
        
        if not df_filtrado.empty:
            st.success(f"Se encontraron {len(df_filtrado)} órdenes que cumplen los criterios.")
            
            # Gráfico de Barras
            conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Órdenes por Técnico")
                fig, ax = plt.subplots(figsize=(10, 5))
                conteo_tecnicos.plot(kind='bar', ax=ax, color='#3498db')
                ax.set_ylabel("Cant. Órdenes")
                plt.xticks(rotation=45, ha='right')
                for i, v in enumerate(conteo_tecnicos):
                    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
                st.pyplot(fig)
            
            with col2:
                st.subheader("Resumen Numérico")
                st.write(conteo_tecnicos)
            
            st.divider()
            st.subheader("📋 Detalle de Órdenes")
            cols_mostrar = ['#Orden', 'Fecha', 'Técnico', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
            cols_finales = [c for c in cols_mostrar if c in df.columns]
            st.dataframe(df_filtrado[cols_finales], use_container_width=True)
            
        else:
            st.warning("El filtro resultó en 0 elementos. Revisa que los estados en el Excel sean exactos.")
            
    except Exception as e:
        st.error(f"Error técnico: {e}")
