import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de página
st.set_page_config(page_title="Control de Órdenes", layout="wide")

st.title("📊 Monitor de Repuestos (Filtro Total)")

uploaded_file = st.file_uploader("Sube tu archivo ordenes.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Leer con separador punto y coma
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza total de nombres de columnas
        df.columns = df.columns.str.strip()
        
        # 3. Limpieza de datos en las celdas (Elimina espacios invisibles y estandariza texto)
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- APLICACIÓN DE REGLAS ---
        
        # Regla: Solicita Repuestos (Sin restricciones de columna Repuestos)
        # Usamos .upper() para evitar fallos por mayúsculas/minúsculas
        cond_solicita = (df['Estado'].str.upper() == "SOLICITA REPUESTOS")
        
        # Regla: Proceso/Repuestos (Debe tener algo escrito en columna Repuestos)
        cond_proceso = (
            (df['Estado'].str.upper() == "PROCESO/REPUESTOS") & 
            (df['Repuestos'].str.upper() != "NAN") & 
            (df['Repuestos'] != "") & 
            (df['Repuestos'] != "0")
        )
        
        # Regla: Excluir técnicos que empiezan con "GO"
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO')
        
        # Filtrado final
        df_filtrado = df[(cond_solicita | cond_proceso) & cond_no_go].copy()
        
        if not df_filtrado.empty:
            st.success(f"✅ Se han filtrado {len(df_filtrado)} órdenes correctamente.")
            
            # Gráfico de Barras por Técnico
            resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            col1, col2 = st.columns([2, 1])
            with col1:
                st.subheader("Órdenes por Técnico")
                fig, ax = plt.subplots(figsize=(10, 5))
                resumen.plot(kind='bar', ax=ax, color='#3498db', edgecolor='black')
                ax.set_ylabel("Cant. Órdenes")
                plt.xticks(rotation=45, ha='right')
                # Etiquetas sobre las barras
                for i, v in enumerate(resumen):
                    ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
                st.pyplot(fig)
            
            with col2:
                st.subheader("Resumen Numérico")
                st.table(resumen)
            
            st.divider()
            # Tabla Detallada con Serie/Artículo
            st.subheader("📋 Detalle de Órdenes")
            cols_finales = ['#Orden', 'Fecha', 'Técnico', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
            # Mostrar solo las columnas que existan en el archivo
            columnas_visibles = [c for c in cols_finales if c in df_filtrado.columns]
            st.dataframe(df_filtrado[columnas_visibles], use_container_width=True)
            
        else:
            st.warning("No se encontraron datos. Verifica que el archivo tenga los estados 'Solicita Repuestos' o 'Proceso/Repuestos'.")
            
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
else:
    st.info("Sube el archivo CSV para ver los resultados.")
