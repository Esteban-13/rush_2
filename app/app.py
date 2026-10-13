"""Application locale : deposer les 4 exports de ventes, obtenir les controles et les analyses.

Aucune logique d'analyse ici : l'interface appelle src/nettoyage.py et src/analyses.py.
Lancement : streamlit run app/app.py   (ou double-clic sur lancer.bat)
"""
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RACINE))

from src import analyses as A  # noqa: E402
from src import nettoyage as N  # noqa: E402

EXEMPLE = RACINE / "data" / "raw"
BLEU, ORANGE, NEUTRE, FOND_NEUTRE = "#2a78d6", "#eb6834", "#b9bfc4", "#f1f0ec"
ENCRE, ENCRE_2 = "#0b0b0b", "#52514e"
MOIS_ABR = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

st.set_page_config(page_title="Ventes de la pharmacie", layout="wide", initial_sidebar_state="expanded")


# ------------------------------------------------------------------ utilitaires
def fr(x, decimales=0):
    """Nombre a la francaise : 1 234,5"""
    if pd.isna(x):
        return "–"
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


def montre(graphique):
    try:
        st.altair_chart(graphique, width="stretch")
    except TypeError:                      # versions plus anciennes de Streamlit
        st.altair_chart(graphique, use_container_width=True)


def tableau(df, formats=None):
    style = df.style.format(formats or {}, na_rep="–", decimal=",", thousands=" ")
    try:
        st.dataframe(style, width="stretch")
    except TypeError:
        st.dataframe(style, use_container_width=True)


def theme(graphique):
    return (graphique.configure_view(strokeWidth=0)
            .configure_axis(labelColor=ENCRE_2, titleColor=ENCRE_2, gridColor="#e7e6e1", domainColor="#c9c8c2",
                            tickColor="#c9c8c2", labelFontSize=12, titleFontSize=12)
            .configure_legend(labelColor=ENCRE_2, titleColor=ENCRE_2, labelFontSize=12, titleFontSize=12)
            .configure_header(labelColor=ENCRE, labelFontSize=13, labelFontWeight="bold", titleColor=ENCRE_2))


def carte_indices(t, colonnes, nom_x):
    """Tableau colore groupe x periode, indice 100 = moyenne du groupe (bleu = creux, orange = fort)."""
    t = t.copy()
    t.columns = colonnes
    t.index = [N.nom_court(g) for g in t.index]
    donnees = t.reset_index(names="Groupe").melt("Groupe", var_name=nom_x, value_name="Indice").dropna()
    base = alt.Chart(donnees).encode(
        x=alt.X(f"{nom_x}:N", sort=colonnes, title=None, axis=alt.Axis(labelAngle=0, orient="top", ticks=False, domain=False)),
        y=alt.Y("Groupe:N", sort=list(t.index), title=None, axis=alt.Axis(ticks=False, domain=False, labelLimit=220)))
    cases = base.mark_rect(stroke="white", strokeWidth=2, cornerRadius=3).encode(
        color=alt.Color("Indice:Q", scale=alt.Scale(domain=[40, 100, 180], range=[BLEU, FOND_NEUTRE, ORANGE], clamp=True, interpolate="rgb"),
                        legend=alt.Legend(title="Indice", orient="right", gradientLength=160)),
        tooltip=["Groupe", nom_x, alt.Tooltip("Indice:Q", format=".0f")])
    valeurs = base.mark_text(fontSize=12).encode(
        text=alt.Text("Indice:Q", format=".0f"),
        color=alt.condition("datum.Indice >= 150 || datum.Indice <= 55", alt.value("white"), alt.value(ENCRE)))
    return theme((cases + valeurs).properties(height=38 * len(t) + 30))


