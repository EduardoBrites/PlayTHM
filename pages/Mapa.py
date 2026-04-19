import pandas as pd
import numpy as np
import folium
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import matplotlib.pyplot as plt
from io import BytesIO

from pathlib import Path
from branca.colormap import LinearColormap
from folium.features import CustomIcon
from folium.plugins import Fullscreen, MiniMap, MeasureControl
from streamlit_folium import st_folium

from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import StandardScaler

from scipy.cluster.hierarchy import linkage, leaves_list, dendrogram, fcluster
from matplotlib.colors import LinearSegmentedColormap, to_hex

st.set_page_config(page_title="PlayTennis - THM", page_icon="🎾", layout="wide")

ARQUIVO_XLSX = Path("data") / "TIAGO-MARUM-Playtennis-16ABRIL2026.xlsx"
LOGO_PATH = Path("assets/img/Playtennis.png")


# =========================================================
# LEITURA
# =========================================================
@st.cache_data
def carregar_dados(caminho):
    unidades = pd.read_excel(caminho, sheet_name="Sheet1")
    unidades.columns = [str(c).strip() for c in unidades.columns]

    raw = pd.read_excel(caminho, sheet_name="LOJAS", header=None)

    metricas = [
        "Renda_media",
        "Praticam_Tenis",
        "Praticam_Esporte",
        "Domicilios",
        "Populacao",
        "H_20_24",
        "H_25_29",
        "H_30_39",
        "H_40_49",
        "H_50_59",
        "M_20_24",
        "M_25_29",
        "M_30_39",
        "M_40_49",
        "M_50_59",
    ]

    cols = ["id", "nome_unidade"]
    for raio in ["1km", "2km", "3km"]:
        for m in metricas:
            cols.append(f"{raio}_{m}")

    lojas = raw.iloc[2:16].copy()
    lojas.columns = cols

    lojas["id"] = pd.to_numeric(lojas["id"], errors="coerce")
    lojas = lojas.dropna(subset=["id"]).copy()
    lojas["id"] = lojas["id"].astype(int)

    for c in lojas.columns:
        if c not in ["id", "nome_unidade"]:
            lojas[c] = pd.to_numeric(lojas[c], errors="coerce")

    base = unidades.merge(lojas, on=["id", "nome_unidade"], how="left")
    return base


# =========================================================
# PREPARO
# =========================================================
def calcular_publico_20_59(df, raio):
    cols = [
        f"{raio}_H_20_24",
        f"{raio}_H_25_29",
        f"{raio}_H_30_39",
        f"{raio}_H_40_49",
        f"{raio}_H_50_59",
        f"{raio}_M_20_24",
        f"{raio}_M_25_29",
        f"{raio}_M_30_39",
        f"{raio}_M_40_49",
        f"{raio}_M_50_59",
    ]
    return df[cols].sum(axis=1)


def preparar_variaveis(df, raio, usar_taxa_manual=False, taxa_tenis=0.03):
    out = df.copy()

    out["publico_20_59"] = calcular_publico_20_59(out, raio)
    out["renda_media"] = out[f"{raio}_Renda_media"]
    out["populacao"] = out[f"{raio}_Populacao"]
    out["domicilios"] = out[f"{raio}_Domicilios"]
    out["praticam_esporte"] = out[f"{raio}_Praticam_Esporte"]

    if usar_taxa_manual:
        out["praticam_tenis"] = out["populacao"] * taxa_tenis
    else:
        out["praticam_tenis"] = out[f"{raio}_Praticam_Tenis"]

    out["penetracao_tenis"] = np.where(
        out["populacao"] > 0, out["praticam_tenis"] / out["populacao"], np.nan
    )

    raio_km = {"1km": 1, "2km": 2, "3km": 3}.get(raio, 2)
    area_km2 = np.pi * (raio_km ** 2)

    out["densidade_demografica"] = np.where(
        area_km2 > 0,
        out["populacao"] / area_km2,
        np.nan
    )

    cols_h = [
        f"{raio}_H_20_24",
        f"{raio}_H_25_29",
        f"{raio}_H_30_39",
        f"{raio}_H_40_49",
        f"{raio}_H_50_59",
    ]
    cols_m = [
        f"{raio}_M_20_24",
        f"{raio}_M_25_29",
        f"{raio}_M_30_39",
        f"{raio}_M_40_49",
        f"{raio}_M_50_59",
    ]

    out["homens_20_59"] = out[cols_h].sum(axis=1)
    out["mulheres_20_59"] = out[cols_m].sum(axis=1)

    out["share_homens_20_59"] = np.where(
        out["publico_20_59"] > 0, out["homens_20_59"] / out["publico_20_59"], np.nan
    )
    out["share_mulheres_20_59"] = np.where(
        out["publico_20_59"] > 0, out["mulheres_20_59"] / out["publico_20_59"], np.nan
    )

    return out


