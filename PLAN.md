# Rush 2 – Plan pour terminer le projet

Document de travail du groupe. **À ne pas livrer** : le sujet demande que le dépôt ne contienne rien d'inutile au client ou au manager. À supprimer avant le rendu.

Chaque étape est décrite de la même façon : **pourquoi** on la fait (ce que le sujet exige), **ce qu'il faut faire** (dans l'ordre), **ce qu'on obtient**, et **c'est fini quand**.

## Où on en est

| Étape | Livrable | État |
|---|---|---|
| – | Nettoyage des 4 exports (`nettoyage.py`) | Fait |
| – | Noms des groupes (`data/ref/atc.csv`) | Fait, libellés à vérifier sur l'index ATC/DDD de l'OMS |
| 1 | Dépôt propre | Presque : reste `package-lock.json` à supprimer |
| 2 | Statistiques descriptives (`statistiques.ipynb`) | 5 cellules faites ; reste les conclusions en texte |
| 3 | Donnée publique externe (`externe.ipynb`) | Donnée téléchargée, code prêt ; notebook en cours |
| 4 | Test de prévision | À faire |
| 5 | Classeur Excel | À faire |
| 6 | Mémo PDF | À faire |
| 7 | 3 decks de 5 slides | À faire |
| 8 | README et répétition | README vide |

## Ce que le nettoyage a déjà établi

À réutiliser dans le classeur, le mémo et le deck manager.

- Les exports horaire, journalier et hebdomadaire concordent entre eux.
- L'export **mensuel du client est écarté** : 31 mois sur 70 ne correspondent pas à la somme des jours. Le mensuel est reconstruit depuis le journalier.
- Dernier mois complet : **septembre 2019**. Octobre 2019 ne contient que 8 jours, janvier 2014 n'a pas le 1er janvier.
- Pharmacie ouverte de 7 h à 22 h ; aucune vente de 23 h à 6 h.
- 9 valeurs extrêmes repérées et marquées, jamais supprimées.
- Quantités non entières (0,33 ; 3,67) : unité non documentée.
- **Ni prix ni unité dans l'export** : aucune conclusion en euros ou en marge, tout se dit en quantités.

---

## Étape 1 – Assainir le dépôt

**Pourquoi.** Le sujet dit : « le code doit tourner depuis une copie fraîche » et « le dépôt ne contient rien dont le client ou le manager n'a pas besoin ». Le dépôt lui-même est noté.

**Ce qu'il faut faire.**

1. Supprimer `package-lock.json` : il vient d'une commande `npm` lancée par erreur et n'a rien à faire dans un projet Python.
2. Vérifier que `requirements.txt` contient bien `pandas`, `numpy`, `jupyter` (et plus tard les bibliothèques ajoutées aux étapes 4 et 5).
3. Chacun commite sous son propre nom : l'historique doit montrer qui a fait quoi.
4. Avant de modifier un fichier partagé : `git pull`. Juste après : commit et `git push`. Une seule personne à la fois sur un même notebook.

**C'est fini quand** le dépôt ne contient que : `data/`, `nettoyage.py`, les notebooks, `requirements.txt`, `README.md`, et à la fin les livrables.

---

## Étape 2 – Statistiques descriptives (`statistiques.ipynb`)

**Pourquoi.** Le sujet demande « les statistiques descriptives qui soutiennent vos conclusions » et précise « vous choisissez lesquelles comptent ». Chaque statistique doit donc servir une décision d'un des trois interlocuteurs.

**Ce qui est fait.** Cinq cellules :

| Cellule | Ce qu'elle calcule | À quoi elle sert | Pour qui |
|---|---|---|---|
| Résumé par groupe | Total, moyenne et médiane par jour, écart-type, part des jours à zéro, coefficient de variation | Savoir ce qui se vend et si c'est régulier | Pharmacien acheteur |
| Jour de semaine | Indice par jour (100 = jour moyen du groupe) | Savoir quels jours renforcer le stock et l'équipe | Pharmacien acheteur, propriétaire |
| Heure | Part de chaque heure dans les ventes de la journée | Repérer les pics et les heures creuses, discuter les horaires | Propriétaire |
| Saisonnalité | Indice par mois (100 = mois moyen du groupe) | Savoir quelles périodes de l'année anticiper | Pharmacien acheteur |
| Tendance annuelle | Total par année complète (2015-2018) et évolution en % | Savoir quels groupes montent ou baissent | Propriétaire, manager |

