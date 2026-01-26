import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la interfaz
st.set_page_config(page_title="Gestión por Talleres", layout="wide")

st.title("🧑‍🔧 Listado de Repuestos por Taller")
st.markdown("""
**Filtros de Exclusión Activos:**
* 🚫 Técnicos que inician con **'GO'**
* 🚫 **STDIGICENT, STBMDIGI, TCLCUE, TCLCUENC**
""")

uploaded_file = st.file_uploader("Sube tu archivo ordenes.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Lectura del archivo (Separador ;)
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de nombres de columnas y celdas
        df.columns = df.columns.str.strip()
        for col in ['Estado', 'Técnico']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- LÓGICA DE FILTRADO ---
        
        # Filtro A: Solo estados que contengan "Solicita"
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        
        # Filtro B: Excluir los que empiezan con "GO"
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        
        # Filtro C: Excluir lista específica (Añadido TCLCUENC)
        excluidos = ['STDIGICENT', 'STBMDIGI', 'TCLCUE', 'TCLCUENC']
        cond_no_especificos = ~df['Técnico'].str.upper().isin([e.upper() for e in excluidos])
        
        # Aplicar Filtros
        df_filtrado = df[cond_solicita & cond_no_go & cond_no_especificos].copy()
        
        if not df_filtrado.empty:
            st.success(f"Se generaron las listas para {len(df_filtrado)} órdenes.")
            
            # --- LISTAS PEQUEÑAS POR TALLER ---
            st.divider()
            talleres = sorted(df_filtrado['Técnico'].unique())
            
            for taller in talleres:
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                
                with st.expander(f"📍 Taller: {taller} - ({len(datos_taller)} órdenes)"):
                    # Columnas para la vista rápida
                    columnas = ['#Orden', 'Fecha', 'Cliente', 'Serie/Artículo', 'Producto', 'Repuestos']
                    cols_finales = [c for c in columnas if c in df.columns]
                    
                    st.dataframe(
                        datos_taller[cols_finales], 
                        use_container_width=True, 
                        hide_index=True
                    )
            
            # --- RESUMEN GRÁFICO ---
            st.divider()
            st.subheader("📈 Carga de Trabajo Actual")
            resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            fig, ax = plt.subplots(figsize=(10, 4))
            resumen.plot(kind='bar', ax=ax, color='#1abc9c', edgecolor='black')
            ax.set_ylabel("N° de Órdenes")
            for i, v in enumerate(resumen):
                ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            st.pyplot(fig)
            
        else:
            st.warning("No se encontraron órdenes para los talleres seleccionados con los filtros actuales.")

    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
