"""Genere classeur_pharmacie.xlsx a partir des exports nettoyes (data/clean/).

Usage :  python classeur.py
A relancer apres chaque mise a jour des exports (et de nettoyage.py) : toutes les
statistiques du classeur sont recalculees ici, rien n'est saisi a la main.
"""
import os
import re

import numpy as np
import pandas as pd

CLEAN = "data/clean"
EXTERNE = "data/externe/sentinelles_syndromes_grippaux.csv"   # facultatif (etape 3)
SORTIE = "classeur_pharmacie.xlsx"

MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
        "août", "septembre", "octobre", "novembre", "décembre"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def lire(nom, **kw):
    return pd.read_csv(f"{CLEAN}/{nom}", encoding="utf-8-sig", **kw)


# ------------------------------------------------------------------ 1. donnees
d_tout = lire("ventes_journalier.csv", parse_dates=["date"])
groupes = [c for c in d_tout.columns if c.endswith(")")]          # les 8 colonnes "Nom (code)"
d = d_tout[d_tout["journee_complete"]]                            # on ecarte les 2 journees tronquees

h = lire("ventes_horaire.csv", parse_dates=["date"])
h = h[h["heure_ouverture"] & h["date"].dt.normalize().isin(d["date"])]

m = lire("ventes_mensuel.csv", parse_dates=["date_fin_mois"])
m = m[m["mois_complet"]].set_index("date_fin_mois").sort_index()
y = m[groupes]
dernier_mois = y.index[-1]
prochain_mois = dernier_mois + pd.offsets.MonthEnd(1)
nom_prochain = f"{MOIS[prochain_mois.month - 1]} {prochain_mois.year}"
nom_dernier = f"{MOIS[dernier_mois.month - 1]} {dernier_mois.year}"

# ------------------------------------------------------- 2. statistiques descriptives
resume = pd.DataFrame({
    "Total": d[groupes].sum(),
    "Moyenne par jour": d[groupes].mean(),
    "Médiane par jour": d[groupes].median(),
    "Écart-type": d[groupes].std(),
    "Jours sans vente (%)": 100 * (d[groupes] == 0).mean(),
})
resume["Coefficient de variation"] = resume["Écart-type"] / resume["Moyenne par jour"]

par_jour = d.groupby("jour_semaine")[groupes].mean().loc[JOURS]
indice_jour = (100 * par_jour / d[groupes].mean()).T
indice_jour.columns = [j.capitalize() for j in JOURS]

par_heure = h.groupby("heure")[groupes].mean()
part_heure = (100 * par_heure / par_heure.sum()).T
part_heure.columns = [f"{int(c)} h" for c in part_heure.columns]

par_mois = m.groupby(m.index.month)[groupes].mean()
indice_mois = (100 * par_mois / par_mois.mean()).T
indice_mois.columns = [MOIS[i - 1][:4].capitalize() + ("." if len(MOIS[i - 1]) > 4 else "")
                       for i in par_mois.index]

annees = sorted(d.loc[d["annee"].between(2015, 2018), "annee"].unique())
annuel = d[d["annee"].between(2015, 2018)].groupby("annee")[groupes].sum().T
evolution = 100 * (annuel[2018] / annuel[2015] - 1)
annuel.columns = [str(a) for a in annuel.columns]
annuel["Évolution 2015-2018 (%)"] = evolution

# --------------------------------------------------------------- 3. test de prevision
N_TEST = 24
SEUIL = 0.8


def holt_winters(serie, trend="add"):
    """Lissage exponentiel saisonnier (Holt-Winters additif, tendance amortie), en numpy.
    Reglages choisis sur la serie fournie uniquement. Renvoie la prevision du mois suivant."""
    x = np.asarray(serie, dtype=float)
    n, p = len(x), 12
    alpha, beta, gamma, phi = [a.ravel() for a in np.meshgrid(
        [0.05, 0.15, 0.3, 0.5, 0.7, 0.9],
        [0.0, 0.1, 0.3, 0.6] if trend else [0.0],
        [0.0, 0.25, 0.5, 0.75, 1.0],
        [0.8, 0.9, 0.98] if trend else [0.0])]
    niveau = np.full(alpha.shape, x[:p].mean())
    pente = np.full(alpha.shape, (x[p:2 * p].mean() - x[:p].mean()) / p if trend else 0.0)
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


