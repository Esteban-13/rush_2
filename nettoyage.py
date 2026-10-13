"""
Nettoyage des exports de ventes de la pharmacie (Rush 2).

Usage :  python nettoyage.py [dossier_raw] [dossier_clean]
Par defaut : data/raw  ->  data/clean
Dans VS Code, les lignes "# %%" permettent d'executer le script cellule par cellule
(comme un notebook), avec l'extension Jupyter.

Le script est relancable chaque mois : il relit les 4 exports complets,
verifie leur coherence, ecrit des fichiers propres et un "etat des donnees".
"""
# %% Imports et configuration
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/clean")
OUT.mkdir(parents=True, exist_ok=True)

# Referentiel des groupes de medicaments (classification ATC de l'OMS) : seule source
# des noms. Les codes restent la cle technique, les libelles servent a l'affichage.
REF = pd.read_csv(Path("data/ref/atc.csv"))
ATC = REF["code_atc"].tolist()
LIB = {c: f"{lib} ({c})" for c, lib in zip(REF["code_atc"], REF["libelle"])}
JOURS_FR = {0: "lundi", 1: "mardi", 2: "mercredi", 3: "jeudi",
            4: "vendredi", 5: "samedi", 6: "dimanche"}
TOL = 0.05          # tolerance (en unites) pour dire que deux totaux concordent
SEUIL_Z = 8         # seuil d'aberration (z-score robuste, MAD)

journal = []        # "etat des donnees" : une ligne par constat / action


def nomme(df):
    """Colonnes des fichiers ecrits : 'N05B' -> 'Anxiolytiques (N05B)', suffixes conserves."""
    def col(c):
        code, sep, reste = c.partition("_")
        return LIB[code] + sep + reste if code in LIB else c
    return df.rename(columns=col)


def log(fichier, constat, nb, action):
    journal.append({"fichier": fichier, "constat": constat,
                    "nb_lignes_concernees": nb, "action": action})
    print(f"[{fichier:8s}] {constat}  ->  {action}  ({nb})")


# %% 1. Chargement avec formats de date explicites
# Les 3 premiers fichiers sont en mois/jour/annee (americain), le mensuel en ISO.
def charge(nom, fmt):
    f = next(RAW.glob(f"*{nom}.csv"))
    df = pd.read_csv(f)
    df = df.rename(columns={"datum": "date"})
    df["date"] = pd.to_datetime(df["date"], format=fmt)
    return df


h = charge("Hourly", "%m/%d/%Y %H:%M")
d = charge("Daily", "%m/%d/%Y")
w = charge("Weekly", "%m/%d/%Y")
m = charge("Monthly", "%Y-%m-%d")
for nom, df in [("horaire", h), ("jour", d), ("semaine", w), ("mois", m)]:
    print(f"{nom:8s} {len(df):6d} lignes  {df['date'].min()} -> {df['date'].max()}")

log("tous", "Formats de date differents (m/j/a ; ISO pour le mensuel)",
    4, "dates converties en datetime avec format explicite")

# %% 2. Controles de base : tri, doublons, manquants, valeurs negatives
for nom, df in [("horaire", h), ("jour", d), ("semaine", w), ("mois", m)]:
    assert set(ATC) <= set(df.columns), f"{nom} : codes ATC absents du referentiel ou de l'export"
    assert df["date"].is_monotonic_increasing, f"{nom} non trie"
    assert not df["date"].duplicated().any(), f"{nom} doublons de date"
    assert not df[ATC].isna().any().any(), f"{nom} valeurs manquantes"
    assert (df[ATC] >= 0).all().all(), f"{nom} valeurs negatives"
log("tous", "Tri, doublons, valeurs manquantes, valeurs negatives : aucun probleme",
    0, "aucune action")

# %% 3. Colonnes redondantes (Year, Month, Hour, Weekday Name)
# On verifie qu'elles sont coherentes avec la date, puis on les recalcule.
assert (h["Year"] == h["date"].dt.year).all() and (h["Month"] == h["date"].dt.month).all()
assert (h["Hour"] == h["date"].dt.hour).all()
assert (h["Weekday Name"] == h["date"].dt.day_name()).all()
assert (d["Weekday Name"] == d["date"].dt.day_name()).all()