**Le code des cinq cellules.**

Cellule 1 – Résumé par groupe (crée `d` et `groupes`, à exécuter en premier) :

```python
import pandas as pd

d = pd.read_csv("data/clean/ventes_journalier.csv", encoding="utf-8-sig", parse_dates=["date"])
d = d[d["journee_complete"]]                         # on ecarte les 2 journees tronquees
groupes = [c for c in d.columns if c.endswith(")")]  # les 8 colonnes "Nom (code)"

resume = pd.DataFrame({
    "total": d[groupes].sum(),
    "moyenne_jour": d[groupes].mean(),
    "mediane_jour": d[groupes].median(),
    "ecart_type": d[groupes].std(),
    "jours_a_zero_%": 100 * (d[groupes] == 0).mean(),
})
resume["coef_variation"] = resume["ecart_type"] / resume["moyenne_jour"]
display(resume.round(2))
```

Cellule 2 – Jour de semaine :

```python
ordre = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
par_jour = d.groupby("jour_semaine")[groupes].mean().loc[ordre]
indice_jour = 100 * par_jour / d[groupes].mean()     # 100 = jour moyen du groupe
display(indice_jour.round(0).T)
```

Cellule 3 – Heure :

```python
h = pd.read_csv("data/clean/ventes_horaire.csv", encoding="utf-8-sig", parse_dates=["date"])
h = h[h["heure_ouverture"] & h["date"].dt.normalize().isin(d["date"])]   # heures ouvertes, journees completes
par_heure = h.groupby("heure")[groupes].mean()
part_heure = 100 * par_heure / par_heure.sum()       # part de chaque heure dans la journee, en %
display(part_heure.round(1).T)
```

Cellule 4 – Saisonnalité :

```python
m = pd.read_csv("data/clean/ventes_mensuel.csv", encoding="utf-8-sig", parse_dates=["date_fin_mois"])
m = m[m["mois_complet"]]
par_mois = m.groupby(m["date_fin_mois"].dt.month)[groupes].mean()
indice_mois = 100 * par_mois / par_mois.mean()       # 100 = mois moyen du groupe
indice_mois.index.name = "mois"
display(indice_mois.round(0).T)
```

Cellule 5 – Tendance annuelle :

```python
annuel = d[d["annee"].between(2015, 2018)].groupby("annee")[groupes].sum()   # annees completes
evolution = 100 * (annuel.loc[2018] / annuel.loc[2015] - 1)
display(annuel.round(0).T.assign(evolution_2015_2018_pct=evolution.round(1)))
```

**Ce qu'il reste à faire.**

1. Sous chaque cellule, ajouter une cellule de texte (« + Markdown ») avec deux ou trois phrases de conclusion. Sans cela, le manager voit des tableaux sans savoir quoi en penser.
2. Faire « Restart » puis « Run All » : les cinq cellules doivent s'enchaîner sans erreur.
3. Commit et push.

**Résultats à retenir pour les decks.**

- Résumé : le paracétamol domine (30 unités par jour, les autres entre 0,6 et 9). Les somnifères ne se vendent pas deux jours sur trois.
- Jour : anxiolytiques et somnifères chutent le dimanche (65 et 53) ; paracétamol et anti-inflammatoires montent le week-end (111 à 119).
- Heure : deux pics, vers 10 h-12 h et 18 h-20 h ; 7 h et 22 h pèsent moins de 1 % chacune.
- Saison : antihistaminiques au printemps (179 en mai) ; antiasthmatiques et paracétamol forts en hiver, creux en été.
- Tendance : antiasthmatiques et somnifères environ +52 %, antihistaminiques +21 %, aspirine -30 %.