lignes = []
for i in range(len(y) - N_TEST, len(y)):
    for g in groupes:
        passe = y[g].iloc[:i].to_numpy()
        lignes.append({"mois": y.index[i], "groupe": g, "reel": y[g].iloc[i],
                       "naif_dernier": passe[-1], "naif_annee": passe[-12],
                       "modele": holt_winters(passe)})
test = pd.DataFrame(lignes)
ecart = {k: (test[k] - test["reel"]).abs() for k in ["naif_dernier", "naif_annee", "modele"]}
mae = pd.DataFrame(ecart).groupby(test["groupe"]).mean().loc[groupes]
meilleur_naif = mae[["naif_dernier", "naif_annee"]].min(axis=1)
prevision = pd.DataFrame({
    "Ventes moyennes par mois": test.groupby("groupe")["reel"].mean().loc[groupes],
    "Erreur du modèle": mae["modele"],
    "Erreur de la meilleure référence naïve": meilleur_naif,
})
prevision["Rapport (modèle / référence)"] = prevision["Erreur du modèle"] / meilleur_naif
prevision["Erreur relative du modèle (%)"] = 100 * prevision["Erreur du modèle"] / prevision["Ventes moyennes par mois"]
prevision["Prévisible ?"] = np.where(prevision["Rapport (modèle / référence)"] <= SEUIL, "oui", "non")
prevision[f"Prévision {nom_prochain}"] = [
    holt_winters(y[g].to_numpy()) if o == "oui" else np.nan
    for g, o in zip(groupes, prevision["Prévisible ?"])]

# ------------------------------------------------- 4. donnee externe (si presente)
grippe = None
if os.path.exists(EXTERNE):
    s = pd.read_csv(EXTERNE, comment="#", encoding="latin-1")
    s["date_fin_semaine"] = pd.to_datetime(s["week"].astype(str) + "7", format="%G%V%u")
    s["grippe"] = pd.to_numeric(s["inc100"], errors="coerce")
    w = lire("ventes_hebdo.csv", parse_dates=["date_fin_semaine"])
    w = w[w["semaine_complete"]].merge(s[["date_fin_semaine", "grippe"]], on="date_fin_semaine", how="left")
    w["forte_grippe"] = w["grippe"] >= 150
    comp = w.groupby("forte_grippe")[groupes].mean().T
    grippe = pd.DataFrame({
        "Corrélation avec la grippe": w[groupes].corrwith(w["grippe"]),
        "Semaine normale": comp[False],
        "Semaine de forte grippe": comp[True],
    })
    grippe["Écart (%)"] = 100 * (grippe["Semaine de forte grippe"] / grippe["Semaine normale"] - 1)

# ------------------------------------------------------------ 5. fiche et messages
def pic(serie):
    return f"{serie.idxmax()} ({serie.max():.0f})"


def creux(serie):
    return f"{serie.idxmin()} ({serie.min():.0f})"


fiche = pd.DataFrame({
    "Moyenne par jour": resume["Moyenne par jour"],
    "Jour le plus fort (indice)": [pic(indice_jour.loc[g]) for g in groupes],
    "Jour le plus faible (indice)": [creux(indice_jour.loc[g]) for g in groupes],
    "Mois le plus fort (indice)": [pic(indice_mois.loc[g]) for g in groupes],
    "Mois le plus faible (indice)": [creux(indice_mois.loc[g]) for g in groupes],
    "Évolution 2015-2018 (%)": evolution,
    "Prévisible le mois prochain ?": prevision["Prévisible ?"],
    f"Prévision {nom_prochain}": prevision[f"Prévision {nom_prochain}"],
})

