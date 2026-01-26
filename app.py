import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Reporte por Talleres", layout="wide")

st.title("🧑‍🔧 Órdenes por Taller (Solicita Repuestos)")
st.markdown("""
**Filtros aplicados:**
* 🔍 **Estado:** Contiene la palabra 'Solicita'.
* 🚫 **Excluidos:** Técnicos que empiezan con 'GO', STDIGICENT, STBMDIGI y TCLCUE.
""")

uploaded_file = st.file_uploader("Sube tu archivo ordenes.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Leer archivo con punto y coma
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de nombres de columnas y datos
        df.columns = df.columns.str.strip()
        for col in ['Estado', 'Técnico']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- FILTRADO AVANZADO ---
        
        # Condición: Estado contiene "Solicita"
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        
        # Condición: Excluir los que empiezan con "GO"
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        
        # Condición: Excluir específicamente a STDIGICENT, STBMDIGI y TCLCUE
        excluidos_fijos = ['STDIGICENT', 'STBMDIGI', 'TCLCUE']
        cond_no_especificos = ~df['Técnico'].str.upper().isin([e.upper() for e in excluidos_fijos])
        
        # Aplicar todos los filtros
        df_filtrado = df[cond_solicita & cond_no_go & cond_no_especificos].copy()
        
        if not df_filtrado.empty:
            # Métricas generales
            st.metric("Total Órdenes en Listado", len(df_filtrado))
            
            # --- SECCIÓN DE LISTAS POR TALLER ---
            st.divider()
            st.header("📋 Listas por Servicio Técnico (ST)")
            
            # Obtenemos la lista única de técnicos que pasaron el filtro
            talleres = sorted(df_filtrado['Técnico'].unique())
            
            for taller in talleres:
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                
                with st.expander(f"📍 Taller: {taller} ({len(datos_taller)} órdenes)"):
                    # Columnas importantes para la lista pequeña
                    cols_lista = ['#Orden', 'Fecha', 'Cliente', 'Serie/Artículo', 'Producto', 'Repuestos']
                    cols_finales = [c for c in cols_lista if c in datos_taller.columns]
                    
                    # Usamos dataframe para que sea interactivo pero en formato pequeño
                    st.dataframe(datos_taller[cols_finales], use_container_width=True, hide_index=True)
            
            # --- GRÁFICO RESUMEN ---
            st.divider()
            st.subheader("📈 Resumen de Carga por Taller")
            resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            fig, ax = plt.subplots(figsize=(10, 4))
            resumen.plot(kind='bar', ax=ax, color='#e67e22', edgecolor='black')
            ax.set_ylabel("Cantidad")
            for i, v in enumerate(resumen):
                ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            st.pyplot(fig)
            
        else:
            st.warning("No se encontraron órdenes que cumplan con los filtros establecidos.")

    except Exception as e:
        st.error(f"Error al procesar: {e}")
else:
    st.info("Sube el archivo CSV para generar las listas por taller.")
