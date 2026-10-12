# Comprendre le code du projet

Ce document explique, pour chaque fichier de code, à quoi il sert, pourquoi on l'a fait et comment il fonctionne. Il sert à réviser avant l'oral. Fichier de travail : à ne pas livrer dans le dépôt.

## 1. La logique d'ensemble

Le projet est une chaîne. Chaque étape utilise ce que la précédente a produit.

```
data/raw/            les 4 exports du client (on n'y touche jamais)
     |
     v
nettoyage.py         vérifie les exports et écrit des fichiers propres
     |
     v
data/clean/          les données nettoyées, avec les vrais noms des médicaments
     |
     +--> statistiques.ipynb   qu'est-ce qui se vend, quand ?
     +--> externe.ipynb        les ventes suivent-elles la grippe ?
     +--> prevision.ipynb      peut-on prévoir le mois suivant ?
     +--> controle.ipynb       graphique : le fichier mensuel du client est faux
     +--> partage.ipynb        graphique : risque de donner les données au laboratoire
     +--> classeur.ipynb       fabrique le classeur Excel pour le client
```

**Pourquoi cette organisation.** Le sujet dit que le client renverra ses quatre fichiers chaque mois et que le manager veut relancer le code sans tout refaire à la main. Donc :

- on ne modifie jamais les fichiers du client (`data/raw/`) ;
- tout ce qui est calculé vient du code, rien n'est tapé à la main dans Excel ;
- pour mettre à jour, il suffit de remplacer les 4 exports, de relancer `nettoyage.py`, puis `classeur.ipynb`.

**L'ordre compte.** Le nettoyage d'abord, toujours. Les notebooks lisent `data/clean/`, pas `data/raw/`.

## 2. Les dossiers de données

| Dossier | Contenu | D'où ça vient |
|---|---|---|
| `data/raw/` | Les 4 exports : par heure, jour, semaine, mois | Le client |
| `data/ref/atc.csv` | Le tableau code ATC → nom du groupe | Écrit par nous |
| `data/clean/` | Les fichiers nettoyés | Créés par `nettoyage.py` |
| `data/externe/` | Les cas de grippe en France par semaine | Téléchargé sur le site du réseau Sentinelles |

**Les codes ATC.** Dans l'export, les médicaments sont nommés par des codes (`N02BE`, `N05B`…). C'est une classification internationale de l'OMS. On a créé `atc.csv` pour traduire : `N02BE` devient « Paracétamol (N02BE) ». On garde le code entre parenthèses pour pouvoir toujours retrouver l'original. Ce sont des **groupes** de médicaments : on ne sait pas quelles boîtes précises ont été vendues.

## 3. `nettoyage.py` – vérifier et nettoyer

**À quoi il sert.** Le sujet prévient : les quatre fichiers ont été produits à des moments différents et personne n'a vérifié qu'ils sont d'accord entre eux. Ce script fait cette vérification, puis écrit des fichiers propres.

**Pourquoi c'est la base de tout.** Si les données sont fausses, toutes les analyses derrière sont fausses.

**Les étapes, dans l'ordre du code.**

| Étape | Ce qu'elle fait | Pourquoi |
|---|---|---|
| Configuration | Lit `atc.csv` pour connaître les 8 groupes et leurs noms | Une seule source pour les noms |
| 1. Chargement | Lit les 4 fichiers et transforme les dates en vraies dates | Trois fichiers écrivent les dates à l'américaine (mois/jour/année), le quatrième autrement |
| 2. Contrôles de base | Vérifie : dates dans l'ordre, pas de doublon, pas de case vide, pas de valeur négative | Le script s'arrête s'il y a un problème, au lieu de continuer avec des données cassées |
| 3. Colonnes en double | Vérifie les colonnes année, mois, heure, jour, puis les recalcule | Elles répètent la date. Dans le fichier journalier, la colonne « Hour » vaut 276 quand la journée est complète (0+1+…+23) : ça permet de repérer les journées coupées |
| 4. Cohérence | Additionne les heures pour comparer aux jours, les jours pour comparer aux semaines, puis aux mois | C'est LE contrôle demandé par le sujet |
| 5. Périodes incomplètes | Marque les jours, semaines et mois qui ne sont pas entiers | Comparer un mois de 8 jours à un mois de 31 jours fausserait tout |
| 6. Heures d'ouverture | Repère les heures où il n'y a jamais de vente (23 h à 6 h) | Pour ne pas les compter dans les moyennes par heure |
| 7. Valeurs extrêmes | Repère les jours anormalement hauts et les marque | On les signale mais on ne les supprime pas : on ne peut pas prouver que ce sont des erreurs |
| 8. Quantités à virgule | Compte les valeurs comme 0,33 | L'unité n'est pas expliquée dans l'export : on le signale |
| 9. Écriture | Écrit les fichiers dans `data/clean/` avec les vrais noms en colonnes, et le journal `etat_des_donnees.csv` | Les notebooks partent de là |