oui = [g for g in groupes if prevision.loc[g, "Prévisible ?"] == "oui"]
heures_fortes = part_heure.mean().nlargest(4).index.tolist()
heures_fortes = sorted(heures_fortes, key=lambda t: int(t.split()[0]))
messages = [
    f"Historique du {d_tout['date'].min():%d/%m/%Y} au {d_tout['date'].max():%d/%m/%Y} ; "
    f"dernier mois complet : {nom_dernier}.",
    ("Prévision du mois suivant : le test sur les 24 derniers mois montre qu'elle n'est fiable que pour "
     f"{len(oui)} groupe(s) sur {len(groupes)} : " + ", ".join(oui) + "." if oui else
     "Prévision du mois suivant : aucun groupe ne se prévoit mieux qu'avec la référence naïve."),
    "Heures les plus chargées (moyenne des groupes) : " + ", ".join(heures_fortes) + ".",
]
if grippe is not None:
    lies = grippe[grippe["Corrélation avec la grippe"] >= 0.3].index.tolist()
    messages.append("Les ventes de " + ", ".join(lies) + " augmentent nettement les semaines de forte grippe "
                    "(donnée Sentinelles) : suivre le bulletin hebdomadaire pour anticiper les commandes."
                    if lies else "Aucun groupe n'est nettement lié à la grippe.")
messages.append("Limites : l'unité des quantités n'est pas documentée et l'export ne contient aucun prix. "
                "Les groupes ne se comparent donc pas entre eux en volume, et aucune conclusion n'est donnée en euros.")

# ----------------------------------------------------------- 6. referentiel et etat
ref = pd.DataFrame([re.match(r"^(.*) \((.+)\)$", g).groups() for g in groupes],
                   columns=["Nom du groupe", "Code ATC"])
ref.insert(0, "Libellé dans l'export", groupes)

etat = lire("etat_des_donnees.csv")
etat.columns = ["Fichier", "Constat", "Lignes concernées", "Action"]
usages = pd.DataFrame([
    ["Horaire", "Utilisé", "Répartition des ventes dans la journée (pics et heures creuses)."],
    ["Journalier", "Utilisé (base du classeur)", "Jours de semaine, tendance annuelle, outil de sélection. La somme des heures lui est égale."],
    ["Hebdomadaire", "Utilisé pour contrôle", "La somme des jours lui est égale ; sert aussi à croiser avec la donnée externe."],
    ["Mensuel (client)", "Écarté", "Ne correspond pas à la somme des jours pour une partie des mois. Remplacé par un mensuel reconstruit depuis le journalier, utilisé pour la saisonnalité et la prévision."],
], columns=["Export", "Statut", "Pour quoi faire"])
ecarts = None
if os.path.exists(f"{CLEAN}/ecarts_mensuel_vs_journalier.csv"):
    e = lire("ecarts_mensuel_vs_journalier.csv")
    cols = [c for c in e.columns if c.endswith("_ecart_%")]
    ecarts = pd.DataFrame({"Mois": e["mois"],
                           "Groupes en écart": (e[cols].abs() > 0.05).sum(axis=1),
                           "Plus grand écart (%)": e[cols].abs().max(axis=1)})

# -------------------------------------------------------------------- 7. classeur
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name, xl_rowcol_to_cell

wb = xlsxwriter.Workbook(SORTIE, {"nan_inf_to_errors": True})
for _nom in ["Synthèse", "Statistiques", "État des données", "Outil", "Données", "Référentiel"]:
    wb.add_worksheet(_nom)            # ordre des onglets du classeur
