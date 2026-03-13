"""
src/data.py
Chargement des donnees macro-financieres pour l'analyse des crises.
Sources : World Bank, FRED (pandas-datareader), yfinance, donnees synthetiques en fallback.
"""

import numpy as np
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

try:
    import yfinance as yf
    YF_OK = True
except ImportError:
    YF_OK = False

try:
    import pandas_datareader.data as web
    PDR_OK = True
except ImportError:
    PDR_OK = False

try:
    import wbdata
    WB_OK = True
except ImportError:
    WB_OK = False


# ── Definition des crises ─────────────────────────────────────────────────────

CRISES = {
    "2008": {
        "label":       "Crise des subprimes (2008)",
        "debut":       "2007-01-01",
        "fin":         "2010-12-31",
        "choc":        "2008-09-15",
        "choc_label":  "Faillite Lehman Brothers",
        "couleur":     "#ef4444",
        "description": (
            "La crise financiere de 2008 trouve son origine dans l'effondrement "
            "du marche des credits hypothecaires a risque aux Etats-Unis. "
            "La faillite de Lehman Brothers le 15 septembre 2008 declenche "
            "une panique mondiale, entrainant la plus grave recession depuis 1929."
        ),
    },
    "euro": {
        "label":       "Crise de la zone euro (2011)",
        "debut":       "2010-01-01",
        "fin":         "2013-12-31",
        "choc":        "2011-07-01",
        "choc_label":  "Pic de la crise souveraine",
        "couleur":     "#f59e0b",
        "description": (
            "La crise de la dette souveraine europeenne expose les fragilites "
            "de l'union monetaire. La Grece, l'Irlande, le Portugal, l'Espagne "
            "et l'Italie subissent des pressions intenses sur leurs taux d'emprunt. "
            "La BCE intervient avec le programme OMT en 2012."
        ),
    },
    "petrole": {
        "label":       "Crise petroliere (2014)",
        "debut":       "2013-01-01",
        "fin":         "2016-12-31",
        "choc":        "2014-06-01",
        "choc_label":  "Effondrement du prix du petrole",
        "couleur":     "#8b5cf6",
        "description": (
            "Entre juin et decembre 2014, le prix du baril de Brent chute de "
            "115 dollars a moins de 60 dollars. Cette correction touche les "
            "economies exportatrices de petrole et provoque des tensions sur "
            "les marches emergents et certains pays de l'OCDE."
        ),
    },
    "covid": {
        "label":       "Crise COVID-19 (2020)",
        "debut":       "2019-01-01",
        "fin":         "2022-12-31",
        "choc":        "2020-03-11",
        "choc_label":  "Declaration pandemie OMS",
        "couleur":     "#10b981",
        "description": (
            "La pandemie de COVID-19 provoque le choc economique le plus brutal "
            "depuis la Seconde Guerre mondiale. Le PIB mondial recule de 3,1% en 2020. "
            "Les gouvernements deploient des plans de relance historiques, "
            "entrainant une explosion de la dette publique dans les pays de l'OCDE."
        ),
    },
}

PAYS_OCDE = {
    "Etats-Unis":    "US",
    "Allemagne":     "DE",
    "France":        "FR",
    "Royaume-Uni":   "GB",
    "Japon":         "JP",
    "Italie":        "IT",
    "Espagne":       "ES",
    "Canada":        "CA",
}

INDICATEURS_WB = {
    "Croissance PIB (%)":       "NY.GDP.MKTP.KD.ZG",
    "Chomage (%)":              "SL.UEM.TOTL.ZS",
    "Inflation (%)":            "FP.CPI.TOTL.ZG",
    "Dette publique / PIB (%)": "GC.DOD.TOTL.GD.ZS",
    "Balance courante / PIB":   "BN.CAB.XOKA.GD.ZS",
}

INDICES_ACTIONS = {
    "S&P 500":  "^GSPC",
    "DAX":      "^GDAXI",
    "CAC 40":   "^FCHI",
    "FTSE 100": "^FTSE",
    "Nikkei":   "^N225",
}

