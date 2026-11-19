import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard Video Game Sales", layout="wide", page_icon="🎮"
)

st.markdown(
    """
    <style>
    .stApp { background: #050b12; color: #e5e7eb; }
    .metric-card {
        background: #0f172a;
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px;
        padding: 1rem 1.2rem;
    }
    .metric-title { font-size: 0.9rem; color: #94a3b8; }
    .metric-value { font-size: 1.9rem; font-weight: 700; color: #f8fafc; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
  df = pd.read_csv("vgsales_gameSales2_clean.csv")
  df["Year"] = df["Year"].astype(int)
  return df


df = load_data()

st.title("🎮 Dashboard de Ventas de Videojuegos")
st.caption("Ventas expresadas en millones de copias vendidas.")

# --- FILTROS EN SIDEBAR ---
st.sidebar.header("Filtros")
min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Rango de años", min_year, max_year, (min_year, max_year)
)

platforms = sorted(df["Platform"].unique())
selected_platforms = st.sidebar.multiselect(
    "Plataforma(s)", platforms, default=platforms
)

genres = sorted(df["Genre"].unique())
selected_genres = st.sidebar.multiselect("Género(s)", genres, default=genres)

df_f = df[
    (df["Year"] >= year_range[0])
    & (df["Year"] <= year_range[1])
    & (df["Platform"].isin(selected_platforms))
    & (df["Genre"].isin(selected_genres))
]

if df_f.empty:
  st.warning("No hay registros con los filtros actuales.")
  st.stop()

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
kpis = [
    ("Ventas Globales (M)", f"{df_f['Global_Sales'].sum():,.2f}"),
    ("Ventas NA (M)", f"{df_f['NA_Sales'].sum():,.2f}"),
    ("Ventas EU (M)", f"{df_f['EU_Sales'].sum():,.2f}"),
    ("Ventas JP (M)", f"{df_f['JP_Sales'].sum():,.2f}"),
]
for col, (title, val) in zip([c1, c2, c3, c4], kpis):
  with col:
    st.markdown(
        f'<div class="metric-card"><div class="metric-title">{title}</div>'
        f'<div class="metric-value">{val}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
tab1, tab2 = st.tabs(["📊 Gráficas y Tabla", "🗺️ Mapa por Región"])

with tab1:
  col_l, col_r = st.columns(2)
  with col_l:
    df_genre = (
        df_f.groupby("Genre", as_index=False)["Global_Sales"]
        .sum()
        .sort_values("Global_Sales", ascending=False)
    )
    st.plotly_chart(
        px.bar(
            df_genre,
            x="Global_Sales",
            y="Genre",
            orientation="h",
            title="Ventas Globales por Género (Millones)",
        ),
        use_container_width=True,
    )

  with col_r:
    df_year = df_f.groupby("Year", as_index=False)["Global_Sales"].sum()
    st.plotly_chart(
        px.line(
            df_year,
            x="Year",
            y="Global_Sales",
            markers=True,
            title="Evolución Anual de Ventas Globales (Millones)",
        ),
        use_container_width=True,
    )

  st.subheader("Detalle de Videojuegos")
  st.dataframe(
      df_f.sort_values("Global_Sales", ascending=False),
      use_container_width=True,
      hide_index=True,
  )

with tab2:
  # Mapa aproximado asignando un país representativo por bloque del dataset
  region_map = pd.DataFrame([
      {
          "Region": "Norteamérica (NA_Sales)",
          "Pais_Ref": "United States",
          "Ventas_M": df_f["NA_Sales"].sum(),
      },
      {
          "Region": "Europa (EU_Sales)",
          "Pais_Ref": "Germany",
          "Ventas_M": df_f["EU_Sales"].sum(),
      },
      {
          "Region": "Japón (JP_Sales)",
          "Pais_Ref": "Japan",
          "Ventas_M": df_f["JP_Sales"].sum(),
      },
      {
          "Region": "Otras Regiones (Other_Sales)",
          "Pais_Ref": "Brazil",
          "Ventas_M": df_f["Other_Sales"].sum(),
      },
  ])
  fig_map = px.choropleth(
      region_map,
      locations="Pais_Ref",
      locationmode="country names",
      color="Ventas_M",
      hover_name="Region",
      title="Ventas por Región del Dataset (Millones de copias)",
      color_continuous_scale="Plasma",
  )
  st.plotly_chart(fig_map, use_container_width=True)
  st.dataframe(region_map, use_container_width=True, hide_index=True)