**Réserves à dire à l'oral.**

- L'année 2017 est basse (paracétamol : 9 484 contre 13 544 en 2016). Vérifié : ce n'est pas un trou dans les données, aucun jour ne manque. La cause est inconnue : question à poser au client.
- On ne compare pas les groupes entre eux en volume : l'unité n'est pas documentée.
- L'export ne couvre que 8 groupes : une heure creuse pour eux ne l'est pas forcément pour toute la pharmacie.

**C'est fini quand** « Run All » passe sans erreur et que chaque tableau a sa conclusion écrite.

---

## Étape 3 – Donnée externe (`externe.ipynb`)

**Pourquoi.** Le propriétaire se demande « quelle part de ce qui se passe dans la boutique est due à la pharmacie elle-même, et quelle part à son environnement ». Le sujet impose donc :

- d'aller chercher soi-même une donnée dans une **source publique et structurée** (un fichier de données, pas un article) ;
- de l'**intégrer à l'analyse** : la citer sur une slide ne suffit pas, elle doit être croisée avec les ventes ;
- d'en tirer **au moins une recommandation**.

**L'idée, en clair.** On prend une mesure de ce qui se passe hors de la pharmacie, par exemple le nombre de cas de grippe en France chaque semaine. On la met côte à côte avec les ventes de la pharmacie, semaine par semaine. Si les deux courbes montent et descendent ensemble, alors les ventes dépendent de l'environnement (l'épidémie) et non de la façon dont la pharmacie travaille. C'est la réponse à la question du propriétaire.

**Les sources possibles.**

| Source | Ce qu'elle contient | Ce qu'on en fait | Priorité |
|---|---|---|---|
| Réseau Sentinelles (sentiweb.fr) | Nombre de cas de syndromes grippaux en France, par semaine | Le croiser avec les ventes de paracétamol et d'antiasthmatiques | 1 |
| Jours fériés et vacances scolaires (data.gouv.fr) | Calendrier officiel | Voir si les ventes baissent ces jours-là | 2 |
| Open Medic (Assurance Maladie) | Médicaments remboursés en France par code ATC | Comparer la tendance de la pharmacie à celle du pays | 3 |

Une seule source bien exploitée suffit. Commencer par Sentinelles.

**Ce qu'il faut faire.**

1. **Télécharger** le fichier des syndromes grippaux, niveau France entière, sur le site du réseau Sentinelles. Vérifier qu'il couvre 2014 à 2019 et noter le nom des colonnes (semaine, incidence).
2. **L'enregistrer dans le dépôt**, dans `data/externe/`. Le code doit tourner depuis une copie fraîche, même sans Internet.
3. **Noter la source** : adresse de téléchargement et date, dans le notebook et plus tard dans le classeur.
4. **Charger** ce fichier et `data/clean/ventes_hebdo.csv` dans un nouveau notebook.
5. **Aligner les semaines.** Dans nos ventes, chaque semaine est repérée par son dimanche de fin. Il faut ramener le fichier externe au même repère pour pouvoir joindre les deux tables.
6. **Écarter** les deux semaines incomplètes (`semaine_complete` à Faux).
7. **Calculer la corrélation** entre l'incidence de la grippe et les ventes de chaque groupe. C'est un chiffre entre -1 et 1 : proche de 1 = les deux bougent ensemble, proche de 0 = aucun lien.
8. **Tracer un graphique** : ventes de paracétamol et cas de grippe sur le même axe de temps.
9. **Écrire la conclusion et la recommandation.**

**Déjà fait.** Les points 1 à 3 : le fichier est dans `data/externe/sentinelles_syndromes_grippaux.csv`, téléchargé le 09/10/2026 depuis `https://www.sentiweb.fr/datasets/all/inc-3-PAY.csv`. Il couvre 2014-2019. `matplotlib` est ajouté à `requirements.txt` : après un `git pull`, relancer `venv\Scripts\python -m pip install -r requirements.txt`.

**Le code des cinq cellules** (`externe.ipynb`, à la racine).

Cellule 1 – Charger la donnée grippe (crée `s`, à exécuter en premier) :

```python
import pandas as pd
import matplotlib.pyplot as plt

# Source : reseau Sentinelles (INSERM, Sorbonne Universite), syndromes grippaux, France entiere
# https://www.sentiweb.fr/datasets/all/inc-3-PAY.csv  (telecharge le 09/10/2026)
s = pd.read_csv("data/externe/sentinelles_syndromes_grippaux.csv", comment="#", encoding="latin-1")
s["date_fin_semaine"] = pd.to_datetime(s["week"].astype(str) + "7", format="%G%V%u")   # semaine -> dimanche de fin
s["grippe"] = pd.to_numeric(s["inc100"], errors="coerce")   # cas pour 100 000 habitants
s = s[["date_fin_semaine", "grippe"]]
display(s.head())
```

Cellule 2 – Joindre aux ventes (crée `x`, utilisé par toutes les suivantes) :

```python
w = pd.read_csv("data/clean/ventes_hebdo.csv", encoding="utf-8-sig", parse_dates=["date_fin_semaine"])
w = w[w["semaine_complete"]]
groupes = [c for c in w.columns if c.endswith(")")]
x = w.merge(s, on="date_fin_semaine", how="left")
print(len(x), "semaines ;", x["grippe"].isna().sum(), "sans donnee grippe")
```

Doit afficher `300 semaines ; 0 sans donnee grippe`.

Cellule 3 – Corrélation par groupe :

```python
corr = x[groupes].corrwith(x["grippe"])
tableau = pd.DataFrame({"correlation": corr.round(2),
                        "part_expliquee_%": (100 * corr**2).round(0)})
display(tableau.sort_values("correlation", ascending=False))
```

Cellule 4 – Semaines de forte grippe contre les autres :

```python
x["forte_grippe"] = x["grippe"] >= 150      # seuil choisi par nous : 51 semaines sur 300
comp = x.groupby("forte_grippe")[groupes].mean().T
comp.columns = ["semaine_normale", "semaine_forte_grippe"]
comp["ecart_%"] = (100 * (comp["semaine_forte_grippe"] / comp["semaine_normale"] - 1)).round(0)
display(comp.round(1))
```

Cellule 5 – Graphique :

```python
para = [g for g in groupes if "N02BE" in g][0]
fig, (haut, bas) = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
haut.plot(x["date_fin_semaine"], x[para])
haut.set_ylabel("Ventes par semaine")
haut.set_title(f"{para} : ventes de la pharmacie")
bas.plot(x["date_fin_semaine"], x["grippe"], color="tab:red")
bas.set_ylabel("Cas pour 100 000 habitants")
bas.set_title("Syndromes grippaux en France (réseau Sentinelles)")
plt.tight_layout()
plt.show()
```

**Ce qu'on obtient.**

| Groupe | Corrélation | Semaine normale | Semaine de forte grippe | Écart |
|---|---|---|---|---|
| Paracétamol (N02BE) | 0,42 | 197,6 | 287,8 | +46 % |
| Antiasthmatiques (R03) | 0,29 | 36,3 | 52,3 | +44 % |
| AINS propioniques (M01AE) | 0,39 | 26,5 | 33,6 | +27 % |
| Aspirine et dérivés (N02BA) | 0,24 | 26,5 | 30,9 | +17 % |
| Anxiolytiques (N05B) | 0,09 | 61,1 | 65,4 | +7 % |
| Somnifères (N05C) | 0,03 | 4,1 | 4,3 | +3 % |
| AINS acétiques (M01AB) | 0,01 | 35,6 | 36,0 | +1 % |
| Antihistaminiques (R06) | -0,32 | 22,1 | 12,7 | -43 % |

**Les conclusions à écrire.**

- Quatre groupes dépendent de l'environnement : paracétamol, antiasthmatiques, anti-inflammatoires propioniques et aspirine se vendent nettement plus les semaines de forte grippe (+17 à +46 %).
- Trois groupes n'en dépendent pas : anxiolytiques, somnifères et anti-inflammatoires acétiques ne bougent presque pas.
- Les antihistaminiques baissent pendant la grippe parce que la grippe est en hiver et les allergies au printemps : ce n'est pas un effet de la grippe.

**La recommandation qui en découle** : suivre le bulletin hebdomadaire Sentinelles et relever les commandes de paracétamol et d'antiasthmatiques dès que l'épidémie démarre, au lieu d'attendre de voir les ventes monter.

**Réserves à dire à l'oral.**

- Le lien est réel mais partiel : la grippe n'explique que 17 % des variations du paracétamol. Les ventes montent dès l'automne, avant le pic de grippe de janvier-février : d'autres causes hivernales jouent.
- On ne sait pas où est la pharmacie : la donnée est nationale, pas locale. Avec la région du client, l'analyse serait plus précise (argument pour une mission de suivi).
- Deux courbes qui bougent ensemble ne prouvent pas que l'une cause l'autre : le froid peut faire monter les deux.
- Le seuil de 150 cas pour 100 000 est notre choix pour séparer les semaines, pas un seuil officiel.

**C'est fini quand** le notebook tourne depuis une copie fraîche, que le fichier externe est dans le dépôt avec sa source, et que la recommandation est écrite.

---

## Étape 4 – Test de prévision (`prevision.ipynb`)

**Pourquoi.** Le manager pose une question précise avant de signer une mission de suivi : « ces données permettent-elles de prévoir, pour chaque groupe, les ventes du mois qui suit le dernier mois complet ? ». Le dernier mois complet est septembre 2019, donc il s'agit de prévoir octobre 2019. Le sujet exige :

- un **vrai test** : des prévisions confrontées à des mois qui n'ont pas servi à les construire ;
- une comparaison avec **la prévision la plus simple** que n'importe qui ferait sans nous ;
- « l'allure d'une courbe n'est pas un test ».

« Oui », « non » ou « pour certains groupes seulement » sont tous acceptés, à condition d'être prouvés.

**L'idée, en clair.** On fait semblant d'être dans le passé. On se place fin septembre 2017, on prévoit octobre 2017 avec uniquement ce qu'on connaissait alors, puis on regarde ce qui s'est réellement vendu. On recommence pour chaque mois jusqu'à septembre 2019. On obtient 24 prévisions et 24 erreurs par groupe. On fait pareil avec une méthode « bête ». Si notre méthode ne se trompe pas moins que la méthode bête, elle ne sert à rien.

**Ce qu'il faut faire.**

1. **Charger** `data/clean/ventes_mensuel.csv` et garder les mois complets (février 2014 à septembre 2019, 68 mois).
2. **Programmer deux prévisions naïves** :
   - « le mois prochain = ce mois-ci » ;
   - « le mois prochain = le même mois l'an dernier ».
3. **Programmer un modèle** : lissage exponentiel saisonnier (Holt-Winters, bibliothèque `statsmodels`), un par groupe. Ajouter `statsmodels` à `requirements.txt`.
4. **Faire le test glissant** sur les 24 derniers mois : à chaque fois, n'utiliser que les mois d'avant.
5. **Mesurer l'erreur** de chaque méthode : l'écart moyen entre prévu et réel (erreur absolue moyenne), par groupe.
6. **Construire le tableau de verdict** : pour chaque groupe, erreur du modèle, erreur de la meilleure méthode naïve, et le rapport entre les deux.
7. **Décider par groupe** : « oui » seulement si le modèle bat nettement la référence naïve.
8. **Donner la prévision d'octobre 2019** pour les groupes où la réponse est oui.

**Ce qu'on obtient.** Un tableau de 8 lignes qui est le cœur du mémo partie 1 et du deck manager.

**Ce à quoi s'attendre.** Probablement « pour certains groupes seulement » : les groupes très saisonniers (antihistaminiques, antiasthmatiques, paracétamol) ont plus de chances d'être prévisibles ; les somnifères, trop rares, sans doute pas.

**C'est fini quand** le tableau de verdict existe et que la réponse tient en une phrase par groupe.

---

## Étape 5 – Classeur Excel (`classeur.py` ou notebook)

**Pourquoi.** C'est le livrable principal pour le client. Le sujet exige :

- une **feuille de synthèse**, les **statistiques**, et un **état des données** (quel export sert à quoi, ce qui a été corrigé ou écarté) ;
- que les statistiques du classeur **viennent du code** : le manager relancera le code chaque mois sur les nouveaux exports ;
- un **outil de sélection** : le pharmacien choisit un ou plusieurs groupes et un jour ou une période, et voit les ventes. Dans Excel 365, **sans macro**, pour quelqu'un qui n'ouvrira jamais Python.

**Décision à prendre d'abord.**

| Option | Avantage | Inconvénient |
|---|---|---|
| Classeur généré entièrement en Python (recommandé) | Se régénère tout seul chaque mois | Outil un peu moins élégant |
| Tableau croisé dynamique avec segments, fait à la main | Plus joli, plus naturel dans Excel | À refaire ou à rafraîchir à la main ; le code ne le recrée pas |

**Ce qu'il faut faire (option recommandée).**

1. Ajouter `xlsxwriter` à `requirements.txt`.
2. Écrire un code qui crée le classeur avec ces feuilles :

| Feuille | Contenu | D'où ça vient |
|---|---|---|
| Synthèse | Chiffres clés et messages principaux | Étapes 2, 3 et 4 |
| Statistiques | Les cinq tableaux | Étape 2 |
| État des données | Journal du nettoyage + quel export sert à quoi | `data/clean/etat_des_donnees.csv` |
| Outil | Sélection et résultat | Formules Excel |
| Données | Ventes journalières | `data/clean/ventes_journalier.csv` |
| Référentiel | Codes ATC et noms | `data/ref/atc.csv` |

3. Construire la feuille **Outil** :
   - 8 cellules Oui/Non (liste déroulante), une par groupe ;
   - une cellule « date de début » et une « date de fin » (même date dans les deux = un seul jour) ;
   - des formules `SOMME.SI.ENS` qui affichent le total par groupe sélectionné sur la période.
4. Ouvrir le classeur dans Excel 365 et tester l'outil comme le ferait le pharmacien.
5. Retirer `data/clean/ventes_journalier_long.csv` et le bloc qui le crée dans `nettoyage.py` : il ne sert plus avec cette option.

**C'est fini quand** une personne du groupe qui n'a pas écrit le code relance tout, ouvre le classeur et utilise l'outil sans aide.

---

## Étape 6 – Mémo PDF

**Pourquoi.** Livrable écrit en deux parties, imposé par le sujet.

### Partie 1 – Réponse sur la prévision

**Ce qu'il faut faire.** Rédiger une page :

1. la question du manager ;
2. le protocole du test (étape 4), expliqué simplement ;
3. le tableau de verdict par groupe ;
4. la réponse, en une phrase.

### Partie 2 – Partage des données avec le laboratoire

**Pourquoi.** Un laboratoire propose de meilleures conditions d'achat contre l'accès à l'export. Certains groupes concernent l'anxiété et le sommeil. Le propriétaire veut savoir : quelqu'un qui connaît la pharmacie pourrait-il apprendre quelque chose sur une personne ? À quel niveau de détail ? Et à quoi d'autre, au-delà de la protection des données, l'accord l'expose-t-il ?

**Ce qu'il faut faire.**

1. **Mesurer le risque dans nos propres données**, par niveau de détail. Compter, pour les anxiolytiques et les somnifères, combien d'heures et de jours n'ont qu'une ou deux ventes. C'est ce qui rend l'analyse concrète.
2. **Expliquer le scénario** : à l'heure, les somnifères se vendent à l'unité. Quelqu'un qui a vu un voisin entrer à 9 h peut en déduire son achat. Au mois, les ventes sont noyées dans le total.
3. **Qualifier juridiquement** : l'export n'a pas de nom de patient, mais une donnée qui permet de retrouver une personne reste une donnée personnelle, et ici une donnée de santé.
4. **Traiter le « au-delà du RGPD »**, pistes à vérifier sur Légifrance et le site de la CNIL (citées de mémoire, ne pas les recopier sans contrôle) :
   - secret professionnel ;
   - indépendance du pharmacien (code de déontologie) ;
   - dispositif « anti-cadeaux » du Code de la santé publique ;
   - plafonnement des remises ;
   - dépendance commerciale envers le laboratoire ;
   - réutilisation ou revente des données par le laboratoire.
5. **Conclure par une recommandation** claire au propriétaire. Probable : partage mensuel au plus, jamais horaire ni journalier, avec un contrat qui encadre l'usage.

**C'est fini quand** le PDF tient en deux à quatre pages et que chaque référence juridique a été vérifiée à la source.

---

## Étape 7 – Trois decks de 5 slides

**Pourquoi.** Chaque interlocuteur a son deck, présenté à l'oral en 5 minutes. Le sujet prévient : « trois decks qui ne diffèrent que par leur titre seront traités comme un seul ». Ce qui change, c'est la décision que chacun doit prendre.

| Interlocuteur | Ce qu'il doit décider | Ce qu'on lui montre |
|---|---|---|
| Manager | L'analyse est-elle solide ? Peut-on vendre une suite ? | Contrôles faits, mensuel écarté, test de prévision, proposition de mission de suivi |
| Pharmacien acheteur | Quoi commander, et quand ? | Groupes, jours et périodes à anticiper ; démonstration de l'outil |
| Propriétaire | Que changer dans la pharmacie ? | Horaires, effectifs, stock saisonnier ; part de l'environnement ; réponse à l'offre du laboratoire |

**Ce qu'il faut faire.**

1. Pour chaque deck, écrire d'abord en une phrase la décision attendue.
2. Faire 5 slides au plus, une idée par slide, avec un titre qui est une conclusion.
3. Ne rien dire en euros : l'export n'a pas de prix.
4. Vérifier qu'aucune slide n'est identique d'un deck à l'autre.

**C'est fini quand** chaque deck se présente en 5 minutes chronométrées.

---

## Étape 8 – README et répétition

**Pourquoi.** Le sujet dit : « le README doit indiquer qui était responsable de quoi ».

**Ce qu'il faut faire.**

1. Écrire le README : objet du projet, comment installer et relancer le code, contenu du dépôt, qui a fait quoi.
2. Tester sur une copie fraîche : cloner le dépôt dans un nouveau dossier, installer, tout relancer.
3. Supprimer ce `PLAN.md`.
4. Répéter les trois oraux, chronomètre en main.

**C'est fini quand** le test sur copie fraîche passe et que les trois oraux tiennent en 5 minutes.

---

## Répartition proposée

| Personne | Code | Écrit | Deck et oral |
|---|---|---|---|
| A | Étapes 2 (fin) et 5 (classeur, outil) | README | Pharmacien acheteur |
| B | Étapes 3 et 4 (donnée externe, prévision) | Mémo partie 1 | Manager |
| C | Étape 1, relecture, test sur copie fraîche | Mémo partie 2 (juridique) | Propriétaire |

- B et C peuvent avancer sans attendre A.
- Le classeur (étape 5) dépend des étapes 2 à 4 : A en construit d'abord le squelette, puis y branche les résultats de B.

## Ordre de travail

1. Finir les étapes 1 et 2.
2. En parallèle : étape 3 (B), squelette du classeur (A), mémo partie 2 (C).
3. Étape 4 (B), puis fin du classeur (A).
4. Mémo partie 1, decks, README.
5. Test sur copie fraîche, puis répétition des oraux.

## Décisions à prendre en groupe

- Classeur généré en Python (recommandé) ou tableau croisé fait à la main ?
- Qui est A, B, C ?