def filtro_sp_capital(df):
    if "endereco" in df.columns:
        mask = df["endereco"].astype(str).str.contains("São Paulo", case=False, na=False)
        if mask.sum() >= 3:
            return df[mask].copy()

    lat_min, lat_max = -23.80, -23.35
    lon_min, lon_max = -46.85, -46.35
    mask = (
        df["latitude"].between(lat_min, lat_max)
        & df["longitude"].between(lon_min, lon_max)
    )
    return df[mask].copy() if mask.sum() >= 3 else df.copy()


# =========================================================
# FORMATAÇÃO
# =========================================================
def fmt_int(v):
    if pd.isna(v):
        return "-"
    return f"{int(round(v)):,}".replace(",", ".")


def fmt_money(v):
    if pd.isna(v):
        return "-"
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_pct(v):
    if pd.isna(v):
        return "-"
    return f"{100*v:.1f}%"


def valor_formatado(col, valor):
    if "penetracao" in col or "share_" in col:
        return fmt_pct(valor)
    if "renda" in col:
        return fmt_money(valor)
    return fmt_int(valor)


def raio_para_metros(raio_txt):
    return {"1km": 1000, "2km": 2000, "3km": 3000}.get(raio_txt, 2000)


def compara_media_generica(valor, media, tipo="int"):
    if pd.isna(valor) or pd.isna(media) or media == 0:
        return "Sem comparação disponível"
    diff = ((valor / media) - 1) * 100
    media_fmt = fmt_money(media) if tipo == "money" else fmt_int(media)
    if diff > 0:
        return f"{abs(diff):.1f}% acima da média geral ({media_fmt})"
    elif diff < 0:
        return f"{abs(diff):.1f}% abaixo da média geral ({media_fmt})"
    return f"Em linha com a média geral ({media_fmt})"


def compara_total_parte(valor, total):
    if pd.isna(valor) or pd.isna(total) or total == 0:
        return "Sem comparação disponível"
    share = (valor / total) * 100
    return f"Representa {share:.1f}% do total geral ({fmt_int(total)})"


