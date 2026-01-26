import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Configuración de la interfaz
st.set_page_config(page_title="Gestión de Repuestos", layout="wide")

st.title("🛠️ Monitor de Repuestos (Solicitudes + Proceso)")
st.markdown("""
**Reglas de Filtrado Activas:**
1. ✅ **Solicita Repuestos:** Entran todas (tengan o no detalle).
2. ✅ **Proceso/Repuestos:** Entran SOLO si tienen datos en la columna 'Repuestos'.
3. 🚫 **Excluidos:** Técnicos 'GO...' y lista negra (STDIGICENT, TCLCUENC, etc).
""")

uploaded_file = st.file_uploader("Sube tu archivo ordenes.csv", type=["csv"])

if uploaded_file is not None:
    try:
        # 1. Leer archivo (Separador ;)
        df = pd.read_csv(uploaded_file, sep=';', engine='python')
        
        # 2. Limpieza de nombres de columnas y celdas
        df.columns = df.columns.str.strip()
        
        # Convertimos a texto y quitamos espacios para evitar errores
        for col in ['Estado', 'Técnico', 'Repuestos']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # --- LÓGICA DE FILTRADO MAESTRA ---
        
        # A. Condición: Estado contiene "Solicita" (Flexible)
        cond_solicita = df['Estado'].str.contains('Solicita', case=False, na=False)
        
        # B. Condición: Estado es "Proceso/Repuestos" Y tiene datos en Repuestos
        # Verificamos que contenga "Proceso" y que Repuestos no sea "nan", vacío o "0"
        es_proceso = df['Estado'].str.contains('Proceso/Repuestos', case=False, na=False)
        tiene_datos = (
            (df['Repuestos'].str.lower() != 'nan') & 
            (df['Repuestos'] != '') & 
            (df['Repuestos'] != '0')
        )
        cond_proceso_valido = es_proceso & tiene_datos
        
        # C. Exclusiones (Técnicos GO y Lista Negra)
        cond_no_go = ~df['Técnico'].str.upper().str.startswith('GO', na=False)
        
        excluidos = ['STDIGICENT', 'STBMDIGI', 'TCLCUE', 'TCLCUENC']
        cond_no_lista_negra = ~df['Técnico'].str.upper().isin([e.upper() for e in excluidos])
        
        # --- FILTRO FINAL: (A o B) y C ---
        df_filtrado = df[(cond_solicita | cond_proceso_valido) & cond_no_go & cond_no_lista_negra].copy()
        
        if not df_filtrado.empty:
            st.success(f"✅ Se encontraron {len(df_filtrado)} órdenes gestionables.")
            
            # --- LISTAS INDIVIDUALES POR TALLER ---
            st.divider()
            talleres = sorted(df_filtrado['Técnico'].unique())
            
            for taller in talleres:
                datos_taller = df_filtrado[df_filtrado['Técnico'] == taller]
                
                with st.expander(f"📍 {taller} - ({len(datos_taller)} órdenes)"):
                    # Seleccionar columnas clave para mostrar
                    columnas_deseadas = ['#Orden', 'Fecha', 'Cliente', 'Estado', 'Serie/Artículo', 'Repuestos', 'Producto']
                    cols_finales = [c for c in columnas_deseadas if c in df.columns]
                    
                    st.dataframe(
                        datos_taller[cols_finales], 
                        use_container_width=True, 
                        hide_index=True
                    )
            
            # --- GRÁFICO TOTAL ---
            st.divider()
            st.subheader("📊 Resumen de Carga Total")
            resumen = df_filtrado.groupby('Técnico')['#Orden'].count().sort_values(ascending=False)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            resumen.plot(kind='bar', ax=ax, color='#3498db', edgecolor='black')
            ax.set_ylabel("Total Órdenes")
            for i, v in enumerate(resumen):
                ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')
            st.pyplot(fig)
            
        else:
            st.warning("No hay órdenes que cumplan los criterios (Solicita Repuestos O Proceso con datos).")

    except Exception as e:
        st.error(f"Error procesando el archivo: {e}")
