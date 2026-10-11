# Rush 2 - Analyse des ventes d'une pharmacie

Projet réalisé à trois dans le cadre du Bootcamp Data.

On a analysé les ventes d'une pharmacie indépendante entre janvier 2014 et octobre 2019, sur 8 groupes de médicaments. Le but était de rendre un classeur Excel que le client peut utiliser seul, avec le code Python qui permet de le refaire quand de nouvelles données arrivent.

On a utilisé Jupyter.

## Ce qu'il y a dans le dépôt

- `data/raw/` : les 4 exports du client (par heure, jour, semaine et mois). On n'y a pas touché.
- `data/clean/` : les mêmes données une fois nettoyées.
- `data/ref/atc.csv` : le tableau qui fait le lien entre les codes ATC et les vrais noms des médicaments.
- `data/externe/` : les chiffres de la grippe en France par semaine, récupérés sur le site du réseau Sentinelles.
- `nettoyage.py` : vérifie les exports et crée les fichiers propres.
- `statistiques.ipynb` : les statistiques descriptives (par jour, par heure, par mois, par année).
- `externe.ipynb` : la comparaison entre nos ventes et l'épidémie de grippe.
- `prevision.ipynb` : le test pour savoir si on peut prévoir le mois suivant.
- `classeur.py` : fabrique le classeur Excel.
- `classeur_pharmacie.xlsx` : le classeur pour le client.

## Installation

Il faut avoir Python 3. Ensuite, dans un terminal à la racine du projet :

```
python -m venv venv
venv\Scripts\python -m pip install -r requirements.txt
```

## Comment relancer le projet avec de nouvelles données
1. Mettre les 4 nouveaux exports dans `data/raw/` à la place des anciens, sans changer leurs noms.
2. Lancer le nettoyage :
   ```
   venv\Scripts\python nettoyage.py
   ```
3. Lancer la création du classeur :
   ```
   venv\Scripts\python classeur.py
   ```
4. Pour les notebooks, les ouvrir dans VS Code, choisir le noyau `venv` et faire « Run All ».

Il faut respecter cet ordre, parce que le classeur et les notebooks utilisent les fichiers créés par le nettoyage.
Le classeur mis à jour s'appelle `classeur_pharmacie.xlsx` et se trouve à la racine.

## Le classeur Excel

Il contient 6 feuilles : Synthèse, Statistiques, État des données, Outil, Données et Référentiel.
La feuille Outil permet de choisir un ou plusieurs groupes de médicaments et une période, et d'afficher les ventes correspondantes. Il n'y a pas de macro, ça fonctionne directement dans Excel 365.

## Ce qu'on a remarqué sur les données

- Le fichier mensuel du client ne donne pas les mêmes totaux que les trois autres (31 mois sur 70 sont différents). On ne l'a donc pas utilisé : on a recalculé les mois à partir du fichier journalier.
- Le dernier mois complet est septembre 2019. Octobre 2019 s'arrête au 8.
- Il n'y a pas de prix dans les exports et on ne connaît pas l'unité des quantités. On parle donc toujours de quantités vendues, jamais de chiffre d'affaires.

## Qui a fait quoi
- **Esteban** : 
- **Léa** : 
- **Lilie** : 