# =========================================================
# CSS / UI
# =========================================================
def css_global():
    st.markdown(
        """
        <style>
        .cardx{
            border-radius:18px;
            padding:18px 18px 14px 18px;
            box-shadow:0 6px 18px rgba(0,0,0,0.08);
            border:1px solid rgba(0,0,0,0.05);
            background:white;
            min-height:150px;
        }
        .cardx-title{
            font-size:0.95rem;
            color:#5f6368;
            margin-bottom:10px;
        }
        .cardx-value{
            font-size:1.85rem;
            font-weight:700;
            line-height:1.05;
        }
        .cardx-sub{
            margin-top:8px;
            color:#757575;
            font-size:0.82rem;
            line-height:1.45;
        }
        .green-bg{background:linear-gradient(135deg,#e5f5e7 0%,#f8fff8 100%);}
        .sport-bg{background:linear-gradient(135deg,#edf7dd 0%,#fbfff4 100%);}
        .tennis-bg{background:linear-gradient(135deg,#fff2cc 0%,#fffdf1 100%);}
        .yellow-bg{background:linear-gradient(135deg,#fff8dc 0%,#fffef7 100%);}
        .green-tx{color:#1f7a3e;}
        .dark-tx{color:#2e2e2e;}
        .olive-tx{color:#6b6f00;}
        .insight-card{
            border-radius:18px;
            padding:16px;
            border:1px solid rgba(0,0,0,0.06);
            background:#ffffff;
            box-shadow:0 4px 14px rgba(0,0,0,0.06);
            margin-bottom:12px;
        }
        .insight-title{
            font-size:1rem;
            font-weight:700;
            margin-bottom:8px;
            color:#1f2a44;
        }
        .insight-unit{
            font-size:1.08rem;
            font-weight:700;
            color:#1f2a44;
            margin-bottom:6px;
        }
        .insight-score{
            font-size:1.5rem;
            font-weight:700;
            margin-bottom:8px;
        }
        .insight-meta{
            font-size:0.88rem;
            color:#6b7280;
            line-height:1.45;
        }
        .badge{
            display:inline-block;
            padding:5px 10px;
            border-radius:999px;
            background:#eef5ff;
            color:#24406a;
            font-size:0.8rem;
            margin:4px 6px 0 0;
            border:1px solid #d4e2ff;
        }
        .cluster-card{
            border-left:6px solid #1f7a3e;
            border-radius:12px;
            padding:14px 16px;
            background:#fbfcff;
            border-top:1px solid rgba(0,0,0,0.05);
            border-right:1px solid rgba(0,0,0,0.05);
            border-bottom:1px solid rgba(0,0,0,0.05);
            margin-bottom:10px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_card_html(title, value, subtitle, bg_class, value_class):
    return f"""
    <div class="cardx {bg_class}">
        <div class="cardx-title">{title}</div>
        <div class="cardx-value {value_class}">{value}</div>
        <div class="cardx-sub">{subtitle}</div>
    </div>
    """


def render_cards(selected_row, df_geral):
    renda_media_geral = df_geral["renda_media"].mean()
    densidade_media_geral = df_geral["densidade_demografica"].mean()
    esporte_total = df_geral["praticam_esporte"].sum()
    tenis_total = df_geral["praticam_tenis"].sum()

    subt_renda = compara_media_generica(selected_row["renda_media"], renda_media_geral, tipo="money")
    subt_dens = compara_media_generica(selected_row["densidade_demografica"], densidade_media_geral, tipo="int")
    subt_esporte = compara_total_parte(selected_row["praticam_esporte"], esporte_total)
    subt_tenis = compara_total_parte(selected_row["praticam_tenis"], tenis_total)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            render_card_html(
                "Renda média do entorno",
                fmt_money(selected_row["renda_media"]),
                subt_renda,
                "green-bg",
                "green-tx",
            ),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            render_card_html(
                "Densidade demográfica",
                fmt_int(selected_row["densidade_demografica"]),
                subt_dens,
                "yellow-bg",
                "dark-tx",
            ),
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            render_card_html(
                "Praticam esporte",
                fmt_int(selected_row["praticam_esporte"]),
                subt_esporte,
                "sport-bg",
                "dark-tx",
            ),
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            render_card_html(
                "Praticam tênis",
                fmt_int(selected_row["praticam_tenis"]),
                subt_tenis,
                "tennis-bg",
                "olive-tx",
            ),
            unsafe_allow_html=True,
        )


# =========================================================
# SIMILARIDADE / CLUSTERS (AGORA VIA DENDROGRAMA)
# =========================================================
def calcular_clusters_e_similaridade(df, feature_cols, n_clusters):
    out = df.copy()

    base = out[feature_cols].copy()
    base = base.fillna(base.median(numeric_only=True))

    scaler = StandardScaler()
    X = scaler.fit_transform(base)
    X_df = pd.DataFrame(X, index=out["nome_unidade"], columns=feature_cols)

    dist_matrix = pairwise_distances(X_df.values, metric="euclidean")
    sim_matrix = 1 / (1 + dist_matrix)

    sim_df = pd.DataFrame(
        sim_matrix,
        index=out["nome_unidade"].tolist(),
        columns=out["nome_unidade"].tolist(),
    )

    linkage_matrix = linkage(X_df.values, method="ward") if len(out) >= 2 else None

    if linkage_matrix is not None and len(out) >= 2:
        out["cluster_sim"] = fcluster(linkage_matrix, t=n_clusters, criterion="maxclust") - 1
    else:
        out["cluster_sim"] = 0

    return out, sim_df, X_df, linkage_matrix


def cluster_summary_cards(df_clustered, feature_labels):
    resumo = (
        df_clustered.groupby("cluster_sim")
        .agg(
            unidades=("nome_unidade", lambda x: list(x)),
            renda_media=("renda_media", "mean"),
            densidade_demografica=("densidade_demografica", "mean"),
            praticam_esporte=("praticam_esporte", "mean"),
            praticam_tenis=("praticam_tenis", "mean"),
            publico_20_59=("publico_20_59", "mean"),
        )
        .reset_index()
    )

    med_renda = resumo["renda_media"].median()
    med_dens = resumo["densidade_demografica"].median()
    med_tenis = resumo["praticam_tenis"].median()

    st.markdown("### Leitura por grupos")
    for _, row in resumo.iterrows():
        leituras = []
        leituras.append("entorno mais rico" if row["renda_media"] >= med_renda else "entorno menos rico")
        leituras.append("maior densidade" if row["densidade_demografica"] >= med_dens else "menor densidade")
        leituras.append("maior aderência ao tênis" if row["praticam_tenis"] >= med_tenis else "menor aderência ao tênis")

        html = f"""
        <div class="cluster-card">
            <div class="insight-title">Grupo {int(row['cluster_sim'])}</div>
            <div><b>Unidades:</b> {' | '.join(row['unidades'])}</div>
            <div style="margin-top:8px;"><b>Leitura:</b> {', '.join(leituras)}</div>
            <div style="margin-top:8px;">
                <span class="badge">Renda média: {fmt_money(row['renda_media'])}</span>
                <span class="badge">Densidade: {fmt_int(row['densidade_demografica'])}</span>
                <span class="badge">Praticam esporte: {fmt_int(row['praticam_esporte'])}</span>
                <span class="badge">Praticam tênis: {fmt_int(row['praticam_tenis'])}</span>
            </div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


def feature_contributions(unit_a, unit_b, X_df, feature_labels):
    vec_a = X_df.loc[unit_a]
    vec_b = X_df.loc[unit_b]
    diffs = (vec_a - vec_b).abs()

    raw = 1 / (1 + diffs)
    shares = raw / raw.sum()

    contrib = pd.DataFrame(
        {
            "feature": raw.index,
            "similarity_component": raw.values,
            "share": shares.values,
            "diff": diffs.values,
        }
    ).sort_values("share", ascending=False)

    contrib["label"] = contrib["feature"].map(feature_labels)
    return contrib


def render_similarity_card(title, unit_name, similarity_value, contrib_df, color="#1a9850"):
    top_feats = contrib_df.head(3)["label"].tolist()
    motors = " | ".join(top_feats)

    html = f"""
    <div class="insight-card">
        <div class="insight-title">{title}</div>
        <div class="insight-unit">{unit_name}</div>
        <div class="insight-score" style="color:{color};">{similarity_value:.1%}</div>
        <div class="insight-meta"><b>Motores da semelhança:</b> {motors}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# =========================================================
# EXPORTAÇÃO
# =========================================================
def gerar_excel_estudo(df_export, sim_df_export):
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, sheet_name="dados_estudo", index=False)
        sim_df_export.to_excel(writer, sheet_name="matriz_similaridade")

    output.seek(0)
    return output


# =========================================================
# MAPA
# =========================================================
def criar_popup_html(row, variavel_label, variavel_col):
    html = f"""
    <div style="width:290px;font-family:Arial,sans-serif;">
        <h4 style="margin-bottom:6px;">🎾 {row['nome_unidade']}</h4>
        <p style="margin:2px 0;"><b>{variavel_label}:</b> {valor_formatado(variavel_col, row[variavel_col])}</p>
        <p style="margin:2px 0;"><b>Renda média:</b> {fmt_money(row['renda_media'])}</p>
        <p style="margin:2px 0;"><b>Densidade demográfica:</b> {fmt_int(row['densidade_demografica'])}</p>
        <p style="margin:2px 0;"><b>Praticam esporte:</b> {fmt_int(row['praticam_esporte'])}</p>
        <p style="margin:2px 0;"><b>Praticam tênis:</b> {fmt_int(row['praticam_tenis'])}</p>
        <p style="margin:2px 0;"><b>Público 20–59:</b> {fmt_int(row['publico_20_59'])}</p>
        <p style="margin:2px 0;"><b>Grupo:</b> {row['cluster_sim']}</p>
    </div>
    """
    return html


def montar_mapa(
    df,
    variavel_col,
    variavel_label,
    raio_txt,
    unidade_foco,
    mostrar_logo=True,
    tamanho_logo=42,
):
    df_mapa = df.copy()
    if df_mapa.empty:
        return None

    raio_m = raio_para_metros(raio_txt)

    foco_row = df_mapa[df_mapa["nome_unidade"] == unidade_foco].iloc[0]
    centro_lat = foco_row["latitude"]
    centro_lon = foco_row["longitude"]

    m = folium.Map(
        location=[centro_lat, centro_lon],
        zoom_start=11,
        tiles="CartoDB positron",
    )

    Fullscreen().add_to(m)
    MiniMap(toggle_display=True).add_to(m)
    MeasureControl().add_to(m)

    vmin = float(df_mapa[variavel_col].min())
    vmax = float(df_mapa[variavel_col].max())
    if vmin == vmax:
        vmax = vmin + 1

    colormap = LinearColormap(
        colors=["#d73027", "#f46d43", "#fee08b", "#a6d96a", "#1a9850"],
        vmin=vmin,
        vmax=vmax,
    )
    colormap.caption = f"Escala - {variavel_label}"
    colormap.add_to(m)

    for _, row in df_mapa.iterrows():
        is_foco = row["nome_unidade"] == unidade_foco
        cor = colormap(row[variavel_col]) if pd.notna(row[variavel_col]) else "#999999"
        tooltip_txt = f"{row['nome_unidade']} | {variavel_label}: {valor_formatado(variavel_col, row[variavel_col])}"

        folium.Circle(
            location=[row["latitude"], row["longitude"]],
            radius=raio_m,
            color=cor if not is_foco else "#111111",
            weight=5 if is_foco else 3,
            fill=True,
            fill_color=cor,
            fill_opacity=0.18 if is_foco else 0.12,
            opacity=0.95 if is_foco else 0.85,
            tooltip=tooltip_txt,
        ).add_to(m)

        popup = folium.Popup(criar_popup_html(row, variavel_label, variavel_col), max_width=320)

        if mostrar_logo:
            size = tamanho_logo + 8 if is_foco else tamanho_logo
            if LOGO_PATH.exists():
                icon = CustomIcon(
                    str(LOGO_PATH),
                    icon_size=(size, size),
                    icon_anchor=(size // 2, size // 2),
                )
            else:
                icon = folium.Icon(color="green")

            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=popup,
                tooltip=row["nome_unidade"],
                icon=icon,
            ).add_to(m)
        else:
            folium.CircleMarker(
                location=[row["latitude"], row["longitude"]],
                radius=11 if is_foco else 8,
                color="#111111" if is_foco else cor,
                fill=True,
                fill_color=cor,
                fill_opacity=1,
                weight=3 if is_foco else 2,
                popup=popup,
                tooltip=row["nome_unidade"],
            ).add_to(m)

    return m


# =========================================================
# HELPERS DENDRO / HEATMAP
# =========================================================
def get_dendrogram_color_threshold(linkage_matrix, n_groups):
    if linkage_matrix is None:
        return None

    n_obs = linkage_matrix.shape[0] + 1

    if n_groups <= 1:
        return float(linkage_matrix[-1, 2]) + 1e-9

    if n_groups >= n_obs:
        return max(float(linkage_matrix[0, 2]) - 1e-9, 0)

    lower_idx = n_obs - n_groups - 1
    upper_idx = n_obs - n_groups

    lower_dist = float(linkage_matrix[lower_idx, 2])
    upper_dist = float(linkage_matrix[upper_idx, 2])

    return (lower_dist + upper_dist) / 2


def gerar_escala_discreta_gradiente(n_breaks):
    cmap = LinearSegmentedColormap.from_list(
        "cinza_amarelo_verde",
        ["#d9d9d9", "#f0e68c", "#1a9850"]
    )

    cores = [to_hex(cmap(i / max(n_breaks - 1, 1))) for i in range(n_breaks)]
    breaks = np.linspace(0, 1, n_breaks + 1)

    discrete_scale = []
    for i in range(n_breaks):
        left = breaks[i]
        right = breaks[i + 1]
        color = cores[i]
        discrete_scale.append([left, color])
        discrete_scale.append([right, color])

    return discrete_scale


# =========================================================
# APP
# =========================================================
css_global()

st.title("🎾 Estudo de Mercado")
st.caption("Visão estratégica das unidades PlayTennis para apoiar expansão e leitura comparativa do entorno.")

df_base = carregar_dados(ARQUIVO_XLSX)

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.header("Filtros do estudo")

raio_escolhido = st.sidebar.selectbox("Raio de análise", ["1km", "2km", "3km"], index=1)

usar_taxa_manual = st.sidebar.checkbox("Ajustar manualmente % de praticantes de tênis", value=True)

taxa_manual_pct = st.sidebar.slider(
    "% da população que pratica tênis",
    min_value=0.1,
    max_value=15.0,
    value=1.5,
    step=0.1,
)

focar_sp = st.sidebar.checkbox("Focar em São Paulo capital", value=True)

mostrar_logo = st.sidebar.checkbox("Mostrar logo no mapa", value=True)

tamanho_logo = st.sidebar.slider(
    "Tamanho do logo",
    min_value=20,
    max_value=80,
    value=42,
    step=2,
    disabled=not mostrar_logo,
)

df = preparar_variaveis(
    df_base,
    raio_escolhido,
    usar_taxa_manual=usar_taxa_manual,
    taxa_tenis=taxa_manual_pct / 100.0,
)

if focar_sp:
    df = filtro_sp_capital(df)

feature_options = {
    "Renda média": "renda_media",
    "Densidade demográfica": "densidade_demografica",
    "Público 20–59": "publico_20_59",
    "Homens 20–59 (%)": "share_homens_20_59",
    "Mulheres 20–59 (%)": "share_mulheres_20_59",
    "Praticam esporte": "praticam_esporte",
    "Praticam tênis": "praticam_tenis",
}

selected_feature_labels = st.sidebar.multiselect(
    "Variáveis usadas para similaridade e agrupamento",
    options=list(feature_options.keys()),
    default=[
        "Renda média",
        "Densidade demográfica",
        "Praticam esporte",
    ],
)

if len(selected_feature_labels) < 2:
    st.sidebar.warning("Selecione pelo menos 2 variáveis para a similaridade.")
    selected_feature_labels = [
        "Renda média",
        "Densidade demográfica",
        "Praticam esporte",
    ]

selected_feature_cols = [feature_options[k] for k in selected_feature_labels]
feature_labels_reverse = {v: k for k, v in feature_options.items()}

variaveis_mapa = {
    "Renda média": "renda_media",
    "Praticam esporte": "praticam_esporte",
    "Praticam tênis": "praticam_tenis",
    "Público 20–59 anos": "publico_20_59",
    "Penetração do tênis": "penetracao_tenis",
    "Densidade demográfica": "densidade_demografica",
    "Share homens 20–59": "share_homens_20_59",
    "Share mulheres 20–59": "share_mulheres_20_59",
}

variavel_label = st.sidebar.selectbox("Variável exibida no mapa", list(variaveis_mapa.keys()), index=0)
variavel_col = variaveis_mapa[variavel_label]

n_clusters = st.sidebar.slider(
    "Número de grupos (corte do dendrograma)",
    min_value=2,
    max_value=6,
    value=4,
    step=1,
)

n_breaks_heatmap = st.sidebar.slider(
    "Número de quebras da matriz de similaridade",
    min_value=3,
    max_value=9,
    value=5,
    step=1,
)

df, sim_df, X_df, linkage_matrix = calcular_clusters_e_similaridade(
    df,
    selected_feature_cols,
    n_clusters=n_clusters,
)

# -------------------------
# FILTRO PRINCIPAL ACIMA DOS CARDS
# -------------------------
st.markdown("### Unidade foco")
unidade_foco = st.selectbox(
    "Selecione a unidade para leitura e benchmark",
    sorted(df["nome_unidade"].tolist()),
)
selected_row = df[df["nome_unidade"] == unidade_foco].iloc[0]

render_cards(selected_row, df)

st.divider()

# =========================================================
# MAPA
# =========================================================
st.subheader(f"Mapa estratégico | {variavel_label} | {raio_escolhido}")

mapa = montar_mapa(
    df=df,
    variavel_col=variavel_col,
    variavel_label=variavel_label,
    raio_txt=raio_escolhido,
    unidade_foco=unidade_foco,
    mostrar_logo=mostrar_logo,
    tamanho_logo=tamanho_logo,
)

if mapa is not None:
    st_folium(mapa, width=None, height=720, returned_objects=[])
else:
    st.warning("Não foi possível montar o mapa com os filtros atuais.")

# =========================================================
# GRÁFICO DE DISPERSÃO
# =========================================================
st.markdown("## Relação entre renda média e densidade demográfica")

fig_disp = px.scatter(
    df,
    x="renda_media",
    y="densidade_demografica",
    text="nome_unidade",
    color="praticam_esporte",
    hover_data={
        "nome_unidade": True,
        "renda_media": ":,.0f",
        "densidade_demografica": ":,.0f",
        "praticam_esporte": ":,.0f",
        "praticam_tenis": ":,.0f",
        "cluster_sim": True,
    },
)

fig_disp.update_traces(textposition="top center", marker=dict(size=12))
fig_disp.update_layout(
    height=520,
    xaxis_title="Renda média",
    yaxis_title="Densidade demográfica",
    legend_title="Praticam esporte",
)
st.plotly_chart(fig_disp, use_container_width=True)

# =========================================================
# MAIS / MENOS PARECIDAS
# =========================================================
sim_foco = sim_df.loc[unidade_foco].sort_values(ascending=False).drop(index=unidade_foco)

top_parecidas = sim_foco.head(3)
top_distantes = sim_foco.tail(3).sort_values(ascending=True)

st.markdown("## Similaridade da unidade selecionada")

col_sim1, col_sim2 = st.columns(2)

with col_sim1:
    st.markdown("### Mais parecidas")
    for unit_name, sim_value in top_parecidas.items():
        contrib = feature_contributions(unidade_foco, unit_name, X_df, feature_labels_reverse)
        render_similarity_card(
            title="Unidade-irmã",
            unit_name=unit_name,
            similarity_value=sim_value,
            contrib_df=contrib,
            color="#1a9850",
        )

with col_sim2:
    st.markdown("### Menos parecidas")
    for unit_name, sim_value in top_distantes.items():
        contrib = feature_contributions(unidade_foco, unit_name, X_df, feature_labels_reverse)
        render_similarity_card(
            title="Unidade mais distante",
            unit_name=unit_name,
            similarity_value=sim_value,
            contrib_df=contrib,
            color="#d73027",
        )

st.divider()

# =========================================================
# DOWNLOAD
# =========================================================
excel_estudo = gerar_excel_estudo(df, sim_df)

st.download_button(
    label="⬇️ Baixar planilha do estudo consolidado",
    data=excel_estudo,
    file_name=f"PlayTennis_estudo_mercado_{raio_escolhido}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.divider()

# =========================================================
# MATRIZ AGRUPADA
# =========================================================
st.markdown("## Matriz de similaridade agrupada")

if linkage_matrix is not None and len(sim_df) >= 2:
    order = leaves_list(linkage_matrix)
    ordered_names = sim_df.index[order].tolist()
    sim_clustered = sim_df.loc[ordered_names, ordered_names]

    discrete_scale = gerar_escala_discreta_gradiente(n_breaks_heatmap)

    fig_heat = go.Figure(
        data=go.Heatmap(
            z=sim_clustered.values,
            x=sim_clustered.columns,
            y=sim_clustered.index,
            colorscale=discrete_scale,
            zmin=0,
            zmax=1,
            colorbar=dict(title="Similaridade"),
            hovertemplate="Linha: %{y}<br>Coluna: %{x}<br>Similaridade: %{z:.1%}<extra></extra>",
        )
    )
    fig_heat.update_layout(
        height=650,
        xaxis_title="",
        yaxis_title="",
    )
    st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# =========================================================
# VARIÁVEIS USADAS + DENDROGRAMA
# =========================================================
st.markdown("## Variáveis consideradas no agrupamento")
st.markdown(
    " ".join([f"<span class='badge'>{label}</span>" for label in selected_feature_labels]),
    unsafe_allow_html=True,
)

st.markdown("## Dendrograma das unidades")

if linkage_matrix is not None and len(df) >= 2:
    color_threshold = get_dendrogram_color_threshold(linkage_matrix, n_clusters)

    fig, ax = plt.subplots(figsize=(12, 5))
    dendrogram(
        linkage_matrix,
        labels=df["nome_unidade"].tolist(),
        leaf_rotation=45,
        leaf_font_size=10,
        color_threshold=color_threshold,
        above_threshold_color="#9aa0a6",
        ax=ax,
    )
    ax.set_ylabel("Distância")
    ax.set_xlabel("")
    plt.tight_layout()
    st.pyplot(fig)

st.divider()

# =========================================================
# GRUPOS EM CARDS
# =========================================================
cluster_summary_cards(df, feature_labels_reverse)