# Rush 2 – Plan pour terminer le projet

Document de travail du groupe. **À ne pas livrer** : le sujet demande que le dépôt ne contienne rien d'inutile au client ou au manager. À supprimer (ou à ne pas commiter) avant le rendu.

## Où on en est

| Livrable | État |
|---|---|
| Nettoyage des 4 exports (`nettoyage.py`) | Fait |
| Noms des groupes de médicaments (`data/ref/atc.csv`) | Fait, libellés à vérifier sur l'index ATC/DDD de l'OMS |
| Statistiques descriptives | À faire |
| Donnée publique externe | À faire |
| Test de prévision | À faire |
| Classeur Excel (synthèse, statistiques, état des données, outil) | À faire |
| Mémo PDF (prévision + partage des données) | À faire |
| 3 decks de 5 slides | À faire |
| README (qui a fait quoi) | Vide |

## Ce que le nettoyage a déjà établi

À réutiliser dans le classeur, le mémo et le deck manager.

- Les exports horaire, journalier et hebdomadaire concordent entre eux.
- L'export **mensuel du client est écarté** : 31 mois sur 70 ne correspondent pas à la somme des jours. Le mensuel est reconstruit depuis le journalier.
- Dernier mois complet : **septembre 2019**. Octobre 2019 ne contient que 8 jours, janvier 2014 n'a pas le 1er janvier.
- Pharmacie ouverte de 7 h à 22 h ; aucune vente de 23 h à 6 h.
- 9 valeurs extrêmes repérées et marquées, jamais supprimées.
- Quantités non entières (0,33 ; 3,67) : unité non documentée.
- **Ni prix ni unité dans l'export** : aucune conclusion en euros ou en marge, tout se dit en quantités.

## Les étapes, dans l'ordre

### 1. Assainir le dépôt (30 min)

- Commiter le travail actuel.
- Supprimer `mon_analyse.ipynb` (brouillon).
- Ajouter un `requirements.txt` (pandas, numpy, etc.) : sans lui, le code ne tourne pas depuis une copie fraîche.
- Chacun commite sous son propre compte : l'historique est noté et doit montrer le partage du travail.

### 2. Statistiques descriptives (`statistiques.ipynb`)

Cinq cellules, à exécuter dans l'ordre. Chacune répond à une question d'un interlocuteur.

| Cellule | Ce qu'elle calcule | À quoi elle sert | Pour qui |
|---|---|---|---|
| 1. Résumé par groupe | Total, moyenne et médiane par jour, écart-type, part des jours à zéro, coefficient de variation | Savoir ce qui se vend et si c'est régulier. Un coefficient de variation élevé ou beaucoup de jours à zéro = groupe difficile à anticiper | Pharmacien acheteur |
| 2. Jour de semaine | Indice par jour (100 = jour moyen du groupe) | Savoir quels jours renforcer le stock et l'équipe, et repérer les groupes semaine / week-end | Pharmacien acheteur, propriétaire |
| 3. Heure | Part de chaque heure dans les ventes de la journée, heures d'ouverture seulement | Repérer les pics de la journée et les heures creuses, pour discuter les horaires d'ouverture | Propriétaire |
| 4. Saisonnalité | Indice par mois (100 = mois moyen du groupe) | Savoir quelles périodes de l'année anticiper pour chaque groupe | Pharmacien acheteur |
| 5. Tendance annuelle | Total par année complète (2015-2018) et évolution en % | Savoir quels groupes montent ou baissent sur la durée | Propriétaire, manager |

Règles communes :

- La cellule 1 crée `d` et `groupes`, utilisés par toutes les autres : toujours l'exécuter en premier.
- Une statistique par cellule : Jupyter n'affiche que le dernier tableau d'une cellule.
- Les indices (base 100) servent à comparer des groupes de tailles très différentes : le paracétamol se vend six fois plus que les autres.
- On ne calcule pas de « part du volume » entre groupes : l'unité des quantités n'est pas documentée, additionner des groupes entre eux n'a pas de sens garanti.
- Journées, mois et années incomplets sont écartés des calculs.

Premiers résultats à retenir :

- Jour : anxiolytiques et somnifères chutent le dimanche (65 et 53) ; paracétamol et anti-inflammatoires montent le week-end (111 à 119).
- Heure : deux pics, vers 10 h-12 h et 18 h-20 h ; 7 h et 22 h pèsent moins de 1 % chacune.
- Saison : antihistaminiques au printemps (179 en mai), antiasthmatiques et paracétamol en hiver, creux en été.
- Tendance : antiasthmatiques et somnifères environ +52 %, aspirine -30 %.

