# Application locale (Streamlit)

Une petite application web qui tourne sur l'ordinateur de la pharmacie. On y dépose les
4 exports de ventes : le code contrôle et nettoie les fichiers, puis affiche les analyses
et les graphiques. Aucune connaissance de Python n'est nécessaire pour s'en servir.

## Lancer l'application

Sous Windows : double-cliquer sur `lancer.bat`. Le navigateur s'ouvre tout seul sur
l'application (http://localhost:8501). Pour l'arrêter, fermer la fenêtre noire.

En ligne de commande :

    pip install -r requirements.txt
    python -m streamlit run app/app.py

## S'en servir

1. Déposer les 4 exports (heure, jour, semaine, mois) dans le cadre « Vos fichiers », à gauche.
   L'ordre n'a pas d'importance, l'application reconnaît chaque fichier.
2. Lire le bandeau en haut : il indique si les fichiers sont cohérents entre eux.
3. Parcourir les onglets.

Pour une démonstration sans fichier, cocher « Utiliser les exports d'exemple » (lit `data/raw/`).

| Onglet | Pour qui | Ce qu'on y trouve |
|---|---|---|
| Commandes | Pharmacien acheteur | Ventes par groupe et par période, saisons, jours de la semaine, prévision du mois suivant |
| Organisation de la pharmacie | Propriétaire | Heures chargées, lien avec la grippe, risque selon le niveau de détail partagé |
| Fiabilité des données | Manager | Contrôles des fichiers, écarts du fichier mensuel, test de la prévision |
| Télécharger | Tous | Classeur Excel des statistiques, ventes journalières nettoyées |

## Organisation du code

- `app/app.py` : l'interface. Elle ne fait aucun calcul, elle appelle `src/`.
- `src/nettoyage.py` : lecture, contrôles et nettoyage des 4 exports, avec le journal des contrôles.
- `src/analyses.py` : statistiques, test de prévision, comparaison avec la grippe, ventes isolées.
- `.streamlit/config.toml` : couleurs et réglages de l'application.

## Données et confidentialité

Les fichiers déposés sont traités en mémoire : rien n'est écrit sur le disque ni envoyé sur
Internet. L'application est prévue pour tourner en local uniquement, jamais hébergée en ligne :
l'export horaire permet de repérer des ventes isolées d'anxiolytiques et de somnifères.

La comparaison avec la grippe utilise `data/externe/sentinelles_syndromes_grippaux.csv`
(réseau Sentinelles), ou un fichier plus récent déposé dans le panneau de gauche.
