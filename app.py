import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la página
st.set_page_config(page_title="Control de Repuestos", layout="wide")

st.title("📊 Gestión de Órdenes y Repuestos")
st.markdown("""
**Reglas de Filtro:**
1. Estados: **'Proceso/Repuestos'** o **'Solicita Repuestos'**.
2. Columna **'Repuestos'** debe tener información.
3. 🚫 **Exclusión:** Técnicos que empiezan con **'GO'** no pueden solicitar repuestos.
""")

# Carga de archivo
uploaded_file = st.file_uploader("Sube tu archivo CSV (ordenes.csv)", type=["csv"])

if uploaded_file is not None:
    try:
        # Lectura con punto y coma (;) según tu archivo
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # Limpieza de nombres de columnas
        df.columns = df.columns.str.strip()
        
        # --- APLICACIÓN DE FILTROS ---
        estados_validos = ["Proceso/Repuestos", "Solicita Repuestos"]
        
        # 1. Filtro de Estados y Repuestos no vacíos
        mask_basica = (
            (df['Estado'].isin(estados_validos)) & 
            (df['Repuestos'].notna()) & 
            (df['Repuestos'].astype(str).str.strip() != "") &
            (df['Repuestos'].astype(str).str.strip() != "0")
        )
        
        # 2. NUEVA REGLA: Excluir técnicos que empiezan con "GO"
        # Usamos .str.startswith('GO') y negamos con ~
        mask_excluir_go = ~df['Técnico'].astype(str).str.upper().str.startswith('GO')
        
        df_filtrado = df[mask_basica & mask_excluir_go].copy()
        
        if not df_filtrado.empty:
            st.metric("Total Órdenes Válidas", len(df_filtrado))
            
            # Agrupar por Técnico
            conteo_tecnicos = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Carga por Técnico (Sin Prefijo GO)")
                fig, ax = plt.subplots(figsize=(10, 5))
                conteo_tecnicos.plot(kind='bar', ax=ax, color='#f39c12', edgecolor='black')
                ax.set_ylabel("Cantidad de Órdenes")
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
            
            # Mostrar solo columnas existentes
            cols_finales = [c for c in cols_mostrar if c in df.columns]
            st.dataframe(df_filtrado[cols_finales], use_container_width=True)
            
        else:
            st.warning("No hay registros que cumplan los criterios o todos los técnicos detectados empiezan con 'GO'.")
            
    except Exception as e:
        st.error(f"Error al procesar el archivo: {e}")
else:
    st.info("Sube el archivo CSV para procesar los datos.")
