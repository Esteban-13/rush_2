"""Chargement, controles et nettoyage des 4 exports de ventes.

Version en fonctions de nettoyage.py, utilisee par l'application : rien n'est ecrit sur
le disque, tout est renvoye en memoire. Les constats du journal sont calcules a partir
des fichiers recus (aucune date ni aucun chiffre ecrit en dur).
"""
import io
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parent.parent
REFERENTIEL = RACINE / "data" / "ref" / "atc.csv"

TYPES = ["horaire", "journalier", "hebdomadaire", "mensuel"]
MOTS_CLES = {
    "horaire": ["hourly", "horaire", "heure"],
    "journalier": ["daily", "journalier", "jour"],
    "hebdomadaire": ["weekly", "hebdo", "semaine"],
    "mensuel": ["monthly", "mensuel", "mois"],
}
COLONNES_TECHNIQUES = {"datum", "date", "year", "month", "hour", "weekday name"}
FORMATS_DATE = ["%m/%d/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"]
JOURS_FR = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"]
TOL = 0.05          # tolerance (en unites) pour dire que deux totaux concordent
SEUIL_Z = 8         # seuil de valeur extreme (z-score robuste)


class ErreurExport(Exception):
    """Probleme dans les fichiers deposes, a expliquer a l'utilisateur (message en clair)."""


@dataclass
class Resultat:
    horaire: pd.DataFrame
    journalier: pd.DataFrame
    hebdo: pd.DataFrame
    mensuel: pd.DataFrame
    groupes: list
    journal: pd.DataFrame
    ecarts: pd.DataFrame            # mois x groupe ou le mensuel du client differe des jours
    infos: dict = field(default_factory=dict)


def mois_annee(date):
    return f"{MOIS_FR[date.month - 1]} {date.year}"


def lire_csv(contenu, nom="fichier"):
    """Lit un export (octets ou chemin). Accepte virgule ou point-virgule, UTF-8 ou Latin-1."""
    if isinstance(contenu, (str, Path)):
        contenu = Path(contenu).read_bytes()
    for encodage in ("utf-8-sig", "latin-1"):
        try:
            texte = contenu.decode(encodage)
            break
        except UnicodeDecodeError:
            continue
    premiere = texte.split("\n", 1)[0]
    sep = ";" if premiere.count(";") > premiere.count(",") else ","
    try:
        df = pd.read_csv(io.StringIO(texte), sep=sep, decimal="," if sep == ";" else ".")
    except Exception as e:
        raise ErreurExport(f"« {nom} » n'est pas un fichier CSV lisible ({e}).")
    if df.empty or len(df.columns) < 2:
        raise ErreurExport(f"« {nom} » est vide ou ne contient qu'une seule colonne.")
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _colonne_date(df, nom):
    for c in df.columns:
        if c.lower() in ("datum", "date"):
            return c
    raise ErreurExport(f"« {nom} » : colonne de date introuvable (attendue : « datum »).")


def _dates(serie, nom):
    texte = serie.astype(str).str.strip()
    for fmt in FORMATS_DATE:
        try:
            return pd.to_datetime(texte, format=fmt)
        except (ValueError, TypeError):
            continue
    raise ErreurExport(f"« {nom} » : format de date non reconnu (exemple lu : « {texte.iloc[0]} »).")


def _type_par_nom(nom):
    bas = nom.lower()
    for t, mots in MOTS_CLES.items():
        if any(m in bas for m in mots):
            return t
    return None


def _type_par_contenu(dates):
    pas = dates.sort_values().diff().dropna().dt.total_seconds().median() / 86400
    if pas < 0.5:
        return "horaire"
    if pas < 3:
        return "journalier"
    if pas < 15:
        return "hebdomadaire"
    return "mensuel"


def referentiel():
    """Code ATC -> 'Nom (code)'. Un code absent du referentiel garde son code comme nom."""
    try:
        ref = pd.read_csv(REFERENTIEL)
        return {c: f"{lib} ({c})" for c, lib in zip(ref["code_atc"], ref["libelle"])}
    except Exception:
        return {}