**Ce qu'on a trouvé grâce à lui.**

- Heure, jour et semaine sont parfaitement d'accord.
- Le fichier mensuel du client est faux pour 31 mois sur 70. On l'a écarté et on a recalculé les mois à partir des jours.
- Le premier jour (2 janvier 2014) et le dernier (8 octobre 2019) sont incomplets.
- Le dernier mois complet est septembre 2019.

**Le journal `etat_des_donnees.csv`.** À chaque contrôle, le script écrit une ligne : ce qu'il a constaté et ce qu'il a fait. C'est « l'état des données » demandé par le sujet, et il se retrouve dans le classeur Excel.

## 4. `statistiques.ipynb` – ce qui se vend, et quand

**À quoi il sert.** Le sujet demande des statistiques descriptives qui soutiennent nos conclusions. Chaque tableau répond à une question précise.

| Partie du notebook | Question | Comment c'est calculé |
|---|---|---|
| Résumé statistique | Qu'est-ce qui se vend, est-ce régulier ? | Pour chaque groupe : total, moyenne et médiane par jour, écart-type, part des jours sans vente |
| Régularité (graphique) | Quels groupes sont imprévisibles ? | Coefficient de variation = écart-type ÷ moyenne. Au-dessus de 1, c'est très irrégulier |
| Part par heure | À quelles heures vend-on ? | Moyenne par heure, transformée en pourcentage de la journée |
| Indice par jour | Quels jours sont forts ? | Moyenne du jour ÷ moyenne générale × 100 |
| Indice par mois | Quelles saisons ? | Moyenne du mois ÷ moyenne générale × 100 |
| Carte heure × jour | Quand la pharmacie est-elle chargée ? | Moyenne pour chaque couple jour/heure |
| Évolution 2015-2018 | Qu'est-ce qui monte ou baisse ? | Total par année complète |
| Marge de sécurité | Combien stocker en plus ? | Le « p95 » : la quantité dépassée seulement 1 jour sur 20 |

**Pourquoi des indices en base 100.** Le paracétamol se vend six fois plus que les autres. Si on comparait les quantités, on ne verrait que lui. Avec un indice, 100 veut dire « un jour normal pour ce groupe » et 120 veut dire « 20 % de plus que d'habitude ». Tous les groupes deviennent comparables.

**Pourquoi on n'additionne pas les groupes.** On ne connaît pas l'unité des quantités. Additionner du paracétamol et des somnifères n'a peut-être aucun sens.

**Pourquoi on écarte les périodes incomplètes.** Toutes les cellules commencent par garder seulement les journées ou les mois complets.

## 5. `externe.ipynb` – les ventes et la grippe

**À quoi il sert.** Le propriétaire veut savoir ce qui dépend de sa pharmacie et ce qui dépend de l'extérieur. Le sujet impose d'aller chercher soi-même une donnée publique et de l'utiliser vraiment dans l'analyse.

**L'idée.** On prend le nombre de cas de grippe en France chaque semaine, on le met à côté des ventes de la pharmacie, et on regarde si les deux bougent ensemble.

| Partie | Ce qu'elle fait | Pourquoi |
|---|---|---|
| Chargement de Sentinelles | Lit le fichier grippe et transforme le numéro de semaine en date | Dans nos ventes, une semaine est repérée par son dimanche de fin : il faut le même repère des deux côtés |
| Jointure | Colle la colonne « grippe » à côté des ventes de la même semaine | Pour comparer ligne par ligne |
| Corrélation | Calcule un chiffre entre -1 et 1 par groupe | Proche de 1 : les deux montent ensemble. Proche de 0 : aucun lien |
| Forte grippe / normale | Compare les ventes moyennes des semaines de forte grippe aux autres | Plus parlant qu'une corrélation : « +46 % de paracétamol » |
| Graphique | Les deux courbes l'une sous l'autre | Pour le montrer |
| Grippe contre saison | Refait le calcul en comparant chaque semaine à la moyenne de son mois | Pour vérifier que ce n'est pas juste « l'hiver » qui fait monter les deux |

