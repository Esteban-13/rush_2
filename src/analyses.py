"""Analyses calculees sur les tables nettoyees (src/nettoyage.py).

Chaque fonction prend un Resultat et renvoie un tableau pret a afficher.
Regles communes : periodes incompletes ecartees ; pas de somme entre groupes
(l'unite de l'export n'est pas documentee), d'ou les indices en base 100.
"""
import io

import numpy as np
import pandas as pd

from .nettoyage import JOURS_FR, MOIS_FR, RACINE, lire_csv, mois_annee, nom_court

SENTINELLES = RACINE / "data" / "externe" / "sentinelles_syndromes_grippaux.csv"
SEUIL_PREVISION = 0.8      # "oui" si le modele reduit l'erreur d'au moins 20 %
SEUIL_GRIPPE = 150         # cas pour 100 000 habitants : semaine de forte grippe (notre choix)
SEUIL_ISOLE = 2            # une periode est "isolee" si elle compte 2 unites ou moins
N_TEST = 24


def _jours(r):
    return r.journalier[r.journalier["journee_complete"]]


def _mois(r):
    """Mois complets consecutifs les plus recents (serie sans trou)."""
    m = r.mensuel[r.mensuel["mois_complet"]].set_index("date_fin_mois").sort_index()[r.groupes]
    rang = m.index.year * 12 + m.index.month
    debut = 0
    for i in range(1, len(m)):
        if rang[i] - rang[i - 1] != 1:
            debut = i
    return m.iloc[debut:]


# ------------------------------------------------------------------ statistiques
def resume(r):
    d = _jours(r)[r.groupes]
    t = pd.DataFrame({"Moyenne par jour": d.mean(), "Médiane par jour": d.median(),
                      "Jours sans vente (%)": 100 * (d == 0).mean(),
                      "Régularité (coef. de variation)": d.std() / d.mean().replace(0, np.nan),
                      "Besoin 1 jour sur 20": d.quantile(0.95)})
    t.index.name = "Groupe"
    return t


def indice_jour(r):
    d = _jours(r)
    t = 100 * d.groupby("jour_semaine")[r.groupes].mean().reindex(JOURS_FR) / d[r.groupes].mean()
    return t.T


def part_heure(r):
    h = r.horaire[r.horaire["heure_ouverture"] & r.horaire["journee_complete"]]
    par_heure = h.groupby("heure")[r.groupes].mean()
    return (100 * par_heure / par_heure.sum()).T


def indice_mois(r):
    m = r.mensuel[r.mensuel["mois_complet"]]
    par_mois = m.groupby(m["date_fin_mois"].dt.month)[r.groupes].mean().reindex(range(1, 13))
    t = 100 * par_mois / par_mois.mean()
    t.index = [MOIS_FR[i - 1] for i in t.index]
    return t.T


def annuel(r):
    """Total par annee complete et evolution entre la premiere et la derniere."""
    d = r.journalier
    par_an = d.groupby("annee")["journee_complete"].agg(["sum", "size"])
    attendu = pd.Series({a: 366 if pd.Timestamp(a, 12, 31).is_leap_year else 365 for a in par_an.index})
    completes = par_an.index[(par_an["sum"] == attendu).values]
    if len(completes) < 2:
        return None
    t = d[d["annee"].isin(completes)].groupby("annee")[r.groupes].sum().T
    premier, dernier = completes[0], completes[-1]
    t[f"Évolution {premier}-{dernier} (%)"] = 100 * (t[dernier] / t[premier].replace(0, np.nan) - 1)
    t.columns = [str(c) for c in t.columns]
    return t


def selection(r, groupes, debut, fin):
    """Ventes des groupes choisis entre deux dates (incluses)."""
    d = r.journalier
    return d[(d["date"] >= pd.Timestamp(debut)) & (d["date"] <= pd.Timestamp(fin))][["date", "journee_complete", *groupes]]


# -------------------------------------------------------------------- prevision
def holt_winters(serie, tendance=True):
    """Lissage exponentiel saisonnier (Holt-Winters additif, tendance amortie), en numpy.
    Reglages choisis sur la serie fournie uniquement. Renvoie la prevision du mois suivant."""
    x = np.asarray(serie, dtype=float)
    n, p = len(x), 12
    alpha, beta, gamma, phi = [a.ravel() for a in np.meshgrid(
        [0.05, 0.15, 0.3, 0.5, 0.7, 0.9],
        [0.0, 0.1, 0.3, 0.6] if tendance else [0.0],
        [0.0, 0.25, 0.5, 0.75, 1.0],
        [0.8, 0.9, 0.98] if tendance else [0.0])]
    niveau = np.full(alpha.shape, x[:p].mean())
    pente = np.full(alpha.shape, (x[p:2 * p].mean() - x[:p].mean()) / p if tendance else 0.0)
    saison = [np.full(alpha.shape, v - x[:p].mean()) for v in x[:p]]
    sse = np.zeros(alpha.shape)
    for t in range(p, n):
        e = x[t] - (niveau + phi * pente + saison[t - p])
        sse += e ** 2
        niveau = niveau + phi * pente + alpha * e
        pente = phi * pente + alpha * beta * e
        saison.append(saison[t - p] + gamma * (1 - alpha) * e)
    k = np.argmin(sse)
    return max(0.0, float(niveau[k] + phi[k] * pente[k] + saison[n - p][k]))