def _prepare(nom, contenu):
    df = lire_csv(contenu, nom)
    col = _colonne_date(df, nom)
    dates = _dates(df[col], nom)
    codes = [c for c in df.columns if c.lower() not in COLONNES_TECHNIQUES]
    if not codes:
        raise ErreurExport(f"« {nom} » : aucune colonne de ventes trouvée.")
    valeurs = df[codes].apply(pd.to_numeric, errors="coerce")
    if valeurs.isna().any().any():
        fautives = valeurs.columns[valeurs.isna().any()].tolist()
        raise ErreurExport(f"« {nom} » : valeurs manquantes ou non numériques dans {', '.join(fautives)}.")
    propre = pd.concat([dates.rename("date"), valeurs], axis=1)
    return propre, _type_par_nom(nom) or _type_par_contenu(dates)


def nettoyer(fichiers):
    """fichiers : liste de (nom, contenu). Renvoie un Resultat ou leve ErreurExport."""
    journal = []

    def note(fichier, niveau, constat, action):
        journal.append({"Fichier": fichier, "Niveau": niveau, "Constat": constat, "Action": action})

    # ---------------------------------------------------------------- 1. identification
    tables, noms = {}, {}
    for nom, contenu in fichiers:
        df, t = _prepare(nom, contenu)
        if t in tables:
            raise ErreurExport(f"Deux fichiers ressemblent à l'export {t} : « {noms[t]} » et « {nom} ».")
        tables[t], noms[t] = df, nom
    manquants = [t for t in TYPES if t not in tables]
    if manquants:
        recus = ", ".join(f"« {noms[t]} » ({t})" for t in TYPES if t in noms)
        raise ErreurExport(f"Fichier(s) reçu(s) : {recus}. Il manque l'export " + ", ".join(manquants)
                           + ". Déposez les quatre fichiers en même temps : horaire, journalier, hebdomadaire et mensuel.")

    codes = [c for c in tables["journalier"].columns if c != "date"]
    for t in TYPES:
        autres = [c for c in tables[t].columns if c != "date"]
        if set(autres) != set(codes):
            diff = sorted(set(autres) ^ set(codes))
            raise ErreurExport(f"Les groupes de médicaments ne sont pas les mêmes dans l'export {t} "
                               f"et dans l'export journalier (différence : {', '.join(diff)}).")
    lib = referentiel()
    inconnus = [c for c in codes if c not in lib]
    if inconnus:
        note("tous", "attention", f"Code(s) absent(s) du référentiel des noms : {', '.join(inconnus)}",
             "affichés avec leur code seul ; compléter data/ref/atc.csv")
    nom_groupe = {c: lib.get(c, c) for c in codes}

    # ------------------------------------------------------------- 2. controles de base
    for t in TYPES:
        df = tables[t]
        if not df["date"].is_monotonic_increasing:
            df = df.sort_values("date")
            note(t, "info", "Lignes non triées par date", "triées")
        doublons = int(df["date"].duplicated().sum())
        if doublons:
            df = df[~df["date"].duplicated()]
            note(t, "attention", f"{doublons} date(s) en double", "première occurrence conservée")
        negatives = int((df[codes] < 0).sum().sum())
        if negatives:
            note(t, "attention", f"{negatives} valeur(s) négative(s)", "conservées, à vérifier avec le client")
        tables[t] = df.reset_index(drop=True)
    h, d, w, m = (tables[t] for t in TYPES)
    note("tous", "ok", f"Quatre exports reconnus, {len(codes)} groupes de médicaments, "
         f"du {d['date'].min():%d/%m/%Y} au {d['date'].max():%d/%m/%Y}", "dates converties")

    # ----------------------------------------------- 3. journees completes (24 heures)
    h["jour"] = h["date"].dt.normalize()
    heures_par_jour = h.groupby("jour").size()
    jours_complets = set(heures_par_jour[heures_par_jour == 24].index)
    d["journee_complete"] = d["date"].isin(jours_complets)
    tronques = d.loc[~d["journee_complete"], "date"]
    if len(tronques):
        note("journalier", "info", f"{len(tronques)} journée(s) incomplète(s) : "
             + ", ".join(f"{x:%d/%m/%Y}" for x in tronques[:6]) + (" …" if len(tronques) > 6 else ""),
             "écartées des moyennes")
    absents = pd.date_range(d["date"].min(), d["date"].max()).difference(d["date"])
    if len(absents):
        note("journalier", "attention", f"{len(absents)} jour(s) absent(s) au milieu de l'export",
             "les mois et semaines concernés sont marqués incomplets")

    # ------------------------------------------------ 4. coherence entre les 4 exports
    dj = d.set_index("date")[codes]
    hd = h.groupby("jour")[codes].sum()
    commun = hd.index.intersection(dj.index)
    ecart_h = float((hd.loc[commun] - dj.loc[commun]).abs().max().max()) if len(commun) else np.nan
    if len(commun) and ecart_h <= TOL:
        note("horaire", "ok", "La somme des heures est égale au journalier", "exports cohérents")
    else:
        n = int(((hd.loc[commun] - dj.loc[commun]).abs().max(axis=1) > TOL).sum())
        note("horaire", "attention", f"La somme des heures diffère du journalier pour {n} jour(s) "
             f"(écart maximal {ecart_h:.2f})", "à vérifier avec le client ; le journalier sert de base")

    sem = dj.resample("W-SUN").sum()
    ws = w.set_index("date")[codes]
    commun = sem.index.intersection(ws.index)
    ecart_w = float((sem.loc[commun] - ws.loc[commun]).abs().max().max()) if len(commun) else np.nan
    if len(commun) and ecart_w <= TOL:
        note("hebdomadaire", "ok", "La somme des jours est égale à l'hebdomadaire (semaine du lundi au dimanche)",
             "exports cohérents")
    else:
        n = int(((sem.loc[commun] - ws.loc[commun]).abs().max(axis=1) > TOL).sum()) if len(commun) else len(ws)
        note("hebdomadaire", "attention", f"L'hebdomadaire diffère de la somme des jours pour {n} semaine(s)",
             "à vérifier avec le client ; le journalier sert de base")

    mois_calc = dj.resample("ME").sum()
    mm = m.set_index("date")[codes]
    mm.index = mm.index + pd.offsets.MonthEnd(0)
    commun = mois_calc.index.intersection(mm.index)
    diff = mm.loc[commun] - mois_calc.loc[commun]
    ko = diff.abs() > TOL
    n_ko = int(ko.any(axis=1).sum())
    if n_ko:
        note("mensuel", "attention", f"Le mensuel du client diffère de la somme des jours pour {n_ko} mois "
             f"sur {len(commun)}", "mensuel du client écarté ; mois recalculés à partir du journalier")
    else:
        note("mensuel", "ok", "Le mensuel du client est égal à la somme des jours", "exports cohérents")
    pct = 100 * (mm.loc[commun] / mois_calc.loc[commun].replace(0, np.nan) - 1)
    morceaux = [pd.DataFrame({"mois": commun[ko[c].values], "groupe": nom_groupe[c],
                              "export": mm.loc[commun, c][ko[c].values].values,
                              "recalcule": mois_calc.loc[commun, c][ko[c].values].values,
                              "ecart_pct": pct[c][ko[c].values].values}) for c in codes]
    ecarts = pd.concat(morceaux, ignore_index=True)

    # ---------------------------------------------------------- 5. periodes completes
    n_sem = d.groupby(d["date"].dt.to_period("W-SUN"))["journee_complete"].sum()
    w["semaine_complete"] = n_sem.reindex(w["date"].dt.to_period("W-SUN")).fillna(0).values == 7
    n_mois = d.groupby(d["date"].dt.to_period("M"))["journee_complete"].sum()
    mensuel = mois_calc.reset_index()
    periodes = mensuel["date"].dt.to_period("M")
    mensuel["mois_complet"] = n_mois.reindex(periodes).fillna(0).values == periodes.dt.days_in_month.values
    incomplets = mensuel.loc[~mensuel["mois_complet"], "date"]
    complets = mensuel.loc[mensuel["mois_complet"], "date"]
    if complets.empty:
        raise ErreurExport("Aucun mois complet dans les exports : l'analyse n'est pas possible.")
    dernier_mois = complets.max()
    if len(incomplets):
        note("mensuel", "info", "Mois incomplet(s) : " + ", ".join(mois_annee(x) for x in incomplets[:6])
             + (" …" if len(incomplets) > 6 else ""), f"écartés ; dernier mois complet : {mois_annee(dernier_mois)}")
    n_sem_ko = int((~w["semaine_complete"]).sum())
    if n_sem_ko:
        note("hebdomadaire", "info", f"{n_sem_ko} semaine(s) incomplète(s)", "écartées des analyses par semaine")

    # --------------------------------------------------------- 6. heures d'ouverture
    h["heure"] = h["date"].dt.hour
    total_h = h.groupby("heure")[codes].sum().sum(axis=1)
    actives = total_h[total_h > 0].index
    h["heure_ouverture"] = h["heure"].isin(actives)
    if len(actives):
        note("horaire", "info", f"Ventes enregistrées de {actives.min()} h à {actives.max()} h",
             "les autres heures sont écartées des moyennes horaires")

    # ----------------------------------------- 7. valeurs extremes et quantites a virgule
    def z_robuste(s):
        med = s.median()
        mad = (s - med).abs().median() * 1.4826
        return (s - med) / (mad if mad > 0 else 1)

    n_extremes = int((d[codes].apply(z_robuste).abs() > SEUIL_Z).sum().sum())
    if n_extremes:
        note("journalier", "info", f"{n_extremes} valeur(s) journalière(s) très élevée(s)",
             "conservées : impossible de dire si ce sont des erreurs")
    n_frac = int(((d[codes] % 1) != 0).sum().sum())
    if n_frac:
        note("journalier", "info", f"{n_frac} quantité(s) non entière(s) : l'unité de l'export n'est pas documentée",
             "conservées ; les groupes ne se comparent pas entre eux en volume")

    # ------------------------------------------------------------- 8. tables propres
    groupes = [nom_groupe[c] for c in codes]
    h_out = h[["date", *codes, "heure", "heure_ouverture"]].rename(columns=nom_groupe)
    h_out["journee_complete"] = h["jour"].isin(jours_complets).values
    h_out["jour_semaine"] = h["date"].dt.dayofweek.map(dict(enumerate(JOURS_FR))).values
    d_out = d[["date", *codes, "journee_complete"]].rename(columns=nom_groupe)
    d_out["jour_semaine"] = d["date"].dt.dayofweek.map(dict(enumerate(JOURS_FR)))
    d_out["annee"] = d["date"].dt.year
    w_out = w[["date", *codes, "semaine_complete"]].rename(columns={**nom_groupe, "date": "date_fin_semaine"})
    m_out = mensuel.rename(columns={**nom_groupe, "date": "date_fin_mois"})

    infos = {
        "debut": d["date"].min(), "fin": d["date"].max(),
        "jours_complets": int(d["journee_complete"].sum()),
        "dernier_mois_complet": dernier_mois, "mois_complets": int(mensuel["mois_complet"].sum()),
        "mois_en_ecart": n_ko, "mois_compares": int(len(commun)),
        "heure_min": int(actives.min()) if len(actives) else None,
        "heure_max": int(actives.max()) if len(actives) else None,
        "fichiers": noms,
    }
    return Resultat(h_out, d_out, w_out, m_out, groupes, pd.DataFrame(journal), ecarts, infos)


def nom_court(groupe):
    """'Paracétamol (N02BE)' -> 'Paracétamol'."""
    return re.sub(r"\s*\(.*\)$", "", groupe)