F = {
    "titre": wb.add_format({"bold": True, "font_size": 16, "font_color": "#1F3864"}),
    "sous": wb.add_format({"bold": True, "font_size": 12, "font_color": "#1F3864"}),
    "note": wb.add_format({"italic": True, "font_color": "#595959", "text_wrap": True, "valign": "top"}),
    "entete": wb.add_format({"bold": True, "bg_color": "#1F3864", "font_color": "white", "border": 1,
                             "text_wrap": True, "valign": "vcenter", "align": "center"}),
    "texte": wb.add_format({"border": 1, "text_wrap": True, "valign": "top"}),
    "gras": wb.add_format({"border": 1, "bold": True, "valign": "top"}),
    "n0": wb.add_format({"border": 1, "num_format": "#,##0"}),
    "n1": wb.add_format({"border": 1, "num_format": "#,##0.0"}),
    "n2": wb.add_format({"border": 1, "num_format": "#,##0.00"}),
    "pct": wb.add_format({"border": 1, "num_format": "+0.0;-0.0;0.0"}),
    "date": wb.add_format({"border": 1, "num_format": "dd/mm/yyyy"}),
    "saisie": wb.add_format({"border": 2, "bg_color": "#FFF2CC", "bold": True, "align": "center"}),
    "saisie_date": wb.add_format({"border": 2, "bg_color": "#FFF2CC", "bold": True, "align": "center",
                                  "num_format": "dd/mm/yyyy"}),
    "alerte": wb.add_format({"bold": True, "font_color": "#C00000", "text_wrap": True}),
    "msg": wb.add_format({"text_wrap": True, "valign": "top", "border": 1}),
}


def tableau(ws, r, c, df, fmt, index_nom="Groupe", fmt_col=None, largeur=None):
    """Ecrit un DataFrame (index = groupes) a partir de (r, c). Renvoie la ligne suivante."""
    ws.write(r, c, index_nom, F["entete"])
    for j, nom in enumerate(df.columns):
        ws.write(r, c + 1 + j, nom, F["entete"])
    for i, (idx, ligne) in enumerate(df.iterrows(), start=1):
        ws.write(r + i, c, idx, F["gras"])
        for j, v in enumerate(ligne):
            f = F[(fmt_col or {}).get(df.columns[j], fmt)]
            if isinstance(v, (str, np.str_)):
                ws.write(r + i, c + 1 + j, v, F["texte"])
            elif pd.isna(v):
                ws.write(r + i, c + 1 + j, "–", F["texte"])
            else:
                ws.write_number(r + i, c + 1 + j, float(v), f)
    return r + len(df) + 1


# ---- Synthese
ws = wb.get_worksheet_by_name("Synthèse")
ws.hide_gridlines(2)
ws.set_column(0, 0, 3)
ws.set_column(1, 1, 30)
ws.set_column(2, 9, 17)
ws.write(0, 1, "Analyse des ventes de la pharmacie", F["titre"])
ws.write(1, 1, "Statistiques recalculées par le code (classeur.py) à partir des exports du client.", F["note"])
ws.write(3, 1, "Messages principaux", F["sous"])
r = 4
for msg in messages:
    ws.merge_range(r, 1, r, 9, "• " + msg, F["msg"])
    ws.set_row(r, 32)
    r += 1
ws.write(r + 1, 1, "Fiche par groupe de médicaments", F["sous"])
fiche_fmt = {"Moyenne par jour": "n1", "Évolution 2015-2018 (%)": "pct", f"Prévision {nom_prochain}": "n0"}
fin = tableau(ws, r + 2, 1, fiche, "n1", fmt_col=fiche_fmt)
ws.set_row(r + 2, 45)
ws.merge_range(fin + 1, 1, fin + 1, 9,
               "Indice : 100 = jour (ou mois) moyen du groupe ; 120 = 20 % de plus que la moyenne. "
               "« Prévisible » = le modèle réduit l'erreur d'au moins 20 % par rapport à la référence naïve "
               "(voir feuille Statistiques).", F["note"])
ws.set_row(fin + 1, 32)

# ---- Statistiques
ws = wb.get_worksheet_by_name("Statistiques")
ws.hide_gridlines(2)
ws.set_column(0, 0, 30)
ws.set_column(1, 26, 11)
ws.write(0, 0, "Statistiques descriptives", F["titre"])
r = 2


def bloc(titre, lecture, df, fmt, couleurs=None, **kw):
    global r
    ws.write(r, 0, titre, F["sous"])
    ws.merge_range(r + 1, 0, r + 1, 9, lecture, F["note"])
    ws.set_row(r + 1, 30)
    debut = r + 2
    r = tableau(ws, debut, 0, df, fmt, **kw)
    if couleurs == "indice":
        ws.conditional_format(debut + 1, 1, r - 1, len(df.columns), {
            "type": "3_color_scale", "min_type": "num", "min_value": 40, "mid_type": "num", "mid_value": 100,
            "max_type": "num", "max_value": 180, "min_color": "#9DC3E6", "mid_color": "#FFFFFF", "max_color": "#F4B183"})
    elif couleurs == "part":
        ws.conditional_format(debut + 1, 1, r - 1, len(df.columns), {
            "type": "2_color_scale", "min_color": "#FFFFFF", "max_color": "#9DC3E6"})
    r += 2