**Résultat.** Paracétamol +46 %, antiasthmatiques +44 % les semaines de forte grippe. Les anxiolytiques et les somnifères ne bougent pas.

**Les réserves à connaître.**

- La donnée est nationale, car on ne sait pas où est la pharmacie.
- Deux courbes qui bougent ensemble ne prouvent pas que l'une cause l'autre.
- Le seuil de « forte grippe » (150 cas pour 100 000 habitants) est notre choix.

## 6. `prevision.ipynb` – peut-on prévoir le mois suivant ?

**À quoi il sert.** C'est la question du manager. Le sujet exige un vrai test : des prévisions comparées à des mois qui n'ont pas servi à les construire, et comparées à la prévision la plus simple possible.

**La logique du test.** On fait semblant d'être dans le passé.

1. On se place fin septembre 2017.
2. On prévoit octobre 2017 avec uniquement ce qu'on connaissait à ce moment-là.
3. On regarde ce qui s'est vraiment vendu en octobre 2017, et on note l'écart.
4. On avance d'un mois et on recommence, jusqu'à septembre 2019.

Ça fait 24 prévisions par groupe.

**Les trois méthodes comparées.**

| Méthode | Ce qu'elle dit |
|---|---|
| Naïve 1 | Le mois prochain = ce mois-ci |
| Naïve 2 | Le mois prochain = le même mois l'an dernier |
| Notre modèle (Holt-Winters) | Combine le niveau récent des ventes, la tendance (ça monte ou ça baisse) et la saison (l'effet habituel de ce mois-là) |

**Comment on décide.** On calcule l'erreur moyenne de chaque méthode. Puis on divise l'erreur du modèle par celle de la meilleure méthode naïve. Si ce rapport est à 0,80 ou moins, le modèle se trompe au moins 20 % de moins : on répond « oui ».

**Pourquoi comparer à une méthode naïve.** Un modèle compliqué qui ne fait pas mieux que « comme le mois dernier » ne sert à rien. Le pharmacien n'a pas besoin de nous pour ça.

**Pourquoi le test est honnête.** À chaque prévision, le modèle ne voit que les mois d'avant, y compris pour choisir ses réglages. Et le seuil de 0,80 a été fixé avant de regarder les résultats.

**Le contrôle de robustesse.** On refait tout le test avec une version plus simple du modèle (sans la tendance). Si le verdict est le même, c'est qu'il ne dépend pas d'un réglage particulier.

**Résultat.** Oui pour le paracétamol (rapport 0,65) et les antihistaminiques (0,79). Non pour les six autres.

## 7. `controle.ipynb` – le graphique du fichier mensuel

**À quoi il sert.** Montrer en une image pourquoi on a écarté le fichier mensuel du client.

**Comment.** Le nettoyage a déjà calculé, pour chaque mois et chaque groupe, l'écart entre le mensuel du client et la somme des jours. Le notebook garde le plus grand écart de chaque mois et dessine une barre par mois, sur les 70 mois.

**Ce qu'on voit.** 31 barres rouges éparpillées sur six ans, jusqu'à 75 %.

## 8. `partage.ipynb` – le risque de donner les données

**À quoi il sert.** Donner un chiffre au propriétaire pour sa décision sur l'offre du laboratoire.

**L'idée.** Une vente est dangereuse quand elle est toute seule. Si un seul somnifère a été vendu entre 9 h et 10 h, quelqu'un qui a vu une personne entrer à 9 h 15 sait ce qu'elle a acheté.

**Comment.** Pour les anxiolytiques et les somnifères, et pour chaque niveau de détail (heure, jour, semaine, mois) :

1. on garde les périodes où il y a eu au moins une vente ;
2. on compte la part de celles qui n'ont que 2 unités ou moins.

**Résultat.** Par heure : 82 % et 86 %. Par mois : 0 %. Donc on ne partage qu'au mois.

## 9. `classeur.ipynb` – fabriquer le classeur Excel

**À quoi il sert.** C'est le livrable du client. Le sujet demande une feuille de synthèse, les statistiques, l'état des données et un outil de sélection, sans macro.

**Comment.** Le notebook recalcule les statistiques et la prévision, puis écrit le fichier `classeur_pharmacie.xlsx` avec la bibliothèque `xlsxwriter`.

| Feuille | Ce qu'il y a dedans |
|---|---|
| Synthèse | Les messages principaux et une fiche par groupe |
| Statistiques | Tous les tableaux de chiffres |
| État des données | Quel fichier sert à quoi, et le journal du nettoyage |
| Outil | La sélection de groupes et de dates |
| Données | Les ventes jour par jour (l'outil lit cette feuille) |
| Référentiel | Les codes ATC et leurs noms |

**Comment marche l'outil sans macro.** Le notebook écrit des **formules Excel** dans les cellules. Par exemple une formule `SOMME.SI.ENS` qui additionne les ventes d'un groupe entre la date de début et la date de fin. Quand le pharmacien change une date, Excel recalcule tout seul.

**Pourquoi le classeur est fabriqué par le code.** Le sujet l'impose : les statistiques du classeur doivent venir du code. Si on les tapait à la main, il faudrait tout refaire chaque mois.

## 10. Les choix à savoir expliquer

| Notre choix | Pourquoi |
|---|---|
| On ne touche pas à `data/raw/` | Pour pouvoir toujours repartir des fichiers du client |
| On écarte le mensuel du client | Il n'est pas d'accord avec les trois autres fichiers |
| On retire les périodes incomplètes | Sinon les moyennes et les totaux sont faux |
| On marque les valeurs extrêmes sans les supprimer | On ne peut pas prouver que ce sont des erreurs |
| On utilise des indices en base 100 | Pour comparer des groupes de tailles très différentes |
| On ne parle jamais d'euros | Il n'y a pas de prix dans l'export |
| On compare le modèle à une méthode naïve | C'est demandé par le sujet, et c'est la seule façon de savoir s'il sert à quelque chose |
| On fixe les seuils avant de voir les résultats | Pour ne pas arranger la conclusion |
| On prend la grippe au niveau national | On ne connaît pas la ville de la pharmacie |

## 11. Le Python utilisé, en bref

Tout le projet repose sur une bibliothèque, **pandas**, qui manipule des tableaux (comme des feuilles Excel).

| Ce qu'on écrit | Ce que ça fait |
|---|---|
| `import pandas as pd` | Charge pandas. On l'appelle ensuite `pd` |
| `d = pd.read_csv("fichier.csv")` | Lit un fichier et le range dans un tableau nommé `d` |
| `d["colonne"]` | Prend une colonne du tableau |
| `d[d["journee_complete"]]` | Garde seulement les lignes où la condition est vraie (un filtre) |
| `d[groupes].mean()` | Calcule la moyenne de chaque colonne. Pareil avec `.sum()`, `.median()`, `.std()`, `.max()` |
| `d.groupby("jour_semaine")[groupes].mean()` | Fait un calcul par catégorie : ici la moyenne pour chaque jour de la semaine |
| `a.merge(b, on="date")` | Colle deux tableaux côte à côte en faisant correspondre les dates |
| `x[groupes].corrwith(x["grippe"])` | Calcule la corrélation de chaque colonne avec la grippe |
| `display(tableau)` | Affiche un tableau dans le notebook |
| `plt.savefig("image.png")` | Enregistre un graphique en image |

Trois écritures qui reviennent souvent :

- **La liste des groupes.** `groupes = [c for c in d.columns if c.endswith(")")]` veut dire : « fais la liste des colonnes dont le nom finit par une parenthèse ». Ce sont nos 8 groupes, comme « Paracétamol (N02BE) ».
- **La boucle.** `for g in groupes:` répète les lignes qui suivent une fois pour chaque groupe.
- **Le texte avec une valeur dedans.** `f"{n} mois sur 70"` écrit le contenu de la variable `n` dans la phrase.

**Les notebooks.** Un notebook s'exécute de haut en bas. Chaque cellule utilise ce que les cellules du dessus ont créé. C'est pour ça qu'il faut toujours faire « Run All » après l'avoir ouvert : sinon on obtient l'erreur `NameError: name '...' is not defined`, qui veut dire qu'une cellule plus haut n'a pas été lancée.