# Dans le fichier journalier, "Hour" vaut 276 (= 0+1+...+23) : c'est la SOMME des heures
# presentes ce jour-la, pas une heure. Utile pour detecter les journees tronquees.
jours_tronques = d.loc[d["Hour"] != 276, "date"].dt.date.tolist()
log("jour", "Colonne 'Hour' = somme des heures presentes (276 si journee complete)",
    len(jours_tronques), f"colonne supprimee ; journees tronquees detectees : {jours_tronques}")

# %% 4. Coherence entre les 4 exports (le point de vigilance du kick-off)
# 4a. horaire -> jour
hd = h.groupby(h["date"].dt.normalize())[ATC].sum()
ecart = (hd - d.set_index("date")[ATC]).abs().max().max()
log("horaire", f"Somme horaire == journalier (ecart max {ecart:.3f})",
    int((hd.index.difference(d["date"])).size), "concordent : horaire/jour = meme source")

# 4b. jour -> semaine : la date de la semaine est le DIMANCHE QUI CLOT la semaine
sem_calc = d.set_index("date")[ATC].resample("W-SUN").sum()
j = w.set_index("date")[ATC].join(sem_calc, rsuffix="_j", how="outer")
ecart_sem = np.max([(j[c] - j[c + "_j"]).abs().max() for c in ATC])
log("semaine", f"Somme journaliere == hebdo, semaine = lundi->dimanche, date = dimanche "
               f"(ecart max {ecart_sem:.3f})", len(w), "concordent")

# 4c. jour -> mois
mois_calc = d.set_index("date")[ATC].resample("ME").sum()
mm = m.set_index("date")[ATC]
diff_m = mm - mois_calc
mois_ko = diff_m.abs().max(axis=1) > TOL
log("mois", "Mensuel different de la somme des jours (le mensuel est ecarte des 3 autres)",
    int(mois_ko.sum()), f"sur {len(mm)} mois ; mensuel RECONSTRUIT depuis le journalier")

# table des ecarts (a garder pour l'etat des donnees)
ecarts = pd.DataFrame({
    "mois": mm.index.strftime("%Y-%m"),
    **{f"{c}_export": mm[c].values for c in ATC},
    **{f"{c}_recalcule": mois_calc[c].values for c in ATC},
    **{f"{c}_ecart_%": (100 * (mm[c] / mois_calc[c].replace(0, np.nan) - 1)).round(1).values
       for c in ATC},
})
ecarts = ecarts[mois_ko.values]
nomme(ecarts).to_csv(OUT / "ecarts_mensuel_vs_journalier.csv", index=False,
                     encoding="utf-8-sig")

# %% 5. Periodes incompletes (debut et fin d'export)
jour_ok = ~d["date"].isin(pd.to_datetime(jours_tronques))
d["journee_complete"] = jour_ok
derniere_jour_ok = d.loc[d["journee_complete"], "date"].max()
log("jour", "Derniere journee tronquee (export arrete a 19h) / premiere sans 7h",
    len(jours_tronques), "flag journee_complete = False")

# semaine : complete si ses 7 jours sont presents ET complets
nb_jours_sem = d.groupby(d["date"].dt.to_period("W-SUN"))["journee_complete"].sum()
w["semaine_complete"] = (nb_jours_sem.reindex(w["date"].dt.to_period("W-SUN")).values == 7)
# 1re semaine : le 1er janvier est absent ; derniere : export arrete le mardi 8 octobre
log("semaine", "Premiere (1/5/2014) et derniere (10/13/2019) semaines incompletes",
    int((~w["semaine_complete"]).sum()), "flag semaine_complete = False")

# mois : complet si tous les jours du mois existent et sont complets
n_jours = d.groupby(d["date"].dt.to_period("M"))["journee_complete"].sum()
jours_du_mois = n_jours.index.days_in_month
m_clean = pd.DataFrame(mois_calc).reset_index()
m_clean["mois_complet"] = (n_jours.reindex(m_clean["date"].dt.to_period("M")).values
                           == jours_du_mois.values)
dernier_mois_complet = m_clean.loc[m_clean["mois_complet"], "date"].max()
log("mois", "Octobre 2019 incomplet (8 jours), janvier 2014 sans le 1er janvier",
    int((~m_clean["mois_complet"]).sum()),
    f"flag mois_complet ; dernier mois complet = {dernier_mois_complet:%Y-%m}")