def barres_mises_en_avant(donnees, x, y, seuil, titre_y, fmt=".1f", tri=None, horizontal=False):
    """Barres grises, les valeurs au-dessus du seuil en orange, valeur ecrite au bout."""
    couleur = alt.condition(f"datum['{y}'] >= {seuil}", alt.value(ORANGE), alt.value(NEUTRE))
    if horizontal:
        base = alt.Chart(donnees).encode(y=alt.Y(f"{x}:N", sort=tri, title=None, axis=alt.Axis(labelLimit=220)),
                                         x=alt.X(f"{y}:Q", title=titre_y))
        barres = base.mark_bar(cornerRadiusEnd=4, height=20).encode(color=couleur, tooltip=[x, alt.Tooltip(f"{y}:Q", format=fmt)])
        texte = base.mark_text(align="left", dx=5, color=ENCRE, fontSize=12).encode(text=alt.Text(f"{y}:Q", format=fmt))
        return theme((barres + texte).properties(height=34 * len(donnees) + 40))
    base = alt.Chart(donnees).encode(x=alt.X(f"{x}:N", sort=tri, title=None, axis=alt.Axis(labelAngle=0)),
                                     y=alt.Y(f"{y}:Q", title=titre_y))
    barres = base.mark_bar(cornerRadiusEnd=4).encode(color=couleur, tooltip=[x, alt.Tooltip(f"{y}:Q", format=fmt)])
    return theme(barres.properties(height=300))


# -------------------------------------------------------------------- chargement
@st.cache_data(show_spinner="Contrôle et nettoyage des fichiers…")
def charger(fichiers):
    return N.nettoyer(list(fichiers))


@st.cache_data(show_spinner="Calcul des analyses…")
def analyser(fichiers, grippe_octets):
    r = charger(fichiers)
    verdict, infos_prev = A.prevision(r)
    return {
        "resume": A.resume(r), "jour": A.indice_jour(r), "heure": A.part_heure(r), "mois": A.indice_mois(r),
        "annuel": A.annuel(r), "verdict": verdict, "infos_prev": infos_prev,
        "grippe": A.grippe(r, A.lire_sentinelles(grippe_octets)),
    }


def fichiers_exemple():
    return tuple((p.name, p.read_bytes()) for p in sorted(EXEMPLE.glob("*.csv")))


# ----------------------------------------------------------------- barre laterale
with st.sidebar:
    st.header("Vos fichiers")
    deposes = st.file_uploader("Déposez les 4 exports du logiciel de caisse", type=["csv"], accept_multiple_files=True,
                               help="Les exports par heure, par jour, par semaine et par mois. L'ordre n'a pas d'importance.")
    exemple_possible = EXEMPLE.exists() and len(list(EXEMPLE.glob("*.csv"))) >= 4
    exemple = st.checkbox("Utiliser les exports d'exemple", value=False, disabled=not exemple_possible,
                          help="Pour essayer l'application sans déposer de fichier.")
    with st.expander("Données sur la grippe (facultatif)"):
        st.caption("Par défaut, l'application utilise le fichier du réseau Sentinelles fourni avec le projet. "
                   "Vous pouvez en déposer un plus récent (sentiweb.fr, syndromes grippaux, France entière).")
        grippe_depose = st.file_uploader("Fichier Sentinelles", type=["csv"], label_visibility="collapsed")
    st.divider()
    st.caption("Vos fichiers restent sur cet ordinateur : rien n'est envoyé sur Internet ni enregistré.")

fichiers = tuple((f.name, f.getvalue()) for f in deposes) if deposes else (fichiers_exemple() if exemple else ())

st.title("Ventes de la pharmacie")

# ----------------------------------------------------------------------- accueil
if not fichiers:
    st.write("Déposez vos exports de ventes pour obtenir les contrôles, les statistiques et les graphiques à jour.")
    a, b, c = st.columns(3)
    with a:
        st.subheader("1. Exporter")
        st.write("Depuis le logiciel de caisse, exportez les ventes par heure, par jour, par semaine et par mois.")
    with b:
        st.subheader("2. Déposer")
        st.write("Glissez les quatre fichiers dans le cadre « Vos fichiers », à gauche.")
    with c:
        st.subheader("3. Consulter")
        st.write("Les contrôles et les analyses s'affichent seuls. Vous pouvez ensuite télécharger un classeur Excel.")
    st.info("Pour essayer sans fichier, cochez « Utiliser les exports d'exemple » dans le panneau de gauche.")
    st.stop()

