import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Filtro Solicita Repuestos", layout="wide")

st.title("🛠️ Solo Solicita Repuestos")
st.markdown("Buscando todos los registros que contengan la palabra **'Solicita'** en el Estado.")

uploaded_file = st.file_uploader("Sube tu archivo ordenes.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Leer archivo con punto y coma
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # 3. Limpiar datos de las columnas clave
        for col in ['Estado', 'Técnico']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- FILTRADO FLEXIBLE ---
        # Buscamos la palabra "SOLICITA" en cualquier parte del texto del Estado
        # Y seguimos excluyendo a los técnicos que empiezan con "GO"
        
        cond_solicita = df['Estado'].str.contains('SOLICITA', case=False, na=False)
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        
        df_filtrado = df[cond_solicita & cond_no_go].copy()
        
        if not df_filtrado.empty:
            st.success(f"✅ ¡Éxito! Se encontraron {len(df_filtrado)} órdenes en estado 'Solicita'.")
            
            # Gráfico de barras
            resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                fig, ax = plt.subplots(figsize=(10, 5))
                resumen.plot(kind='bar', ax=ax, color='#9b59b6')
                ax.set_ylabel("Cant. Órdenes")
                for i, v in enumerate(resumen):
                    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
                st.pyplot(fig)
            
            with col2:
                st.write("**Conteo por Técnico:**")
                st.table(resumen)
            
            st.divider()
            # Mostrar tabla con Serie/Artículo
            st.subheader("📋 Listado Detallado")
            cols_ver = ['#Orden', 'Técnico', 'Estado', 'Serie/Artículo', 'Producto', 'Repuestos']
            cols_finales = [c for c in cols_ver if c in df.columns]
            st.dataframe(df_filtrado[cols_finales], use_container_width=True)
            
        else:
            st.warning("No se encontraron coincidencias. Por favor, revisa que la columna 'Estado' contenga la palabra 'Solicita'.")
            # Esto te ayudará a ver qué nombres de columnas detectó el programa realmente
            with st.expander("Ver nombres de columnas detectadas"):
                st.write(list(df.columns))
                st.write("Muestra de estados encontrados:", df['Estado'].unique())

    except Exception as e:
        st.error(f"Error al procesar: {e}")