bloc("1. Résumé par groupe (jours complets)",
     "Ce qui se vend et si c'est régulier. Un coefficient de variation élevé ou beaucoup de jours sans vente "
     "signalent un produit difficile à stocker.",
     resume, "n1", fmt_col={"Total": "n0", "Coefficient de variation": "n2"})
bloc("2. Jour de semaine : indice (100 = jour moyen du groupe)",
     "Pour savoir quels jours renforcer le stock et l'équipe.", indice_jour, "n0", "indice")
bloc("3. Heure : part de chaque heure dans les ventes de la journée (%)",
     "Pour repérer les pics et les heures creuses (heures d'ouverture, jours complets).",
     part_heure, "n1", "part")
bloc("4. Saisonnalité : indice par mois (100 = mois moyen du groupe)",
     "Pour savoir quelles périodes de l'année anticiper (mensuel reconstruit depuis le journalier).",
     indice_mois, "n0", "indice")
bloc("5. Tendance : total par année complète",
     "Pour savoir quels groupes montent ou baissent. L'année 2017 est basse pour une cause inconnue.",
     annuel, "n0", fmt_col={"Évolution 2015-2018 (%)": "pct"})
bloc("6. Test de prévision (24 derniers mois)",
     f"Chaque mois est prévu avec les seuls mois précédents, puis comparé au réel. « Oui » si le modèle "
     f"réduit l'erreur d'au moins 20 % par rapport à la meilleure prévision naïve (« comme le mois dernier » "
     f"ou « comme le même mois l'an dernier »). Erreurs en unités du logiciel de caisse.",
     prevision, "n1", fmt_col={"Rapport (modèle / référence)": "n2", "Erreur relative du modèle (%)": "n1",
                               f"Prévision {nom_prochain}": "n0"})
if grippe is not None:
    bloc("7. Environnement : lien avec la grippe (réseau Sentinelles)",
         "Corrélation hebdomadaire avec les syndromes grippaux en France ; semaine de forte grippe = au moins "
         "150 cas pour 100 000 habitants (seuil choisi par nous).",
         grippe, "n1", fmt_col={"Corrélation avec la grippe": "n2", "Écart (%)": "pct"})

# ---- Etat des donnees
ws = wb.get_worksheet_by_name("État des données")
ws.hide_gridlines(2)
ws.set_column(0, 0, 18)
ws.set_column(1, 1, 60)
ws.set_column(2, 2, 18)
ws.set_column(3, 3, 60)
ws.write(0, 0, "État des données", F["titre"])
ws.write(2, 0, "Quel export pour quoi", F["sous"])
for j, nom in enumerate(usages.columns):
    ws.write(3, j, nom, F["entete"])
for i, ligne in enumerate(usages.itertuples(index=False), start=4):
    for j, v in enumerate(ligne):
        ws.write(i, j, v, F["texte"])
    ws.set_row(i, 48)
r = 4 + len(usages) + 2
ws.write(r, 0, "Journal du nettoyage", F["sous"])
for j, nom in enumerate(etat.columns):
    ws.write(r + 1, j, nom, F["entete"])
for i, ligne in enumerate(etat.itertuples(index=False), start=r + 2):
    for j, v in enumerate(ligne):
        ws.write(i, j, v, F["texte"])
    ws.set_row(i, 48)
r = r + 2 + len(etat) + 1
if ecarts is not None:
    ws.write(r, 0, "Mois où le mensuel du client diffère de la somme des jours", F["sous"])
    r += 1
    for j, nom in enumerate(ecarts.columns):
        ws.write(r, j, nom, F["entete"])
    for i, ligne in enumerate(ecarts.itertuples(index=False), start=r + 1):
        ws.write(i, 0, ligne[0], F["texte"])
        ws.write_number(i, 1, ligne[1], F["n0"])
        ws.write_number(i, 2, ligne[2], F["n1"])
    r += len(ecarts) + 2