À creuser : l'année 2017 est nettement plus basse que ses voisines pour plusieurs groupes. Regarder mois par mois s'il y a un trou (fermeture, défaut d'export) avant de conclure sur la tendance.

Pour finir l'étape : « Restart » puis « Run All » sans erreur, puis commit. L'écriture des tableaux dans le classeur relève de l'étape 5.

### 3. Donnée externe (`externe.py`)

Elle doit entrer dans l'analyse et fonder au moins une recommandation au propriétaire (part de la pharmacie / part de son environnement). La localisation de la pharmacie est inconnue : prendre une source nationale.

| Source | Usage | Priorité |
|---|---|---|
| Réseau Sentinelles : incidence hebdomadaire des syndromes grippaux (CSV) | À croiser avec le paracétamol et les antiasthmatiques | 1 |
| Jours fériés et vacances scolaires (data.gouv.fr) | Expliquer les creux | 2 |
| Open Medic (Assurance Maladie, remboursements par code ATC) | Comparer la pharmacie à la France | 3 |

- Le script télécharge la donnée et en garde une copie dans le dépôt, pour que tout tourne hors ligne.
- **À vérifier avant de s'engager** : format de chaque source et couverture de la période 2014-2019.

### 4. Test de prévision (`prevision.py`)

Question du manager : peut-on prévoir, pour chaque groupe, les ventes du mois qui suit le dernier mois complet (donc octobre 2019) ?

- Série mensuelle reconstruite depuis le journalier, mois complets seulement (février 2014 à septembre 2019, 68 mois).
- Test glissant : pour chacun des 24 derniers mois, prévoir avec uniquement les mois précédents.
- Références naïves : « même valeur que le mois dernier » et « même mois l'an dernier ».
- Modèle candidat : lissage exponentiel saisonnier (Holt-Winters), un par groupe.
- Mesure : erreur absolue moyenne, comparée à celle de la meilleure référence naïve.
- Verdict par groupe : « oui » seulement si le modèle bat nettement la référence. Réponse probable : « pour certains groupes seulement ».

L'allure d'une courbe n'est pas un test : seul le tableau d'erreurs compte.

### 5. Classeur Excel (`classeur.py`)

Recommandation : générer le classeur entièrement en Python (bibliothèque xlsxwriter) à chaque relance.

| Feuille | Contenu |
|---|---|
| Synthèse | Chiffres clés et messages |
| Statistiques | Tableaux de l'étape 2 |
| État des données | Journal du nettoyage + quel export sert à quoi |
| Outil | 8 cases Oui/Non pour les groupes, date de début, date de fin, formules `SOMME.SI.ENS` / `FILTRE` |
| Données | Ventes journalières |
| Référentiel | Codes ATC et noms |

- Aucune macro : l'outil doit fonctionner dans Excel 365 pour quelqu'un qui n'ouvrira jamais Python.
- Alternative : tableau croisé dynamique avec segments, fait à la main. Plus joli, mais ne se régénère pas par le code.
- Avec l'option recommandée, `data/clean/ventes_journalier_long.csv` devient inutile et sera à retirer.

### 6. Mémo PDF

**Partie 1 – Prévision.** La question, le protocole de test, le tableau d'erreurs par groupe, la réponse.

**Partie 2 – Partage des données avec le laboratoire.**

- Risque de ré-identification par niveau de détail :
  - à l'heure, les somnifères se vendent à l'unité : quelqu'un qui a vu un voisin entrer à 9 h peut en déduire son achat ;
  - au mois, le risque est faible.
- Recommandation probable : partage mensuel au plus, jamais horaire ni journalier.
- Au-delà du RGPD, pistes **à vérifier sur Légifrance et le site de la CNIL** (citées de mémoire) :
  - secret professionnel ;
  - indépendance du pharmacien (code de déontologie) ;
  - dispositif « anti-cadeaux » du Code de la santé publique ;
  - plafonnement des remises ;
  - dépendance commerciale envers le laboratoire ;
  - réutilisation ou revente des données par le laboratoire.

### 7. Trois decks de 5 slides

Trois decks qui ne diffèrent que par leur titre comptent pour un seul. Chacun part d'une décision différente.

| Interlocuteur | Ce qu'il doit décider | Contenu |
|---|---|---|
| Manager | L'analyse est-elle solide ? Peut-on vendre une suite ? | Contrôles, mensuel écarté, test de prévision, mission de suivi |
| Pharmacien acheteur | Quoi commander, quand ? | Groupes, jours, périodes à anticiper ; démonstration de l'outil |
| Propriétaire | Que changer dans la pharmacie ? | Horaires, effectifs, stock saisonnier ; part de l'environnement ; offre du laboratoire |

### 8. README et répétition

- README : qui a fait quoi, comment relancer le code.
- Trois oraux chronométrés à 5 minutes.

## Répartition proposée

| Personne | Code | Écrit | Deck et oral |
|---|---|---|---|
| A | Étapes 1, 2 et 5 (statistiques, classeur, outil) | README | Pharmacien acheteur |
| B | Étapes 3 et 4 (donnée externe, prévision) | Mémo partie 1 | Manager |
| C | Relecture et tests du code sur copie fraîche | Mémo partie 2 (juridique) | Propriétaire |

- B et C peuvent démarrer tout de suite, sans attendre A.
- Le classeur (étape 5) dépend des étapes 2 à 4 : A en construit d'abord le squelette, puis y branche les résultats de B.

## Ordre de démarrage

1. Étape 1 (dépôt).
2. En parallèle : étape 2 (A), étape 3 (B), mémo partie 2 (C).
3. Étape 4 (B), puis étape 5 (A).
4. Mémo partie 1, decks, README.
5. Test sur une copie fraîche du dépôt, puis répétition des oraux.

## Décisions à prendre en groupe

- Classeur généré en Python (recommandé) ou tableau croisé fait à la main ?
- Quelle source externe en priorité ?
- Qui est A, B, C ?