try:
    r = charger(fichiers)
    calculs = analyser(fichiers, grippe_depose.getvalue() if grippe_depose else None)
except N.ErreurExport as e:
    st.error(f"Les fichiers n'ont pas pu être utilisés. {e}")
    st.markdown("**À vérifier :**\n"
                "- les quatre exports sont bien déposés (heure, jour, semaine, mois) ;\n"
                "- ce sont des fichiers CSV sortis du logiciel de caisse, non modifiés ;\n"
                "- chacun contient une colonne de date nommée « datum » et les mêmes groupes de médicaments.")
    st.stop()
except Exception as e:  # dernier filet : jamais d'ecran d'erreur technique
    st.error("Une erreur inattendue s'est produite pendant l'analyse des fichiers.")
    with st.expander("Détail technique (à transmettre à l'équipe)"):
        st.code(f"{type(e).__name__}: {e}")
    st.stop()

infos, G = r.infos, r.groupes
alertes = r.journal[r.journal["Niveau"] == "attention"]

# ---------------------------------------------------------------------- en-tete
k1, k2, k3, k4 = st.columns(4)
k1.metric("Période couverte", f"{infos['debut']:%m/%Y} – {infos['fin']:%m/%Y}",
          help=f"Du {infos['debut']:%d/%m/%Y} au {infos['fin']:%d/%m/%Y}")
k2.metric("Dernier mois complet", N.mois_annee(infos["dernier_mois_complet"]).capitalize())
k3.metric("Groupes de médicaments", len(G))
k4.metric("Points à vérifier", len(alertes))
if len(alertes):
    st.warning(f"{len(alertes)} point(s) à vérifier dans les fichiers. Le détail est dans l'onglet « Fiabilité des données ».")
else:
    st.success("Les quatre exports sont cohérents entre eux.")

onglet_cmd, onglet_org, onglet_fiab, onglet_dl = st.tabs(
    ["Commandes", "Organisation de la pharmacie", "Fiabilité des données", "Télécharger"])

