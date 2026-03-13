"""
src/charts.py
Fabrique de graphiques Plotly pour l'analyse des crises financieres.
Theme sombre, style professionnel.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

BG       = "#0d1117"
SURFACE  = "#161b22"
SURFACE2 = "#21262d"
BORDER   = "#30363d"
TEXT     = "#e6edf3"
MUTED    = "#7d8590"

PALETTE = [
    "#58a6ff", "#3fb950", "#f78166", "#d2a8ff",
    "#ffa657", "#79c0ff", "#56d364", "#ff7b72",
]

BASE = dict(
    paper_bgcolor=BG,
    plot_bgcolor=SURFACE,
    font=dict(family="Inter, sans-serif", color=TEXT, size=12),
    margin=dict(l=52, r=24, t=40, b=44),
    xaxis=dict(gridcolor=BORDER, linecolor=BORDER,
               zeroline=False, showgrid=True),
    yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
               zeroline=False, showgrid=True),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                borderwidth=1, font=dict(size=11)),
    hoverlabel=dict(bgcolor=SURFACE2, bordercolor=BORDER,
                    font=dict(color=TEXT, size=12)),
)


def _base(fig: go.Figure, titre: str = "", hauteur: int = 400) -> go.Figure:
    layout = dict(BASE)
    layout["title"] = dict(text=titre, font=dict(size=14, color=TEXT),
                           x=0.01, xanchor="left")
    layout["height"] = hauteur
    fig.update_layout(**layout)
    return fig


def _zone_crise(fig: go.Figure, debut: str, fin: str,
                couleur: str, label: str) -> go.Figure:
    fig.add_vrect(
        x0=debut, x1=fin,
        fillcolor=couleur, opacity=0.08,
        layer="below", line_width=0,
    )
    fig.add_vline(
        x=pd.to_datetime(debut).timestamp() * 1000,
        line_dash="dash",
        line_color=couleur, line_width=1,
        annotation_text=label,
        annotation_font=dict(color=couleur, size=10),
        annotation_position="top left",
    )
    return fig


# ── Graphiques indices boursiers ──────────────────────────────────────────────

def ligne_indices(prices: pd.DataFrame,
                  crises: dict,
                  normalise: bool = True,
                  titre: str = "Indices boursiers") -> go.Figure:
    fig = go.Figure()
    df  = prices.copy()
    if normalise:
        df = df.div(df.iloc[0]) * 100

    for i, col in enumerate(df.columns):
        s = df[col].dropna()
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=col,
            mode="lines",
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.8),
            hovertemplate=f"<b>{col}</b><br>%{{x|%d %b %Y}}<br>%{{y:.1f}}<extra></extra>",
        ))

    for crise in crises.values():
        _zone_crise(fig, crise["choc"], crise["fin"],
                    crise["couleur"], crise["choc_label"])

    if normalise:
        fig.add_hline(y=100, line_dash="dot",
                      line_color=MUTED, line_width=1)

    return _base(fig, titre)


def barre_chute(chutes: pd.Series, couleur: str,
                titre: str = "Chute maximale (%)") -> go.Figure:
    chutes_sorted = chutes.sort_values()
    colors = [couleur if v < 0 else "#3fb950" for v in chutes_sorted]
    fig = go.Figure(go.Bar(
        x=chutes_sorted.values,
        y=chutes_sorted.index,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.1f}%" for v in chutes_sorted.values],
        textposition="outside",
        textfont=dict(size=11, color=TEXT),
        hovertemplate="<b>%{y}</b><br>%{x:.2f}%<extra></extra>",
    ))
    fig.add_vline(x=0, line_color=BORDER, line_width=1)
    return _base(fig, titre, hauteur=320)


def area_drawdown(drawdown: pd.DataFrame,
                  crises: dict,
                  titre: str = "Drawdown (%)") -> go.Figure:
    fig = go.Figure()
    for i, col in enumerate(drawdown.columns):
        s = drawdown[col].dropna()
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name=col,
            mode="lines",
            line=dict(color=PALETTE[i % len(PALETTE)], width=1.5),
            fill="tozeroy",
            fillcolor=f"rgba({int(PALETTE[i%len(PALETTE)][1:3],16)},"
                      f"{int(PALETTE[i%len(PALETTE)][3:5],16)},"
                      f"{int(PALETTE[i%len(PALETTE)][5:7],16)},0.08)",
            hovertemplate=f"<b>{col}</b><br>%{{x|%d %b %Y}}<br>%{{y:.1f}}%<extra></extra>",
        ))
    for crise in crises.values():
        _zone_crise(fig, crise["choc"], crise["fin"],
                    crise["couleur"], crise["choc_label"])
    return _base(fig, titre)


def ligne_vix(fred: pd.DataFrame,
              crises: dict,
              titre: str = "VIX et spreads de credit") -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if "VIX" in fred.columns:
        s = fred["VIX"].dropna()
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name="VIX",
            mode="lines",
            line=dict(color=PALETTE[2], width=1.8),
            hovertemplate="<b>VIX</b><br>%{x|%b %Y}<br>%{y:.1f}<extra></extra>",
        ), secondary_y=False)

    if "Credit HY spread (%)" in fred.columns:
        s = fred["Credit HY spread (%)"].dropna()
        fig.add_trace(go.Scatter(
            x=s.index, y=s.values, name="Credit HY spread",
            mode="lines",
            line=dict(color=PALETTE[3], width=1.8),
            hovertemplate="<b>HY Spread</b><br>%{x|%b %Y}<br>%{y:.2f}%<extra></extra>",
        ), secondary_y=True)

    for crise in crises.values():
        fig.add_vrect(x0=crise["choc"], x1=crise["fin"],
                      fillcolor=crise["couleur"], opacity=0.07,
                      layer="below", line_width=0)

    fig.update_layout(**{k: v for k, v in BASE.items()
                          if k not in ("xaxis", "yaxis")})
    fig.update_layout(
        height=400,
        title=dict(text=titre, font=dict(size=14, color=TEXT), x=0.01),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                   title="VIX", zeroline=False),
        yaxis2=dict(gridcolor="rgba(0,0,0,0)", linecolor=BORDER,
                    title="Spread (%)", zeroline=False),
        paper_bgcolor=BG, plot_bgcolor=SURFACE,
    )
    return fig


# ── Graphiques macro ──────────────────────────────────────────────────────────

def ligne_macro(df: pd.DataFrame, indicateur: str,
                pays: list, crises: dict,
                titre: str = "") -> go.Figure:
    sub = df[(df["indicateur"] == indicateur) &
             (df["pays"].isin(pays))].sort_values("annee")
    fig = go.Figure()
    for i, p in enumerate(pays):
        s = sub[sub["pays"] == p]
        fig.add_trace(go.Scatter(
            x=s["annee"], y=s["valeur"],
            name=p, mode="lines+markers",
            line=dict(color=PALETTE[i % len(PALETTE)], width=2),
            marker=dict(size=5),
            hovertemplate=f"<b>{p}</b><br>%{{x}}<br>%{{y:.2f}}<extra></extra>",
        ))
    for crise in crises.values():
        annee_choc = int(crise["choc"][:4])
        fig.add_vline(x=annee_choc, line_dash="dash",
                      line_color=crise["couleur"], line_width=1,
                      annotation_text=crise["choc_label"],
                      annotation_font=dict(color=crise["couleur"], size=9),
                      annotation_position="top left")
    return _base(fig, titre or indicateur)


def barre_macro_comparaison(df: pd.DataFrame, indicateur: str,
                             annees: list,
                             titre: str = "") -> go.Figure:
    sub = df[(df["indicateur"] == indicateur) &
             (df["annee"].isin(annees))].dropna(subset=["valeur"])
    fig = px.bar(
        sub, x="pays", y="valeur", color="annee",
        barmode="group",
        color_discrete_sequence=PALETTE,
        labels={"valeur": indicateur, "pays": "Pays", "annee": "Annee"},
    )
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{y:.2f}<extra></extra>",
    )
    return _base(fig, titre or indicateur)


def radar_crise(df: pd.DataFrame, crise_key: str,
                crises: dict, titre: str = "") -> go.Figure:
    crise  = crises[crise_key]
    annee  = int(crise["choc"][:4])
    annees = [annee - 1, annee, annee + 1]
    inds   = list(df["indicateur"].unique())[:5]
    fig    = go.Figure()

    colors_radar = [MUTED, crise["couleur"], PALETTE[1]]
    for j, a in enumerate(annees):
        sub = df[df["annee"] == a].dropna(subset=["valeur"])
        moyennes = []
        for ind in inds:
            vals = sub[sub["indicateur"] == ind]["valeur"]
            moyennes.append(float(vals.mean()) if len(vals) > 0 else 0)

        colors_muted = ["rgba(125,133,144,0.1)", "rgba(239,68,68,0.1)", "rgba(63,185,80,0.1)"]
        fig.add_trace(go.Scatterpolar(
            r=moyennes + [moyennes[0]],
            theta=inds + [inds[0]],
            name=str(a),
            line=dict(color=colors_radar[j], width=2),
            fill="toself",
            fillcolor=colors_muted[j],
        ))

    fig.update_layout(
        polar=dict(
            bgcolor=SURFACE,
            radialaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                            tickfont=dict(color=MUTED, size=9)),
            angularaxis=dict(gridcolor=BORDER, linecolor=BORDER,
                             tickfont=dict(color=TEXT, size=10)),
        ),
        paper_bgcolor=BG,
        font=dict(color=TEXT),
        height=380,
        title=dict(text=titre or f"Profil macro : {crise['label']}",
                   font=dict(size=14, color=TEXT), x=0.01),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                    font=dict(size=11)),
        margin=dict(l=60, r=60, t=50, b=40),
    )
    return fig


def jauge_impact(valeur: float, label: str,
                 couleur: str = "#58a6ff") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=abs(valeur),
        title=dict(text=label, font=dict(color=TEXT, size=12)),
        number=dict(suffix="%", font=dict(color=TEXT, size=26),
                    valueformat=".1f"),
        gauge=dict(
            axis=dict(range=[0, 15],
                      tickcolor=MUTED,
                      tickfont=dict(color=MUTED, size=9)),
            bar=dict(color=couleur),
            bgcolor=SURFACE2,
            borderwidth=1,
            bordercolor=BORDER,
            steps=[
                dict(range=[0, 3],   color=SURFACE),
                dict(range=[3, 8],   color=SURFACE2),
                dict(range=[8, 15],  color=BORDER),
            ],
        ),
    ))
    fig.update_layout(
        paper_bgcolor=BG,
        font=dict(color=TEXT),
        height=200,
        margin=dict(l=20, r=20, t=40, b=10),
    )
    return fig


def timeline_crises(crises: dict) -> go.Figure:
    fig = go.Figure()
    y_pos = list(range(len(crises)))

    for i, (key, crise) in enumerate(crises.items()):
        debut = pd.to_datetime(crise["debut"])
        fin   = pd.to_datetime(crise["fin"])
        choc  = pd.to_datetime(crise["choc"])

        fig.add_trace(go.Scatter(
            x=[debut, fin],
            y=[i, i],
            mode="lines",
            line=dict(color=crise["couleur"], width=6),
            name=crise["label"],
            hovertemplate=f"<b>{crise['label']}</b><br>"
                          f"Debut : {crise['debut']}<br>"
                          f"Fin : {crise['fin']}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=[choc], y=[i],
            mode="markers",
            marker=dict(color=crise["couleur"], size=12,
                        symbol="diamond",
                        line=dict(color=TEXT, width=1)),
            showlegend=False,
            hovertemplate=f"<b>{crise['choc_label']}</b><br>"
                          f"{crise['choc']}<extra></extra>",
        ))

    fig.update_layout(
        paper_bgcolor=BG,
        plot_bgcolor=SURFACE,
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        hoverlabel=dict(bgcolor=SURFACE2, bordercolor=BORDER,
                        font=dict(color=TEXT, size=12)),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BORDER,
                    font=dict(size=11)),
        height=300,
        title=dict(text="Chronologie des crises (2005-2022)",
                   font=dict(size=14, color=TEXT), x=0.01),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER, zeroline=False,
                   type="date"),
        yaxis=dict(
            gridcolor=BORDER, linecolor=BORDER,
            tickvals=y_pos,
            ticktext=[c["label"] for c in crises.values()],
            tickfont=dict(size=11),
        ),
        showlegend=False,
        margin=dict(l=220, r=24, t=44, b=44),
    )
    return fig