ws.write(r, 0, "Pour lire les chiffres", F["sous"])
for k, t in enumerate([
        "L'unité des quantités n'est pas documentée (des valeurs comme 0,33 ou 3,67 existent) et l'export ne contient aucun prix.",
        "Les groupes ne se comparent pas entre eux en volume ; aucune conclusion n'est exprimée en euros ou en marge.",
        "L'export ne couvre que 8 groupes : une heure creuse pour eux ne l'est pas forcément pour toute la pharmacie.",
        "Les valeurs extrêmes sont signalées dans l'export mais conservées (non vérifiables, cohérentes avec l'hebdomadaire)."], start=1):
    ws.merge_range(r + k, 0, r + k, 3, "• " + t, F["msg"])

# ---- Donnees (journalier complet, base de l'outil)
wd = wb.get_worksheet_by_name("Données")
colonnes = ["Date"] + groupes + ["Journée complète", "Jour"]
for j, nom in enumerate(colonnes):
    wd.write(0, j, nom, F["entete"])
wd.set_row(0, 45)
wd.set_column(0, 0, 12)
wd.set_column(1, len(groupes), 14)
wd.set_column(len(groupes) + 1, len(groupes) + 2, 12)
for i, ligne in enumerate(d_tout.itertuples(index=False), start=1):
    ligne = ligne._asdict()
    wd.write_datetime(i, 0, ligne["date"].to_pydatetime(), F["date"])
for j, g in enumerate(groupes, start=1):
    wd.write_column(1, j, d_tout[g].astype(float).tolist(), F["n2"])
wd.write_column(1, len(groupes) + 1, np.where(d_tout["journee_complete"], "Oui", "Non").tolist())
wd.write_column(1, len(groupes) + 2, d_tout["jour_semaine"].tolist())
wd.freeze_panes(1, 1)
wd.autofilter(0, 0, len(d_tout), len(colonnes) - 1)
n = len(d_tout) + 1                                   # derniere ligne de donnees (1-indexee)
PLAGE_DATE = f"'Données'!$A$2:$A${n}"
col_compl = xl_col_to_name(len(groupes) + 1)
PLAGE_COMPL = f"'Données'!${col_compl}$2:${col_compl}${n}"

# ---- Referentiel
wr = wb.get_worksheet_by_name("Référentiel")
wr.set_column(0, 0, 34)
wr.set_column(1, 1, 30)
wr.set_column(2, 2, 12)
wr.write(0, 0, "Groupes de médicaments (classification ATC de l'OMS)", F["sous"])
for j, nom in enumerate(ref.columns):
    wr.write(2, j, nom, F["entete"])
for i, ligne in enumerate(ref.itertuples(index=False), start=3):
    for j, v in enumerate(ligne):
        wr.write(i, j, v, F["texte"])

# ---- Outil de selection (formules Excel, sans macro)
wo = wb.get_worksheet_by_name("Outil")
wo.hide_gridlines(2)
wo.set_column(0, 0, 3)
wo.set_column(1, 1, 34)
wo.set_column(2, 5, 17)
wo.set_column(6, 9, 17)
wo.write(0, 1, "Outil de sélection des ventes", F["titre"])
wo.merge_range(1, 1, 1, 7, "1) Choisissez la période (même date deux fois = un seul jour).  "
               "2) Mettez Oui ou Non devant chaque groupe.  Les ventes s'affichent aussitôt.", F["note"])
wo.set_row(1, 30)
dmin, dmax = d_tout["date"].min().to_pydatetime(), d_tout["date"].max().to_pydatetime()
fin_mois = dernier_mois.to_pydatetime()
debut_mois = fin_mois.replace(day=1)
wo.write(3, 1, "Date de début", F["gras"])
wo.write_datetime(3, 2, debut_mois, F["saisie_date"])
wo.write(4, 1, "Date de fin", F["gras"])
wo.write_datetime(4, 2, fin_mois, F["saisie_date"])
for ligne in (3, 4):
    wo.data_validation(ligne, 2, ligne, 2, {"validate": "date", "criteria": "between",
                       "minimum": dmin, "maximum": dmax,
                       "error_title": "Date hors historique",
                       "error_message": f"Choisissez une date entre {dmin:%d/%m/%Y} et {dmax:%d/%m/%Y}."})
