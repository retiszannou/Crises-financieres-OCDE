# Analyse des Crises Financieres dans les Pays de l'OCDE

Application Streamlit pour l'analyse comparative de quatre episodes de crise majeurs depuis 2005 : la crise des subprimes (2008), la crise de la zone euro (2011), la crise petroliere (2014) et la crise COVID-19 (2020).

---

## Ce que couvre l'application

**Apercu general** : chronologie interactive des crises, fiches descriptives, indicateurs cles.

**Marches financiers** : performance des indices boursiers (S&P 500, DAX, CAC 40, FTSE, Nikkei), drawdown cumulatif, chutes maximales, duree de recuperation, VIX et spreads de credit.

**Indicateurs macro** : croissance du PIB, chomage, inflation, dette publique, balance courante pour 8 pays de l'OCDE. Comparaison avant, pendant et apres chaque crise.

**Analyse par crise** : fiche detaillee, jauges d'impact, radar macro, evolution des indices pendant la periode.

**Comparaison des crises** : tableau des chutes par indice et par crise, impact sur la croissance du PIB, evolution de la dette publique.

---

## Sources de donnees

| Source | Donnees |
|---|---|
| World Bank API | PIB, chomage, inflation, dette (annuel) |
| FRED (St. Louis Fed) | VIX, spreads, taux Fed |
| yfinance | Indices boursiers (quotidien) |

Le mode demonstration (donnees synthetiques) est active automatiquement si une source est indisponible.

---

## Installation

```bash
git clone https://github.com/retiszannou/crises-financieres-ocde.git
cd crises-financieres-ocde
pip install -r requirements.txt
streamlit run app.py
```

---

## Structure

```
crises-financieres/
├── app.py          # Application Streamlit (5 pages)
├── src/
│   ├── data.py     # Chargement donnees et calculs
│   └── charts.py   # Fabrique de graphiques Plotly
└── requirements.txt
```

---

## Reference

Les periodes de crise sont definies selon les chronologies de l'OCDE, du FMI et de la BCE.

> Projet academique. Ne constitue pas un conseil financier.
