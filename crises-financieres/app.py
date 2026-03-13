"""
app.py
Analyse des crises financieres dans les pays de l'OCDE.
Crises analysees : 2008 (subprimes), 2011 (zone euro),
                   2014 (petrole), 2020 (COVID-19).
"""

import sys
import warnings
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

sys.path.insert(0, "src")
warnings.filterwarnings("ignore")

from data import (
    CRISES, PAYS_OCDE, INDICATEURS_WB,
    fetch_macro, fetch_indices, fetch_fred,
    calcul_drawdown, calcul_volatilite,
    calcul_chute_pic, calcul_duree_recuperation,
)
from charts import (
    ligne_indices, barre_chute, area_drawdown,
    ligne_vix, ligne_macro, barre_macro_comparaison,
    radar_crise, jauge_impact, timeline_crises,
    BG, SURFACE, BORDER, TEXT, MUTED, PALETTE,
)

st.set_page_config(
    page_title="Crises financieres OCDE",
    page_icon="📉",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(f"""
<style>
html, body, [class*="css"] {{
    font-family: Inter, system-ui, sans-serif;
    background-color: {BG};
    color: {TEXT};
}}
.metric-box {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 14px 16px;
}}
.metric-label {{
    font-size: 11px;
    font-weight: 600;
    color: {MUTED};
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 4px;
}}
.metric-value {{
    font-size: 22px;
    font-weight: 600;
    color: {TEXT};
    line-height: 1.2;
}}
.tag {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 500;
    margin-right: 6px;
}}
section[data-testid="stSidebar"] {{
    background-color: {SURFACE};
    border-right: 1px solid {BORDER};
}}
</style>
""", unsafe_allow_html=True)


# ── Cache donnees ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def charger_indices():
    return fetch_indices(debut="2005-01-01")

@st.cache_data(ttl=3600)
def charger_macro():
    return fetch_macro(start=2005)

@st.cache_data(ttl=3600)
def charger_fred():
    return fetch_fred(debut="2005-01-01")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(f"## Crises financieres OCDE")
    st.markdown(f"<span style='color:{MUTED};font-size:12px;'>Analyse comparative 2005-2022</span>",
                unsafe_allow_html=True)
    st.divider()

    page = st.radio("Navigation", [
        "Apercu general",
        "Marches financiers",
        "Indicateurs macro",
        "Analyse par crise",
        "Comparaison des crises",
    ], label_visibility="collapsed")

    st.divider()

    crises_select = st.multiselect(
        "Crises affichees",
        options=list(CRISES.keys()),
        default=list(CRISES.keys()),
        format_func=lambda k: CRISES[k]["label"],
    )
    crises_actives = {k: CRISES[k] for k in crises_select}

    pays_select = st.multiselect(
        "Pays",
        options=list(PAYS_OCDE.values()),
        default=list(PAYS_OCDE.values())[:5],
        format_func=lambda v: [k for k, vv in PAYS_OCDE.items() if vv == v][0],
    )

    st.divider()
    st.markdown(f"<span style='color:{MUTED};font-size:11px;'>Sources : World Bank, FRED, yfinance</span>",
                unsafe_allow_html=True)


# ── Chargement ────────────────────────────────────────────────────────────────

with st.spinner("Chargement des donnees..."):
    indices = charger_indices()
    macro   = charger_macro()
    fred    = charger_fred()


# ── Page 1 : Apercu general ───────────────────────────────────────────────────

if page == "Apercu general":
    st.title("Crises financieres dans les pays de l'OCDE")
    st.markdown(
        "Analyse comparative de quatre episodes de crise majeurs depuis 2005. "
        "Les donnees couvrent les marches financiers, les indicateurs macro-economiques "
        "et les indicateurs de risque systemique."
    )

    # Timeline
    st.plotly_chart(timeline_crises(crises_actives),
                    use_container_width=True, config={"displayModeBar": False})

    st.divider()

    # Fiches par crise
    cols = st.columns(len(crises_actives))
    for i, (key, crise) in enumerate(crises_actives.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label" style="color:{crise['couleur']};">
                    {crise['label']}
                </div>
                <div style="font-size:12px; color:{TEXT}; margin-top:8px; line-height:1.6;">
                    {crise['description'][:200]}...
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # KPI globaux
    st.subheader("Indicateurs cles")
    k1, k2, k3, k4 = st.columns(4)

    chutes_2008 = calcul_chute_pic(indices, "2008-09-01", "2009-03-31")
    chute_max_2008 = float(chutes_2008.min()) if len(chutes_2008) > 0 else -50.0

    chutes_covid = calcul_chute_pic(indices, "2020-02-01", "2020-04-30")
    chute_max_covid = float(chutes_covid.min()) if len(chutes_covid) > 0 else -34.0

    k1.metric("Chute max S&P 500 (2008)", f"{chute_max_2008:.1f}%")
    k2.metric("Chute max indices (COVID)", f"{chute_max_covid:.1f}%")

    vix_max = float(fred["VIX"].max()) if "VIX" in fred.columns else 80.0
    k3.metric("VIX maximum observe", f"{vix_max:.0f}")

    dette_moy = macro[
        (macro["indicateur"] == "Dette publique / PIB (%)") &
        (macro["annee"] == 2021)
    ]["valeur"].mean()
    k4.metric("Dette OCDE moy. 2021 / PIB", f"{dette_moy:.0f}%")


# ── Page 2 : Marches financiers ───────────────────────────────────────────────

elif page == "Marches financiers":
    st.title("Marches financiers")

    normalise = st.checkbox("Normaliser a 100 au 01/01/2005", value=True)

    st.plotly_chart(
        ligne_indices(indices, crises_actives, normalise=normalise,
                      titre="Performance des indices boursiers OCDE"),
        use_container_width=True, config={"displayModeBar": False}
    )

    col_a, col_b = st.columns(2)

    with col_a:
        crise_sel = st.selectbox(
            "Crise analysee",
            options=list(crises_actives.keys()),
            format_func=lambda k: CRISES[k]["label"],
        )
        crise = CRISES[crise_sel]
        chutes = calcul_chute_pic(indices, crise["choc"], crise["fin"])
        st.plotly_chart(
            barre_chute(chutes, crise["couleur"],
                        titre=f"Chute maximale : {crise['label']}"),
            use_container_width=True, config={"displayModeBar": False}
        )

    with col_b:
        dd = calcul_drawdown(indices)
        st.plotly_chart(
            area_drawdown(dd, crises_actives,
                          titre="Drawdown cumulatif (%)"),
            use_container_width=True, config={"displayModeBar": False}
        )

    st.divider()
    st.subheader("Indicateurs de risque systemique")
    st.plotly_chart(
        ligne_vix(fred, crises_actives,
                  titre="VIX et spread de credit HY"),
        use_container_width=True, config={"displayModeBar": False}
    )

    # Duree de recuperation
    st.subheader("Duree de recuperation par crise (jours)")
    rec_cols = st.columns(len(crises_actives))
    for i, (key, crise) in enumerate(crises_actives.items()):
        durees = calcul_duree_recuperation(indices, crise["choc"])
        moy = durees.dropna().mean()
        with rec_cols[i]:
            st.markdown(f"""
            <div class="metric-box">
                <div class="metric-label" style="color:{crise['couleur']};">
                    {crise['label'][:25]}
                </div>
                <div class="metric-value">
                    {f"{moy:.0f} j" if not pd.isna(moy) else "N/D"}
                </div>
            </div>
            """, unsafe_allow_html=True)


# ── Page 3 : Indicateurs macro ────────────────────────────────────────────────

elif page == "Indicateurs macro":
    st.title("Indicateurs macro-economiques")

    indicateur = st.selectbox(
        "Indicateur",
        options=list(INDICATEURS_WB.keys()),
    )

    st.plotly_chart(
        ligne_macro(macro, indicateur, pays_select, crises_actives,
                    titre=f"{indicateur} - Pays OCDE selectionnes"),
        use_container_width=True, config={"displayModeBar": False}
    )

    st.subheader("Comparaison avant / pendant / apres les crises")
    annees_comp = st.multiselect(
        "Annees comparees",
        options=sorted(macro["annee"].unique().tolist()),
        default=[2007, 2009, 2010, 2019, 2020, 2021],
    )
    if annees_comp:
        st.plotly_chart(
            barre_macro_comparaison(
                macro[macro["pays"].isin(pays_select)],
                indicateur, annees_comp,
                titre=f"{indicateur} par pays et par annee",
            ),
            use_container_width=True, config={"displayModeBar": False}
        )

    # Table de synthese
    st.subheader("Table de synthese")
    pivot = macro[
        (macro["indicateur"] == indicateur) &
        (macro["pays"].isin(pays_select))
    ].pivot(index="pays", columns="annee", values="valeur")

    if not pivot.empty:
        st.dataframe(
            pivot.style.format("{:.2f}", na_rep="N/D")
                       .background_gradient(cmap="RdYlGn", axis=None),
            use_container_width=True,
        )


# ── Page 4 : Analyse par crise ────────────────────────────────────────────────

elif page == "Analyse par crise":
    st.title("Analyse detaillee par crise")

    crise_key = st.selectbox(
        "Choisir une crise",
        options=list(CRISES.keys()),
        format_func=lambda k: CRISES[k]["label"],
    )
    crise = CRISES[crise_key]

    st.markdown(f"""
    <div style="border-left: 3px solid {crise['couleur']};
                padding: 12px 16px;
                background: {SURFACE};
                border-radius: 0 8px 8px 0;
                margin-bottom: 16px;">
        <div style="font-size:15px; font-weight:600; color:{crise['couleur']}; margin-bottom:6px;">
            {crise['label']}
        </div>
        <div style="font-size:13px; color:{TEXT}; line-height:1.7;">
            {crise['description']}
        </div>
        <div style="margin-top:10px; font-size:11px; color:{MUTED};">
            Periode : {crise['debut']} - {crise['fin']} |
            Evenement declencheur : {crise['choc_label']} ({crise['choc'][:7]})
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        chutes = calcul_chute_pic(indices, crise["choc"], crise["fin"])
        chute_sp500 = float(chutes.get("S&P 500", -5.0))
        st.plotly_chart(
            jauge_impact(chute_sp500, f"Chute S&P 500 (%)", crise["couleur"]),
            use_container_width=True, config={"displayModeBar": False}
        )

    with col2:
        chute_dax = float(chutes.get("DAX", -5.0))
        st.plotly_chart(
            jauge_impact(chute_dax, f"Chute DAX (%)", crise["couleur"]),
            use_container_width=True, config={"displayModeBar": False}
        )

    st.plotly_chart(
        radar_crise(macro, crise_key, CRISES,
                    titre=f"Profil macro OCDE : {crise['label']}"),
        use_container_width=True, config={"displayModeBar": False}
    )

    # Indices pendant la crise
    mask = (indices.index >= crise["debut"]) & (indices.index <= crise["fin"])
    indices_crise = indices.loc[mask]
    crises_single = {crise_key: crise}
    st.plotly_chart(
        ligne_indices(indices_crise, crises_single, normalise=True,
                      titre=f"Indices boursiers : {crise['label']}"),
        use_container_width=True, config={"displayModeBar": False}
    )


# ── Page 5 : Comparaison des crises ──────────────────────────────────────────

elif page == "Comparaison des crises":
    st.title("Comparaison des crises")

    st.subheader("Chutes maximales des indices par crise")
    comp_data = []
    for key, crise in crises_actives.items():
        chutes = calcul_chute_pic(indices, crise["choc"], crise["fin"])
        for indice, val in chutes.items():
            comp_data.append({
                "Crise":   crise["label"],
                "Indice":  indice,
                "Chute (%)": round(float(val), 2),
            })

    if comp_data:
        df_comp = pd.DataFrame(comp_data)
        pivot_comp = df_comp.pivot(index="Indice",
                                   columns="Crise",
                                   values="Chute (%)").fillna(0)
        st.dataframe(
            pivot_comp.style.format("{:.1f}%")
                            .background_gradient(cmap="RdYlGn_r", axis=None),
            use_container_width=True,
        )

    st.divider()
    st.subheader("Impact macro par crise : croissance du PIB")

    annees_par_crise = {
        "2008":   [2007, 2008, 2009, 2010],
        "euro":   [2010, 2011, 2012, 2013],
        "petrole":[2013, 2014, 2015, 2016],
        "covid":  [2019, 2020, 2021, 2022],
    }

    pib_rows = []
    for key, crise in crises_actives.items():
        annees = annees_par_crise.get(key, [])
        sub = macro[
            (macro["indicateur"] == "Croissance PIB (%)") &
            (macro["annee"].isin(annees))
        ]
        moy = sub.groupby("annee")["valeur"].mean().reset_index()
        moy["crise"] = crise["label"]
        pib_rows.append(moy)

    if pib_rows:
        df_pib = pd.concat(pib_rows, ignore_index=True)
        fig_pib = go.Figure()
        for i, (key, crise) in enumerate(crises_actives.items()):
            sub = df_pib[df_pib["crise"] == crise["label"]]
            fig_pib.add_trace(go.Bar(
                x=sub["annee"].astype(str),
                y=sub["valeur"],
                name=crise["label"],
                marker_color=crise["couleur"],
                hovertemplate="<b>%{x}</b><br>PIB : %{y:.2f}%<extra></extra>",
            ))
        fig_pib.add_hline(y=0, line_color=BORDER, line_width=1)
        fig_pib.update_layout(
            **{k: v for k, v in {
                "paper_bgcolor": BG,
                "plot_bgcolor": SURFACE,
                "font": dict(family="Inter, sans-serif", color=TEXT, size=12),
                "margin": dict(l=52, r=24, t=40, b=44),
                "xaxis": dict(gridcolor=BORDER, linecolor=BORDER),
                "yaxis": dict(gridcolor=BORDER, linecolor=BORDER),
                "legend": dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                               borderwidth=1),
                "barmode": "group",
                "height": 400,
                "title": dict(text="Croissance du PIB OCDE par crise (%)",
                              font=dict(size=14, color=TEXT), x=0.01),
            }.items()},
        )
        st.plotly_chart(fig_pib, use_container_width=True,
                        config={"displayModeBar": False})

    st.divider()
    st.subheader("Tableau de bord de la dette publique")
    st.plotly_chart(
        ligne_macro(macro, "Dette publique / PIB (%)",
                    pays_select, crises_actives,
                    titre="Evolution de la dette publique / PIB (%)"),
        use_container_width=True, config={"displayModeBar": False}
    )