FRED_SERIES = {
    "Taux Fed (%)":         "FEDFUNDS",
    "Spread TED (%)":       "TEDRATE",
    "VIX":                  "VIXCLS",
    "Credit HY spread (%)": "BAMLH0A0HYM2",
    "Taux chomage US (%)":  "UNRATE",
}


# ── Chargement donnees World Bank ─────────────────────────────────────────────

def fetch_macro(pays: list = None, start: int = 2005) -> pd.DataFrame:
    if pays is None:
        pays = list(PAYS_OCDE.values())

    if not WB_OK:
        return _synthetique_macro(pays, start)

    debut = datetime(start, 1, 1)
    fin   = datetime(datetime.now().year, 12, 31)
    rows  = []

    for nom_ind, code_ind in INDICATEURS_WB.items():
        try:
            df = wbdata.get_dataframe(
                {code_ind: nom_ind},
                country=pays,
                date=(debut, fin),
            )
            if df is not None and not df.empty:
                df = df.reset_index()
                df.columns = ["pays", "date", "valeur"]
                df["indicateur"] = nom_ind
                rows.append(df)
        except Exception:
            pass

    if not rows:
        return _synthetique_macro(pays, start)

    df = pd.concat(rows, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df["annee"] = df["date"].dt.year
    return df


# ── Chargement indices boursiers ──────────────────────────────────────────────

def fetch_indices(debut: str = "2005-01-01",
                  fin: str = None) -> pd.DataFrame:
    if fin is None:
        fin = datetime.today().strftime("%Y-%m-%d")

    if not YF_OK:
        return _synthetique_indices(debut, fin)

    frames = {}
    for nom, ticker in INDICES_ACTIONS.items():
        try:
            data = yf.download(ticker, start=debut, end=fin,
                               auto_adjust=True, progress=False, timeout=10)
            if not data.empty:
                close = data["Close"]
                if hasattr(close, "squeeze"):
                    close = close.squeeze()
                frames[nom] = close
        except Exception:
            pass

    if not frames:
        return _synthetique_indices(debut, fin)

    df = pd.DataFrame(frames)
    df.index = pd.to_datetime(df.index)
    return df.ffill().dropna(how="all")


# ── Chargement donnees FRED ───────────────────────────────────────────────────

def fetch_fred(debut: str = "2005-01-01") -> pd.DataFrame:
    if not PDR_OK:
        return _synthetique_fred(debut)

    frames = {}
    for nom, code in FRED_SERIES.items():
        try:
            s = web.DataReader(code, "fred", start=debut,
                               end=datetime.today().strftime("%Y-%m-%d"))
            frames[nom] = s.squeeze()
        except Exception:
            pass

    if not frames:
        return _synthetique_fred(debut)

    df = pd.DataFrame(frames)
    df.index = pd.to_datetime(df.index)
    return df.ffill()


# ── Calcul des indicateurs de crise ──────────────────────────────────────────

def calcul_drawdown(prices: pd.DataFrame) -> pd.DataFrame:
    """Drawdown cumulatif depuis le dernier plus haut."""
    result = pd.DataFrame(index=prices.index, columns=prices.columns)
    for col in prices.columns:
        s = prices[col].dropna()
        rolling_max = s.cummax()
        result[col] = (s - rolling_max) / rolling_max * 100
    return result.astype(float)


def calcul_volatilite(prices: pd.DataFrame, fenetre: int = 21) -> pd.DataFrame:
    """Volatilite annualisee glissante."""
    returns = prices.pct_change()
    return returns.rolling(fenetre).std() * np.sqrt(252) * 100


def calcul_chute_pic(prices: pd.DataFrame,
                     debut_crise: str,
                     fin_crise: str) -> pd.Series:
    """Chute maximale pendant la periode de crise."""
    sub = prices.loc[debut_crise:fin_crise]
    if sub.empty:
        return pd.Series(dtype=float)
    return ((sub.min() - sub.iloc[0]) / sub.iloc[0] * 100).round(2)


def calcul_duree_recuperation(prices: pd.DataFrame,
                               debut_crise: str) -> pd.Series:
    """Nombre de jours pour retrouver le niveau pre-crise."""
    t0 = pd.to_datetime(debut_crise)
    resultats = {}
    for col in prices.columns:
        s = prices[col].dropna()
        if t0 not in s.index:
            idx = s.index.searchsorted(t0)
            if idx >= len(s):
                resultats[col] = None
                continue
            t0_eff = s.index[idx]
        else:
            t0_eff = t0
        niveau_ref = s.loc[t0_eff]
        apres = s.loc[t0_eff:]
        recupere = apres[apres >= niveau_ref]
        if len(recupere) > 1:
            resultats[col] = (recupere.index[1] - t0_eff).days
        else:
            resultats[col] = None
    return pd.Series(resultats)


# ── Donnees synthetiques ──────────────────────────────────────────────────────

def _synthetique_macro(pays: list, start: int) -> pd.DataFrame:
    np.random.seed(42)
    rows = []
    annees = range(start, datetime.now().year + 1)
    chocs = {
        2008: {"Croissance PIB (%)": -4.0, "Chomage (%)": 3.0},
        2009: {"Croissance PIB (%)": -5.0, "Chomage (%)": 4.0},
        2011: {"Croissance PIB (%)": -1.5, "Dette publique / PIB (%)": 15.0},
        2015: {"Inflation (%)": -1.0},
        2020: {"Croissance PIB (%)": -6.0, "Chomage (%)": 2.5,
               "Dette publique / PIB (%)": 20.0},
    }
    bases = {
        "Croissance PIB (%)":       2.0,
        "Chomage (%)":              6.5,
        "Inflation (%)":            2.0,
        "Dette publique / PIB (%)": 65.0,
        "Balance courante / PIB":   0.5,
    }
    for p in pays:
        for a in annees:
            for ind, base in bases.items():
                val = base + np.random.normal(0, base * 0.12)
                if a in chocs and ind in chocs[a]:
                    val += chocs[a][ind] + np.random.normal(0, 0.5)
                rows.append({"pays": p, "date": datetime(a, 12, 31),
                             "annee": a, "valeur": round(val, 2),
                             "indicateur": ind})
    return pd.DataFrame(rows)


def _synthetique_indices(debut: str, fin: str) -> pd.DataFrame:
    np.random.seed(7)
    dates = pd.bdate_range(start=debut, end=fin)
    bases  = {"S&P 500": 1200, "DAX": 5000, "CAC 40": 4000,
              "FTSE 100": 5500, "Nikkei": 11000}
    crises_dates = {
        "2008-09-15": -0.045,
        "2011-08-05": -0.025,
        "2014-10-15": -0.018,
        "2020-03-16": -0.120,
    }
    data = {}
    for nom, base in bases.items():
        prix = [base]
        for i in range(1, len(dates)):
            d_str = dates[i].strftime("%Y-%m-%d")
            choc  = crises_dates.get(d_str, 0)
            ret   = np.random.normal(0.0003, 0.012) + choc
            prix.append(prix[-1] * (1 + ret))
        data[nom] = prix
    return pd.DataFrame(data, index=dates)


def _synthetique_fred(debut: str) -> pd.DataFrame:
    np.random.seed(11)
    dates = pd.date_range(start=debut, end=datetime.today(), freq="MS")
    annees = [d.year for d in dates]

    def serie(base, chocs_annee, bruit=0.1):
        vals = []
        for i, a in enumerate(annees):
            v = base + sum(chocs_annee.get(a, [0]))
            v += np.random.normal(0, bruit)
            vals.append(max(0, v))
        return vals

    data = {
        "Taux Fed (%)":         serie(2.5, {2008: [2], 2009: [-4], 2020: [-1.5], 2022: [3]}),
        "Spread TED (%)":       serie(0.4, {2008: [3.5], 2020: [1.0]}),
        "VIX":                  serie(15,  {2008: [50], 2011: [20], 2020: [65]}, bruit=2),
        "Credit HY spread (%)": serie(4.0, {2008: [12], 2020: [8]}, bruit=0.5),
        "Taux chomage US (%)":  serie(5.0, {2009: [5], 2010: [4], 2020: [10]}, bruit=0.3),
    }
    return pd.DataFrame(data, index=dates)