# ===================================================================== COMMANDES
with onglet_cmd:
    st.subheader("Consulter les ventes")
    st.caption("Choisissez un ou plusieurs groupes et une période. Pour un seul jour, choisissez deux fois la même date.")
    c1, c2 = st.columns([3, 2])
    choix = c1.multiselect("Groupes de médicaments", G, default=G[:1], placeholder="Choisir un ou plusieurs groupes")
    fin_defaut = infos["dernier_mois_complet"].date()
    periode = c2.date_input("Période", value=(fin_defaut.replace(day=1), fin_defaut), min_value=infos["debut"].date(),
                            max_value=infos["fin"].date(), format="DD/MM/YYYY")
    if not choix:
        st.info("Choisissez au moins un groupe de médicaments.")
    elif not isinstance(periode, (tuple, list)) or len(periode) != 2:
        st.info("Choisissez la date de fin de la période.")
    else:
        debut, fin = periode
        sel = A.selection(r, choix, debut, fin)
        if sel.empty:
            st.info("Aucune vente enregistrée sur cette période.")
        else:
            n_incomplets = int((~sel["journee_complete"]).sum())
            if n_incomplets:
                st.warning(f"La période contient {n_incomplets} journée(s) incomplète(s) (début ou fin de l'export).")
            bilan = pd.DataFrame({"Total sur la période": sel[choix].sum(), "Moyenne par jour": sel[choix].mean(),
                                  "Jour le plus fort": sel[choix].max()})
            bilan.index.name = "Groupe"
            st.caption(f"{len(sel)} jour(s) du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}")
            tableau(bilan, {"Total sur la période": "{:,.1f}", "Moyenne par jour": "{:,.1f}", "Jour le plus fort": "{:,.1f}"})

            serie = sel.set_index("date")[choix]
            pas, libelle = ("D", "par jour") if len(sel) <= 92 else (("W-SUN", "par semaine") if len(sel) <= 730 else ("ME", "par mois"))
            if pas != "D":
                serie = serie.resample(pas).sum()
            for g in choix:
                st.markdown(f"**{N.nom_court(g)}** · quantité {libelle}")
                un = serie[[g]].rename(columns={g: "Quantité"}).reset_index()
                montre(theme(alt.Chart(un).mark_bar(color=BLEU, cornerRadiusEnd=2).encode(
                    x=alt.X("date:T", title=None, axis=alt.Axis(format="%d/%m/%y", labelAngle=0)),
                    y=alt.Y("Quantité:Q", title=None),
                    tooltip=[alt.Tooltip("date:T", format="%d/%m/%Y", title="Date"), alt.Tooltip("Quantité:Q", format=".1f")],
                ).properties(height=170)))
            st.caption("Quantités en unités du logiciel de caisse. Chaque groupe a sa propre échelle : "
                       "les groupes ne se comparent pas entre eux en volume.")

    st.divider()
    st.subheader("Les périodes à anticiper")
    st.caption("Indice par mois : 100 = un mois moyen pour le groupe. Orange : mois fort. Bleu : mois creux.")
    montre(carte_indices(calculs["mois"], MOIS_ABR, "Mois"))

    st.subheader("Les jours de la semaine")
    st.caption("Indice par jour : 100 = un jour moyen pour le groupe.")
    montre(carte_indices(calculs["jour"], [j.capitalize() for j in N.JOURS_FR], "Jour"))

    st.divider()
    st.subheader("Prévision du mois suivant")
    v, ip = calculs["verdict"], calculs["infos_prev"]
    if v is None:
        st.info(ip)
    else:
        oui = v[v["Prévisible ?"] == "Oui"]
        st.caption(f"Prévision pour {ip['prochain']}, à partir des données jusqu'à {ip['dernier']}. "
                   f"Seuls les groupes où la prévision a fait ses preuves sur {ip['n_test']} mois sont affichés.")
        if oui.empty:
            st.info("Aucun groupe ne se prévoit mieux qu'en reprenant simplement le chiffre du mois précédent.")
        else:
            for col, (g, ligne) in zip(st.columns(max(len(oui), 3)), oui.iterrows()):
                col.metric(N.nom_court(g), fr(ligne["Prévision"]), f"± {fr(ligne['Erreur du modèle'])}", delta_color="off")
        autres = [N.nom_court(g) for g in v.index[v["Prévisible ?"] == "Non"]]
        if autres:
            st.caption("Sans prévision fiable : " + ", ".join(autres) + ". Pour ces groupes, repartir des ventes du mois précédent.")

    with st.expander("Régularité des ventes et marge de stock"):
        st.caption("Un coefficient de variation élevé ou beaucoup de jours sans vente signalent un groupe difficile à anticiper. "
                   "« Besoin 1 jour sur 20 » : quantité dépassée seulement un jour sur vingt.")
        tableau(calculs["resume"], {c: "{:,.1f}" for c in calculs["resume"].columns} | {"Régularité (coef. de variation)": "{:,.2f}"})

