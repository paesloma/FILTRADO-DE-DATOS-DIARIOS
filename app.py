import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Control de Repuestos", layout="wide")

st.title("📊 Gestión de Órdenes y Repuestos")
st.markdown("""
**Criterios de Selección:**
1. ✅ **Solicita Repuestos:** Se muestra siempre (tenga o no texto en la columna Repuestos).
2. ✅ **Proceso/Repuestos:** Solo se muestra si la columna 'Repuestos' tiene información.
3. 🚫 **Exclusión:** Técnicos que empiezan con **'GO'** (GOMAQUIN, GOQUITO, etc.) están fuera.
""")

# Carga de archivo
uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # Lectura con punto y coma (;)
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        df.columns = df.columns.str.strip()
        
        # --- NUEVA LÓGICA DE FILTRADO ---
        
        # Condición A: Es "Solicita Repuestos" (no importa si la columna repuestos está vacía)
        cond_solicita = (df['Estado'] == "Solicita Repuestos")
        
        # Condición B: Es "Proceso/Repuestos" Y la columna Repuestos TIENE información
        cond_proceso = (
            (df['Estado'] == "Proceso/Repuestos") & 
            (df['Repuestos'].notna()) & 
            (df['Repuestos'].astype(str).str.strip() != "") &
            (df['Repuestos'].astype(str).str.strip() != "0")
        )
        
        # Condición C: El técnico NO empieza con "GO"
        cond_no_go = ~df['Técnico'].astype(str).str.upper().str.startswith('GO')
        
        # Combinamos: (Solicita OR Proceso) AND No_es_GO
        df_filtrado = df[(cond_solicita | cond_proceso) & cond_no_go].copy()
        
        if not df_filtrado.empty:
            st.metric("Total Órdenes en Gestión", len(df_filtrado))
            
            # Gráfico y Resumen
            conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Órdenes por Técnico")
                fig, ax = plt.subplots(figsize=(10, 5))
                conteo_tecnicos.plot(kind='bar', ax=ax, color='#3498db', edgecolor='black')
                ax.set_ylabel("Cant. Órdenes")
                plt.xticks(rotation=45, ha='right')
                for i, v in enumerate(conteo_tecnicos):
                    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
                st.pyplot(fig)
            
            with col2:
                st.subheader("Resumen Numérico")
                st.dataframe(conteo_tecnicos, use_container_width=True)
            
            st.divider()
            st.subheader("📋 Detalle de Órdenes Filtradas")
            
            cols_mostrar = [
                '#Orden', 'Fecha', 'Técnico', 'Cliente', 
                'Estado', 'Serie/Artículo', 'Repuestos', 'Producto'
            ]
            cols_finales = [c for c in cols_mostrar if c in df.columns]
            st.dataframe(df_filtrado[cols_finales], use_container_width=True)
            
        else:
            st.warning("No se encontraron órdenes que cumplan los criterios actuales.")
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Sube el archivo CSV para procesar los datos.")