def prevision(r):
    """Test glissant sur les derniers mois complets. Renvoie (verdict, infos) ou (None, raison)."""
    y = _mois(r)
    n_test = min(N_TEST, len(y) - 36)
    if n_test < 6:
        return None, (f"Il faut au moins 42 mois complets consécutifs pour tester une prévision ; "
                      f"les exports en contiennent {len(y)}.")
    lignes = []
    for i in range(len(y) - n_test, len(y)):
        for g in r.groupes:
            passe = y[g].iloc[:i].to_numpy()
            lignes.append({"groupe": g, "reel": y[g].iloc[i], "naif_dernier": passe[-1],
                           "naif_annee": passe[-12], "modele": holt_winters(passe)})
    test = pd.DataFrame(lignes)
    ecart = pd.DataFrame({k: (test[k] - test["reel"]).abs() for k in ["naif_dernier", "naif_annee", "modele"]})
    mae = ecart.groupby(test["groupe"]).mean().loc[r.groupes]
    ref = mae[["naif_dernier", "naif_annee"]].min(axis=1)
    v = pd.DataFrame({"Ventes moyennes par mois": test.groupby("groupe")["reel"].mean().loc[r.groupes],
                      "Erreur du modèle": mae["modele"], "Erreur de la référence simple": ref})
    v["Rapport"] = v["Erreur du modèle"] / ref.replace(0, np.nan)
    v["Prévisible ?"] = np.where(v["Rapport"] <= SEUIL_PREVISION, "Oui", "Non")
    v["Prévision"] = [holt_winters(y[g].to_numpy()) for g in r.groupes]
    v.index.name = "Groupe"
    prochain = y.index[-1] + pd.offsets.MonthEnd(1)
    return v, {"prochain": mois_annee(prochain), "dernier": mois_annee(y.index[-1]), "n_test": n_test, "n_mois": len(y)}


# ----------------------------------------------------------------- donnee externe
def lire_sentinelles(contenu=None):
    """Incidence hebdomadaire des syndromes grippaux (reseau Sentinelles). None si indisponible."""
    try:
        if contenu is None:
            if not SENTINELLES.exists():
                return None
            contenu = SENTINELLES.read_bytes()
        s = pd.read_csv(io.BytesIO(contenu), comment="#", encoding="latin-1")
        s["date_fin_semaine"] = pd.to_datetime(s["week"].astype(str) + "7", format="%G%V%u")
        s["grippe"] = pd.to_numeric(s["inc100"], errors="coerce")
        return s[["date_fin_semaine", "grippe"]].dropna()
    except Exception:
        return None


def grippe(r, sentinelles):
    """Ventes en semaine de forte grippe contre semaine normale. Renvoie (tableau, series) ou None."""
    if sentinelles is None:
        return None
    w = r.hebdo[r.hebdo["semaine_complete"]].merge(sentinelles, on="date_fin_semaine", how="inner")
    forte = w["grippe"] >= SEUIL_GRIPPE
    if len(w) < 52 or forte.sum() < 5 or (~forte).sum() < 5:
        return None
    t = pd.DataFrame({"Semaine normale": w.loc[~forte, r.groupes].mean(),
                      "Semaine de forte grippe": w.loc[forte, r.groupes].mean(),
                      "Corrélation": w[r.groupes].corrwith(w["grippe"])})
    t["Écart (%)"] = 100 * (t["Semaine de forte grippe"] / t["Semaine normale"].replace(0, np.nan) - 1)
    t.index.name = "Groupe"
    return t, w, int(forte.sum())


# ------------------------------------------------------------ partage des donnees
def ventes_isolees(r, groupes):
    """Part des periodes avec vente qui comptent SEUIL_ISOLE unites ou moins, par niveau de detail."""
    niveaux = {
        "Heure": r.horaire[r.horaire["heure_ouverture"] & r.horaire["journee_complete"]],
        "Jour": _jours(r),
        "Semaine": r.hebdo[r.hebdo["semaine_complete"]],
        "Mois": r.mensuel[r.mensuel["mois_complet"]],
    }
    lignes = []
    for niveau, df in niveaux.items():
        for g in groupes:
            ventes = df[g][df[g] > 0]
            lignes.append({"Niveau": niveau, "Groupe": nom_court(g),
                           "Part (%)": 100 * (ventes <= SEUIL_ISOLE).mean() if len(ventes) else 0.0})
    return pd.DataFrame(lignes)


# ------------------------------------------------------------------ export Excel
def classeur(r, tables):
    """Classeur Excel des statistiques (octets). tables : {nom de feuille: DataFrame}."""
    tampon = io.BytesIO()
    with pd.ExcelWriter(tampon, engine="xlsxwriter") as ecrivain:
        for nom, df in tables.items():
            if df is None:
                continue
            df.to_excel(ecrivain, sheet_name=nom[:31], index=df.index.name is not None)
            feuille = ecrivain.sheets[nom[:31]]
            feuille.set_column(0, 0, 34)
            feuille.set_column(1, max(1, len(df.columns)), 16)
    return tampon.getvalue()