# ================================================================== ORGANISATION
with onglet_org:
    st.subheader("Les heures chargées de la journée")
    heures = calculs["heure"].mean().rename("Part").reset_index()
    heures["Heure"] = heures["heure"].astype(int).astype(str) + " h"
    seuil_h = heures["Part"].nlargest(max(1, len(heures) // 3)).min()
    fortes = heures.loc[heures["Part"] >= seuil_h, "Heure"].tolist()
    st.caption("Part de chaque heure dans les ventes de la journée, en moyenne sur les groupes. "
               f"En orange, les heures les plus chargées : {', '.join(fortes)}.")
    montre(barres_mises_en_avant(heures, "Heure", "Part", seuil_h, "Part des ventes de la journée (%)", tri=heures["Heure"].tolist()))
    st.caption("L'export ne couvre que ces groupes de médicaments : une heure calme ici ne l'est pas forcément pour toute la pharmacie.")

    st.divider()
    st.subheader("Les ventes et la grippe")
    if calculs["grippe"] is None:
        st.info("Comparaison indisponible : le fichier du réseau Sentinelles est absent ou ne couvre pas la période des exports. "
                "Vous pouvez en déposer un dans le panneau de gauche.")
    else:
        tg, _, n_fortes = calculs["grippe"]
        dg = tg["Écart (%)"].rename("Écart").reset_index()
        dg["Groupe"] = dg["Groupe"].map(N.nom_court)
        dg = dg.sort_values("Écart", ascending=False)
        lies = dg.loc[dg["Écart"] >= 15, "Groupe"].tolist()
        st.caption(f"Ventes des semaines de forte grippe ({n_fortes} semaines à {A.SEUIL_GRIPPE} cas ou plus pour 100 000 habitants) "
                   "comparées aux autres semaines. Source : réseau Sentinelles, France entière.")
        montre(barres_mises_en_avant(dg, "Groupe", "Écart", 15, "Écart par rapport à une semaine normale (%)",
                                     fmt="+.0f", tri=dg["Groupe"].tolist(), horizontal=True))
        if lies:
            st.success("Dépendent de l'environnement : " + ", ".join(lies) + ". Suivre le bulletin hebdomadaire Sentinelles "
                       "permet de commander avant la hausse.")
        st.caption("Deux courbes qui montent ensemble ne prouvent pas que l'une cause l'autre : le froid peut jouer aussi. "
                   "Une baisse (antihistaminiques) reflète la saison, pas la grippe.")

    st.divider()
    st.subheader("Partager les données : quel niveau de détail ?")
    sensibles = [g for g in G if "N05B" in g or "N05C" in g]
    choisis = st.multiselect("Groupes sensibles à examiner", G, default=sensibles or G[:2], max_selections=3,
                             help="Par défaut : anxiolytiques et somnifères.")
    if choisis:
        iso = A.ventes_isolees(r, choisis)
        ordre = ["Heure", "Jour", "Semaine", "Mois"]
        st.caption(f"Part des périodes avec vente qui comptent {A.SEUIL_ISOLE} unités ou moins. Plus cette part est élevée, "
                   "plus une vente peut désigner une personne.")
        base = alt.Chart(iso).encode(
            x=alt.X("Niveau:N", sort=ordre, title="Niveau de détail des données partagées", axis=alt.Axis(labelAngle=0)),
            xOffset=alt.XOffset("Groupe:N", sort=[N.nom_court(g) for g in choisis]),
            y=alt.Y("Part (%):Q", scale=alt.Scale(domain=[0, 100]), title="Part des ventes isolées (%)"))
        barres = base.mark_bar(cornerRadiusEnd=4).encode(
            color=alt.Color("Groupe:N", sort=[N.nom_court(g) for g in choisis],
                            scale=alt.Scale(range=[BLEU, ORANGE, "#1baf7a"][:len(choisis)]), legend=alt.Legend(title=None, orient="top")),
            tooltip=["Niveau", "Groupe", alt.Tooltip("Part (%):Q", format=".0f")])
        etiquettes = base.mark_text(dy=-8, color=ENCRE, fontSize=12).encode(text=alt.Text("Part (%):Q", format=".0f"))
        montre(theme((barres + etiquettes).properties(height=320)))
        risque = iso[iso["Niveau"].isin(["Heure", "Jour", "Semaine"])]["Part (%)"].max()
        if risque >= 20:
            st.warning("Au niveau de l'heure, du jour ou de la semaine, des ventes isolées peuvent révéler l'achat d'une personne. "
                       "Ne partager que des chiffres par mois, après avis de l'Ordre des pharmaciens ou d'un juriste.")

# ====================================================================== FIABILITE
with onglet_fiab:
    st.subheader("Contrôle des fichiers reçus")
    icones = {"ok": "✅ Conforme", "info": "ℹ️ À savoir", "attention": "⚠️ À vérifier"}
    journal = r.journal.assign(Niveau=r.journal["Niveau"].map(icones)).rename(columns={"Niveau": "Résultat"})
    tableau(journal[["Résultat", "Fichier", "Constat", "Action"]])

    if len(r.ecarts):
        st.subheader("Mois où le mensuel du client diffère de la somme des jours")
        st.caption(f"{infos['mois_en_ecart']} mois sur {infos['mois_compares']}. Plus grand écart du mois, tous groupes confondus. "
                   "Le mensuel du client est écarté et recalculé à partir du journalier.")
        tous = r.mensuel["date_fin_mois"]
        pire = r.ecarts.groupby("mois")["ecart_pct"].agg(lambda s: s.abs().max()).reindex(tous, fill_value=0)
        de = pd.DataFrame({"Mois": tous.values, "Écart (%)": pire.values})
        montre(theme(alt.Chart(de).mark_bar(color=ORANGE, cornerRadiusEnd=2).encode(
            x=alt.X("yearmonth(Mois):T", title=None, axis=alt.Axis(format="%Y", labelAngle=0, tickCount="year")),
            y=alt.Y("Écart (%):Q", title="Plus grand écart du mois (%)"),
            tooltip=[alt.Tooltip("yearmonth(Mois):T", title="Mois", format="%m/%Y"), alt.Tooltip("Écart (%):Q", format=".1f")],
        ).properties(height=280)))

    st.subheader("Test de la prévision")
    if v is None:
        st.info(ip)
    else:
        st.caption(f"Chacun des {ip['n_test']} derniers mois est prévu avec les seuls mois qui le précèdent, puis comparé au réel. "
                   f"« Oui » si le modèle réduit l'erreur d'au moins {round(100 * (1 - A.SEUIL_PREVISION))} % par rapport à la "
                   "meilleure prévision simple (« comme le mois dernier » ou « comme le même mois l'an dernier »).")
        tableau(v.rename(columns={"Prévision": f"Prévision {ip['prochain']}"}),
                {"Ventes moyennes par mois": "{:,.0f}", "Erreur du modèle": "{:,.1f}", "Erreur de la référence simple": "{:,.1f}",
                 "Rapport": "{:,.2f}", f"Prévision {ip['prochain']}": "{:,.0f}"})

    if calculs["annuel"] is not None:
        st.subheader("Évolution par année complète")
        tableau(calculs["annuel"], {c: ("{:+,.1f}" if "Évolution" in c else "{:,.0f}") for c in calculs["annuel"].columns})

    st.caption("Limites : l'unité des quantités n'est pas documentée et l'export ne contient aucun prix. "
               "Aucun résultat n'est exprimé en euros.")

# ================================================================== TELECHARGER
with onglet_dl:
    st.subheader("Emporter les résultats")
    feuilles = {"Résumé par groupe": calculs["resume"], "Indice par mois": calculs["mois"], "Indice par jour": calculs["jour"],
                "Part par heure (%)": calculs["heure"], "Par année": calculs["annuel"], "Prévision": calculs["verdict"],
                "Grippe": calculs["grippe"][0] if calculs["grippe"] else None, "État des données": r.journal}
    try:
        st.download_button("Télécharger le classeur Excel des statistiques", A.classeur(r, feuilles),
                           file_name=f"statistiques_pharmacie_{infos['fin']:%Y-%m-%d}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
    except Exception:
        st.info("Le classeur Excel n'a pas pu être préparé (bibliothèque xlsxwriter absente).")
    st.download_button("Télécharger les ventes journalières nettoyées (CSV)",
                       r.journalier.to_csv(index=False, date_format="%Y-%m-%d").encode("utf-8-sig"),
                       file_name="ventes_journalier_nettoye.csv", mime="text/csv")
    st.caption("Le classeur contient les tableaux de chiffres et l'état des données. "
               "Les fichiers téléchargés sont créés sur cet ordinateur.")