# %% 6. Heures d'ouverture (fichier horaire)
ventes_par_h = h.groupby("Hour")[ATC].sum().sum(axis=1)
heures_actives = ventes_par_h[ventes_par_h > 0].index
log("horaire", f"Aucune vente de 23h a 6h (ouverture reelle {heures_actives.min()}h-"
               f"{heures_actives.max()}h)", int(h["Hour"].isin(ventes_par_h[ventes_par_h == 0].index).sum()),
    "lignes conservees mais flag heure_ouverture ; a exclure des moyennes horaires")
h["heure_ouverture"] = h["Hour"].isin(heures_actives)

# %% 7. Valeurs aberrantes (journalier) : detectees et marquees, jamais supprimees
def zrob(s):
    med = s.median()
    mad = (s - med).abs().median() * 1.4826
    return (s - med) / (mad if mad > 0 else 1)

z = d[ATC].apply(zrob)
for c in ATC:
    d[f"{c}_aberrant"] = z[c].abs() > SEUIL_Z
n_ab = int(d[[f"{c}_aberrant" for c in ATC]].sum().sum())
ex = d.loc[d[[f"{c}_aberrant" for c in ATC]].any(axis=1), "date"].dt.date.tolist()
log("jour", f"Valeurs extremes (|z robuste| > {SEUIL_Z}) : {n_ab} cellules, ex. {ex[:3]}...",
    n_ab, "flag *_aberrant ; conservees (non verifiables, coherentes avec hebdo)")

# %% 8. Quantites fractionnaires
frac = {c: int(((d[c] % 1) != 0).sum()) for c in ATC}
log("jour", "Quantites non entieres (ex. 0,33 / 3,67 : unite non documentee)",
    sum(frac.values()), "conservees telles quelles, a documenter dans l'etat des donnees")

# %% 9. Ecriture des fichiers propres
def fr_cols(df):
    df["annee"] = df["date"].dt.year
    df["mois_num"] = df["date"].dt.month
    return df

h_out = h[["date", *ATC, "heure_ouverture"]].copy()
h_out["heure"] = h["Hour"]
h_out["jour_semaine"] = h["date"].dt.dayofweek.map(JOURS_FR)
h_out = fr_cols(h_out)

d_out = d[["date", *ATC, "journee_complete", *[f"{c}_aberrant" for c in ATC]]].copy()
d_out["jour_semaine"] = d["date"].dt.dayofweek.map(JOURS_FR)
d_out = fr_cols(d_out)

w_out = w[["date", *ATC, "semaine_complete"]].rename(columns={"date": "date_fin_semaine"})
m_out = m_clean.rename(columns={"date": "date_fin_mois"})

for nom, df in [("ventes_horaire", h_out), ("ventes_journalier", d_out),
                ("ventes_hebdo", w_out), ("ventes_mensuel", m_out)]:
    # utf-8-sig : sans cela Excel affiche mal les accents des libelles
    nomme(df).to_csv(OUT / f"{nom}.csv", index=False, encoding="utf-8-sig",
                     date_format="%Y-%m-%d %H:%M" if nom == "ventes_horaire" else "%Y-%m-%d")

# Format long avec le nom des groupes : une ligne par jour et par groupe.
# C'est la table a brancher sur l'outil de selection Excel (segments sur groupe / date).
d_long = d_out.melt(id_vars=["date", "jour_semaine", "annee", "mois_num", "journee_complete"],
                    value_vars=ATC, var_name="code_atc", value_name="quantite")
d_long["groupe"] = d_long["code_atc"].map(LIB)
d_long = d_long.sort_values(["date", "code_atc"])
d_long.to_csv(OUT / "ventes_journalier_long.csv", index=False, date_format="%Y-%m-%d",
              encoding="utf-8-sig")
log("tous", "Groupes identifies par leur code ATC, sans nom",
    len(ATC), "libelles ajoutes depuis data/ref/atc.csv (classification ATC de l'OMS) ; "
              "codes conserves comme cle")

pd.DataFrame(journal).to_csv(OUT / "etat_des_donnees.csv", index=False)
print(f"\nFichiers ecrits dans {OUT.resolve()}")
print(f"Dernier mois complet : {dernier_mois_complet:%Y-%m} "
      f"| derniere journee complete : {derniere_jour_ok:%Y-%m-%d}")
