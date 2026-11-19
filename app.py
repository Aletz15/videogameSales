import pandas as pd
import plotly.express as px
import streamlit as st

# Configuración de página
st.set_page_config(
    page_title="Dashboard Video Game Sales",
    layout="wide",
    page_icon="🎮",
)

# Estilos oscuros y ajuste para que el título superior no se corte
st.markdown(
    """
    <style>
    .stApp {
        background: #050b12;
        color: #e5e7eb;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 1.5rem;
    }

    h1 {
        color: #f8fafc;
        font-size: 2rem;
        line-height: 1.25;
        margin-bottom: 0.25rem;
    }

    .metric-card {
        background: rgba(11, 18, 30, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1rem 1.2rem;
        min-height: 120px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .metric-title {
        font-size: 0.9rem;
        font-weight: 500;
        color: #94a3b8;
        margin-bottom: 0.45rem;
    }

    .metric-value {
        font-size: clamp(1.7rem, 2.2vw, 2.5rem);
        font-weight: 700;
        color: #f8fafc;
        line-height: 1.1;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
  df = pd.read_csv("vgsales_gameSales2_clean.csv")
  df["Year"] = pd.to_numeric(df["Year"], errors="coerce").dropna().astype(int)
  for col in ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales", "Global_Sales"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
  return df


try:
  df = load_data()
except Exception as e:
  st.error(f"Error al cargar vgsales_gameSales2_clean.csv: {e}")
  st.stop()

st.title("🎮 Dashboard de Ventas de Videojuegos")
st.caption("Ventas expresadas en millones de copias vendidas.")

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Filtros")

search_name = st.sidebar.text_input(
    "Buscar juego por nombre", placeholder="Ej: Mario, GTA, Zelda..."
)

min_year, max_year = int(df["Year"].min()), int(df["Year"].max())
year_range = st.sidebar.slider(
    "Rango de años",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),
)

platforms = sorted(df["Platform"].dropna().unique())
selected_platforms = st.sidebar.multiselect(
    "Plataforma(s)",
    options=platforms,
    default=platforms,
)

genres = sorted(df["Genre"].dropna().unique())
selected_genres = st.sidebar.multiselect(
    "Género(s)",
    options=genres,
    default=genres,
)

publishers_top = (
    df.groupby("Publisher")["Global_Sales"]
    .sum()
    .sort_values(ascending=False)
    .index.tolist()
)
selected_publishers = st.sidebar.multiselect(
    "Publisher(s) (opcional)",
    options=publishers_top,
    default=[],
    help="Déjalo vacío para incluir todos los publishers.",
)

metric_options = {
    "Ventas Globales (Global_Sales)": "Global_Sales",
    "Norteamérica (NA_Sales)": "NA_Sales",
    "Europa (EU_Sales)": "EU_Sales",
    "Japón (JP_Sales)": "JP_Sales",
    "Otras Regiones (Other_Sales)": "Other_Sales",
}
selected_metric_label = st.sidebar.selectbox(
    "Métrica principal para gráficas",
    options=list(metric_options.keys()),
    index=0,
)
metric_col = metric_options[selected_metric_label]

# Aplicar filtros
df_f = df[
    (df["Year"] >= year_range[0])
    & (df["Year"] <= year_range[1])
    & (df["Platform"].isin(selected_platforms))
    & (df["Genre"].isin(selected_genres))
]

if selected_publishers:
  df_f = df_f[df_f["Publisher"].isin(selected_publishers)]

if search_name.strip():
  df_f = df_f[
      df_f["Name"].astype(str).str.contains(search_name.strip(), case=False, na=False)
  ]

if df_f.empty:
  st.warning("No hay registros que coincidan con los filtros seleccionados.")
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
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{val}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# --- PESTAÑAS ---
tab_graficas, tab_mapa, tab_tabla = st.tabs([
    "📊 Gráficas",
    "🗺️ Mapa por Región",
    "📋 Tabla y Exportación",
])

with tab_graficas:
  col_l, col_r = st.columns(2)

  with col_l:
    df_genre = (
        df_f.groupby("Genre", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=True)
    )
    fig_genre = px.bar(
        df_genre,
        x=metric_col,
        y="Genre",
        orientation="h",
        title=f"{selected_metric_label} por Género (M)",
        labels={metric_col: "Millones de copias", "Genre": "Género"},
        color=metric_col,
        color_continuous_scale="Blues",
    )
    st.plotly_chart(fig_genre, use_container_width=True)

  with col_r:
    df_year = df_f.groupby("Year", as_index=False)[metric_col].sum()
    fig_year = px.line(
        df_year,
        x="Year",
        y=metric_col,
        markers=True,
        title=f"Evolución Anual — {selected_metric_label} (M)",
        labels={metric_col: "Millones de copias", "Year": "Año"},
    )
    st.plotly_chart(fig_year, use_container_width=True)

  st.markdown("---")
  col_p1, col_p2 = st.columns(2)

  with col_p1:
    df_plat = (
        df_f.groupby("Platform", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
        .head(10)
        .sort_values(metric_col, ascending=True)
    )
    fig_plat = px.bar(
        df_plat,
        x=metric_col,
        y="Platform",
        orientation="h",
        title=f"Top 10 Plataformas — {selected_metric_label} (M)",
        labels={metric_col: "Millones de copias", "Platform": "Plataforma"},
        color=metric_col,
        color_continuous_scale="Teal",
    )
    st.plotly_chart(fig_plat, use_container_width=True)

  with col_p2:
    df_pub = (
        df_f.groupby("Publisher", as_index=False)[metric_col]
        .sum()
        .sort_values(metric_col, ascending=False)
        .head(10)
        .sort_values(metric_col, ascending=True)
    )
    fig_pub = px.bar(
        df_pub,
        x=metric_col,
        y="Publisher",
        orientation="h",
        title=f"Top 10 Publishers — {selected_metric_label} (M)",
        labels={metric_col: "Millones de copias", "Publisher": "Publisher"},
        color=metric_col,
        color_continuous_scale="Purples",
    )
    st.plotly_chart(fig_pub, use_container_width=True)

  st.markdown("---")
  col_r1, col_r2 = st.columns(2)

  with col_r1:
    reg_totals = pd.DataFrame({
        "Región": ["Norteamérica", "Europa", "Japón", "Otras Regiones"],
        "Ventas_M": [
            df_f["NA_Sales"].sum(),
            df_f["EU_Sales"].sum(),
            df_f["JP_Sales"].sum(),
            df_f["Other_Sales"].sum(),
        ],
    })
    fig_pie = px.pie(
        reg_totals,
        names="Región",
        values="Ventas_M",
        hole=0.45,
        title="Distribución de Ventas por Región (M)",
    )
    st.plotly_chart(fig_pie, use_container_width=True)

  with col_r2:
    heat_data = df_f.groupby("Genre", as_index=True)[
        ["NA_Sales", "EU_Sales", "JP_Sales", "Other_Sales"]
    ].sum()
    fig_heat = px.imshow(
        heat_data,
        text_auto=".1f",
        aspect="auto",
        title="Ventas por Género y Región (Millones)",
        labels={"x": "Región", "y": "Género", "color": "Millones"},
        color_continuous_scale="YlGnBu",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

with tab_mapa:
  st.subheader("Ventas por Región del Dataset")
  st.caption(
      "Nota: El dataset agrupa las ventas por regiones (NA, EU, JP y Otras), "
      "por lo que el mapa muestra un país representativo por cada bloque regional."
  )

  region_map = pd.DataFrame([
      {
          "Región": "Norteamérica (NA_Sales)",
          "País Referencia": "United States",
          "Ventas (M)": round(float(df_f["NA_Sales"].sum()), 2),
      },
      {
          "Región": "Europa (EU_Sales)",
          "País Referencia": "Germany",
          "Ventas (M)": round(float(df_f["EU_Sales"].sum()), 2),
      },
      {
          "Región": "Japón (JP_Sales)",
          "País Referencia": "Japan",
          "Ventas (M)": round(float(df_f["JP_Sales"].sum()), 2),
      },
      {
          "Región": "Otras Regiones (Other_Sales)",
          "País Referencia": "Brazil",
          "Ventas (M)": round(float(df_f["Other_Sales"].sum()), 2),
      },
  ])

  fig_map = px.choropleth(
      region_map,
      locations="País Referencia",
      locationmode="country names",
      color="Ventas (M)",
      hover_name="Región",
      hover_data={"País Referencia": False, "Ventas (M)": ":,.2f"},
      title="Ventas Regionales de Videojuegos (Millones de copias)",
      color_continuous_scale="Plasma",
  )
  fig_map.update_layout(height=520, margin=dict(l=10, r=10, t=50, b=10))
  st.plotly_chart(fig_map, use_container_width=True)

  st.dataframe(region_map, use_container_width=True, hide_index=True)

with tab_tabla:
  st.subheader(f"Detalle de Videojuegos ({len(df_f):,} registros)")
  df_sorted = df_f.sort_values("Global_Sales", ascending=False).reset_index(
      drop=True
  )

  st.download_button(
      label="⬇️ Descargar datos filtrados (CSV)",
      data=df_sorted.to_csv(index=False).encode("utf-8"),
      file_name="vgsales_filtrado.csv",
      mime="text/csv",
  )

  st.dataframe(df_sorted, use_container_width=True, hide_index=True)
