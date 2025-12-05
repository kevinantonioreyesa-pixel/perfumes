import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Perfumes eBay - Proyecto Final", layout="wide")

# Usamos colores para diferenciar géneros en todos los gráficos
MAPA_COLORES = {'Hombre': '#1f77b4', 'Mujer': '#e377c2'}  

def cargar_css(archivo):
    try:
        with open(archivo) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"⚠️ Sin estilos: No se encontró '{archivo}'.")

cargar_css('estilo.css')
# Limpieza de datos
@st.cache_data
def cargar_datos():
    try:
        df_m = pd.read_csv('ebay_mens_perfume.csv').assign(Genero='Hombre')
        df_w = pd.read_csv('ebay_womens_perfume.csv').assign(Genero='Mujer')
        df = pd.concat([df_m, df_w], ignore_index=True)
        
        return df.rename(columns={
            'brand': 'Marca', 'title': 'Titulo', 'price': 'Precio_Texto', 
            'available': 'Disponibles', 'sold': 'Vendidos_Texto', 'itemLocation': 'Ubicacion'
        })
    except FileNotFoundError:
        return None

def limpiar_numero(texto, es_float=True):
    if pd.isna(texto): return 0.0 if es_float else 0
    # Extrae solo números y puntos. Si falla, devuelve 0.
    limpio = ''.join(filter(lambda x: x.isdigit() or (x == '.' and es_float), str(texto)))
    try: return float(limpio) if es_float else int(limpio)
    except: return 0.0 if es_float else 0

df = cargar_datos()

if df is None:
    st.error("Faltan los archivos CSV.")
    st.stop()

# Aplicar limpieza
df['Precio'] = df['Precio_Texto'].apply(lambda x: limpiar_numero(x, True))
df['Vendidos'] = df['Vendidos_Texto'].apply(lambda x: limpiar_numero(x, False))

# SIDEBAR 
st.sidebar.title("Gestión de Perfumería 🌸")
st.sidebar.markdown("Panel de Control")
genero_filtro = st.sidebar.radio("Género:", ["Ambos", "Hombre", "Mujer"])

# Filtrado Global
df_global = df if genero_filtro == "Ambos" else df[df['Genero'] == genero_filtro]

# INTERFAZ PRINCIPAL
st.markdown("""
    <div class="main-header" style='text-align: center; color: #6F4E37;'>
        <h1 style='font-family: Georgia;'>🌸 Análisis de Mercado: Perfumes eBay 🌸</h1>
        <p>Exploración interactiva de precios, ventas y tendencias.</p>
    </div>
    <hr>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Productos", df_global.shape[0])
col2.metric("Precio Promedio", f"${df_global['Precio'].mean():.2f}")
col3.metric("Total Ventas", f"{df_global['Vendidos'].sum():,.0f}")
col4.metric("Marcas Únicas", df_global['Marca'].nunique())
st.divider()

# GRÁFICOS
# 1. TORTA (Composición)
st.subheader("1. Composición del Mercado")
c1, c2 = st.columns([1, 2])
c1.info("Este panel muestra qué porcentaje de la base de datos corresponde a cada género.")

if genero_filtro == "Ambos":
    fig = px.pie(
        df_global, 
        names='Genero', 
        title='Distribución de Productos por Género', 
        color='Genero', 
        hole=0.4, 
        color_discrete_map=MAPA_COLORES
    )
    c2.plotly_chart(fig, use_container_width=True)
    c2.caption("📝 El anillo muestra la proporción total. Si seleccionas una sección, verás la cantidad exacta de perfumes.")
else:
    c2.warning("Selecciona 'Ambos' en el filtro lateral para ver la comparación.")

st.divider()

# BARRAS (Ranking)
st.subheader("2. Ranking de Ventas")
c1, c2 = st.columns([1, 3])
c1.markdown("Explora los líderes en ventas.")
marcas = sorted(df_global['Marca'].astype(str).unique())
marca_sel = c1.selectbox("Marca:", ["Todas"] + marcas)

if marca_sel == "Todas":
    data = df_global.groupby('Marca')['Vendidos'].sum().sort_values(ascending=False).head(10).reset_index()
    fig = px.bar(data, x='Marca', y='Vendidos', color='Vendidos', title="Top 10 Marcas Más Vendidas", color_continuous_scale='Teal')
    desc = "📝 Muestra las 10 marcas con mayor volumen de ventas acumulado. El color más oscuro indica más ventas."
else:
    data = df_global[df_global['Marca'] == marca_sel].sort_values('Vendidos', ascending=False).head(10)
    fig = px.bar(data, x='Vendidos', y='Titulo', orientation='h', title=f"Top Productos: {marca_sel}", color='Vendidos', color_continuous_scale='Teal')
    desc = f"📝 Muestra los 10 perfumes específicos más exitosos de la marca {marca_sel}. Si solo tiene una barra grande, o menor a 5, quiere decir que solo tiene sa cantidad de perfumes."

c2.plotly_chart(fig, use_container_width=True)
c2.caption(desc)

st.divider()
# ANÁLISIS DE PRECIOS
st.subheader("3. Análisis Detallado de Precios")
st.markdown("Utiliza las pestañas para ver diferentes perspectivas de los precios:")
tab1, tab2, tab3 = st.tabs(["📊 Cajas (Comparar Marcas)", "📍 Puntos (Detalle Individual)", "🎻 Violín (Densidad Género)"])

with tab1: # Box Plot
    sel = st.multiselect("Marcas a comparar:", options=marcas, default=df_global['Marca'].value_counts().head(5).index.tolist())
    if sel:
        fig = px.box(df_global[df_global['Marca'].isin(sel)], x='Marca', y='Precio', color='Marca', points="outliers", title="Rangos de Precio por Marca")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📝 La 'caja' contiene el 50% de los precios más comunes. La línea del medio es la **mediana**. Los puntos sueltos arriba son 'precios atípicos' (perfumes inusualmente caros).")

with tab2: # Strip Plot
    sel = st.multiselect("Ver puntos de:", options=marcas, default=df_global['Marca'].value_counts().head(10).index.tolist(), key="strip")
    if sel:
        fig = px.strip(
            df_global[df_global['Marca'].isin(sel)], 
            x='Marca', y='Precio', 
            color='Genero', # Diferenciamos por género
            color_discrete_map=MAPA_COLORES, # <--- Colores arreglados
            hover_data=['Titulo'], 
            stripmode='overlay'
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📝 Cada punto representa **un perfume único**. Esto permite ver la cantidad real de productos y su dispersión de precios. Los puntos azules son de hombre y los rosas de mujer.")

with tab3: # Violin Plot
    df_clean = df_global[df_global['Precio'] < 300] # Filtro visual
    if not df_clean.empty:
        fig = px.violin(
            df_clean, 
            y="Precio", x="Genero", 
            color="Genero", 
            color_discrete_map=MAPA_COLORES, # <--- Colores arreglados
            box=True, points="outliers", 
            title="Densidad de Precios"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📝 El ancho de la figura indica la **frecuencia**: cuanto más ancho, más perfumes hay a ese precio. Permite comparar si los precios de un género están más concentrados o dispersos que el otro.")
    else:
        st.warning("Sin datos suficientes.")

with st.expander("Ver Datos Crudos"):
    st.dataframe(df_global)