wo.write(3, 3, f"Historique : du {dmin:%d/%m/%Y} au {dmax:%d/%m/%Y}", F["note"])
wo.write(5, 1, "Jours couverts par la période", F["gras"])
DEB, FIN = "$C$4", "$C$5"
wo.write_formula(5, 2, f'=COUNTIFS({PLAGE_DATE},">="&{DEB},{PLAGE_DATE},"<="&{FIN})', F["n0"])
n_incompl = f'COUNTIFS({PLAGE_DATE},">="&{DEB},{PLAGE_DATE},"<="&{FIN},{PLAGE_COMPL},"Non")'
wo.merge_range(6, 1, 6, 7, "", F["alerte"])
wo.write_formula(6, 1,
    f'=IF({FIN}<{DEB},"La date de fin est avant la date de début.",'
    f'IF($C$6=0,"Aucune vente enregistrée sur cette période.",'
    f'IF({n_incompl}>0,"Attention : la période contient "&{n_incompl}&" journée(s) incomplète(s) (début ou fin de l\'export).","")))',
    F["alerte"])
ENT = 8
for j, nom in enumerate(["Groupe", "Afficher ?", "Total sur la période", "Moyenne par jour"]):
    wo.write(ENT, 1 + j, nom, F["entete"])
for i, g in enumerate(groupes):
    r0 = ENT + 1 + i
    col = xl_col_to_name(1 + i)
    plage = f"'Données'!${col}$2:${col}${n}"
    wo.write(r0, 1, g, F["gras"])
    wo.write(r0, 2, "Oui", F["saisie"])
    wo.write_formula(r0, 3,
        f'=IF($C{r0 + 1}="Oui",SUMIFS({plage},{PLAGE_DATE},">="&{DEB},{PLAGE_DATE},"<="&{FIN}),"")', F["n1"])
    wo.write_formula(r0, 4, f'=IF(AND($C{r0 + 1}="Oui",$C$6>0),D{r0 + 1}/$C$6,"")', F["n1"])
wo.data_validation(ENT + 1, 2, ENT + len(groupes), 2, {"validate": "list", "source": ["Oui", "Non"]})
wo.write(ENT + len(groupes) + 1, 1, "Quantités en unités du logiciel de caisse ; les groupes ne se comparent pas entre eux.", F["note"])

# detail jour par jour (93 premiers jours de la periode)
NJ = 93
DET = ENT + len(groupes) + 4
wo.write(DET - 1, 1, "Détail jour par jour", F["sous"])
wo.write_formula(DET - 1, 4, f'=IF($C$6>{NJ},"Seuls les {NJ} premiers jours de la période sont détaillés.","")', F["alerte"])
wo.write(DET, 1, "Date", F["entete"])
for j, g in enumerate(groupes):
    wo.write_formula(DET, 2 + j, f'=B{ENT + 2 + j}', F["entete"])
wo.set_row(DET, 45)
for k in range(NJ):
    rr = DET + 1 + k
    wo.write_formula(rr, 1,
        f'=IF(AND({DEB}+{k}<={FIN},COUNTIF({PLAGE_DATE},{DEB}+{k})>0),{DEB}+{k},"")', F["date"])
    for j in range(len(groupes)):
        col = xl_col_to_name(1 + j)
        plage = f"'Données'!${col}$2:${col}${n}"
        sel = f"$C${ENT + 2 + j}"
        wo.write_formula(rr, 2 + j,
            f'=IF(OR($B{rr + 1}="",{sel}<>"Oui"),"",SUMIFS({plage},{PLAGE_DATE},$B{rr + 1}))', F["n1"])
wo.freeze_panes(0, 0)

wb.get_worksheet_by_name("Synthèse").activate()
wb.close()
print("Classeur écrit :", SORTIE)
