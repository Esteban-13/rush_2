# Notes pour l'oral

Trois présentations de 5 minutes, une par interlocuteur. Compter environ 1 minute par diapositive.

Ces notes sont à dire avec vos mots, pas à lire. Fichier de travail : à ne pas livrer dans le dépôt.

## Conseils pour les trois oraux

- Commencer par la conclusion, puis donner les preuves.
- Un chiffre par idée, pas plus. Les autres sont sur la diapositive.
- Ne jamais parler d'euros ni de chiffre d'affaires : l'export ne contient pas de prix.
- Dire « groupes de médicaments », pas « médicaments » : on ne sait pas quelles boîtes ont été vendues.
- Si on ne sait pas répondre à une question : « on ne l'a pas mesuré, c'est une question à poser au client ».

---

# Partie 1 – Le manager (diapositives 1 à 5)

**Ce qu'il veut savoir :** est-ce que l'analyse est solide, et est-ce qu'on peut vendre une suite ?

## Diapositive 1 – Une analyse vérifiée, un outil livré, une suite à proposer (45 s)

- On donne la conclusion tout de suite.
- Les données sont utilisables, mais à condition de mettre de côté le fichier mensuel du client.
- Le classeur Excel est livré et il se refait tout seul avec le code.
- La prévision marche pour 2 groupes sur 8, et on l'a prouvé par un test.
- Ce qu'on n'a pas pu faire donne les idées pour la mission suivante.

## Diapositive 2 – Un export sur quatre ne concorde pas (1 min)

- Le client nous avait dit que personne n'avait vérifié ses quatre fichiers. On l'a fait.
- Les fichiers par heure, par jour et par semaine donnent exactement les mêmes totaux.
- Le fichier mensuel, lui, est faux pour 31 mois sur 70. Il est toujours plus haut que la somme des jours, jusqu'à 75 % en octobre 2014.
- On l'a donc mis de côté et on a recalculé les mois à partir du fichier journalier.
- On ne sait pas d'où vient l'erreur : c'est à demander au client.

**Chiffre à retenir :** 31 mois sur 70.

## Diapositive 3 – Prévoir le mois suivant : oui pour 2 groupes sur 8 (1 min 15)

- On n'a pas jugé sur une courbe. On a fait un vrai test.
- On a fait comme si on était dans le passé : pour chacun des 24 derniers mois, on a prévu les ventes avec seulement les mois d'avant, puis on a comparé avec la réalité.
- On a comparé notre modèle à ce que le pharmacien ferait tout seul : « comme le mois dernier » ou « comme l'an dernier ».
- Pour le paracétamol, le modèle se trompe 35 % de moins. Pour les antihistaminiques, 21 % de moins.
- Pour les six autres groupes, il ne fait pas mieux. Donc on ne promet rien dessus.
- Pour octobre 2019, ça donne environ 1 230 unités de paracétamol, à 140 près.

**Chiffre à retenir :** 2 groupes sur 8.

## Diapositive 4 – Quatre limites à dire au client (1 min)

- Il n'y a ni prix ni unité dans les données : on parle de quantités, jamais d'argent.
- On n'a que 8 groupes de médicaments, pas toute l'activité de la pharmacie.
- On ne sait pas où se trouve la pharmacie, donc on a utilisé les chiffres de la grippe pour toute la France.
- L'année 2017 est beaucoup plus basse que les autres et on ne sait pas pourquoi.
- Ces limites ne rendent pas l'analyse fausse, mais elles disent jusqu'où on peut conclure.

## Diapositive 5 – La mission de suivi que nous proposons (1 min)

- Le suivi mensuel : le client envoie ses quatre fichiers, on relance le code, le classeur est à jour.
- L'analyse en valeur : si le client nous donne les prix, on peut passer des quantités à la marge.
- La prévision élargie : avec l'adresse de la pharmacie, on peut ajouter la grippe de sa région et la météo. C'est une piste, on ne l'a pas encore testée.
- Pour commencer, il faut demander au client : les prix, les unités, l'adresse, et des explications sur 2017 et sur le fichier mensuel.

## Questions possibles du manager

| Question | Réponse |
|---|---|
| Pourquoi faire confiance au journalier plutôt qu'au mensuel ? | Parce que trois fichiers sur quatre sont d'accord entre eux. On n'a pas de preuve absolue, c'est pour ça qu'il faut demander au client. |
| Pourquoi un seuil de 20 % pour dire « oui » ? | C'est notre choix, fixé avant de voir les résultats. En dessous, le gain est trop petit pour s'engager. |
| Pourquoi seulement 24 mois de test ? | On a 68 mois complets et le modèle a besoin de plusieurs années pour apprendre la saison. 24 mois, c'est deux saisons complètes. |
| Le code marche vraiment sur de nouvelles données ? | Oui, il se relance depuis une copie neuve du dépôt. Quelques textes du journal de nettoyage sont encore écrits à la main et seraient à automatiser. |
| Pourquoi ça ne marche pas pour les autres groupes ? | Leurs ventes sont trop irrégulières ou pas assez saisonnières. L'historique seul ne suffit pas. |

---

# Partie 2 – Le pharmacien acheteur (diapositives 6 à 10)

**Ce qu'il veut savoir :** quoi commander, quels jours, à quelles périodes ?

## Diapositive 6 – Vos commandes : quoi anticiper, et quand (45 s)

- Vous savez déjà ce qui se vend. Ce que les données ajoutent, c'est le « quand ».
- Trois exemples : il se vend trois fois plus d'antihistaminiques en mai qu'en janvier.
- Le paracétamol monte de 46 % pendant les semaines de forte grippe.
- Les anxiolytiques baissent de 35 % le dimanche.

## Diapositive 7 – Chaque groupe a sa saison (1 min 15)

- Le tableau se lit ligne par ligne. 100, c'est un mois normal pour le groupe.
- En orange, les mois forts. En vert, les mois creux.
- Les antihistaminiques : pic d'avril à juin, c'est la saison des allergies.
- Le paracétamol et les antiasthmatiques : forts en janvier, octobre et décembre, creux en été.
- Les anti-inflammatoires acétiques et les anxiolytiques changent peu : le stock peut rester le même toute l'année.

**Chiffre à retenir :** 179 en mai pour les antihistaminiques.

## Diapositive 8 – Semaine ou week-end : deux profils de vente (1 min)

- Il y a deux types de groupes.
- Ceux qui se vendent en semaine : les anxiolytiques et les somnifères. Le dimanche, ils tombent à 65 et 53.
- Ceux qui montent le week-end : le paracétamol et les anti-inflammatoires, entre 111 et 119 le samedi et le dimanche.
- Les antiasthmatiques, eux, sont stables toute la semaine.

## Diapositive 9 – Ce qu'on peut prévoir, et ce qu'on ne peut pas (1 min)

- Pour deux groupes, on peut annoncer un chiffre à l'avance : le paracétamol (environ 1 230 unités en octobre 2019) et les antihistaminiques (environ 78).
- Pour les six autres, non. Notre modèle ne fait pas mieux que de reprendre le chiffre du mois d'avant.
- Les somnifères sont un cas à part : deux jours sur trois, il ne s'en vend aucun. Mieux vaut garder un petit stock fixe que chercher à prévoir.

## Diapositive 10 – Votre outil dans Excel (1 min)

- L'outil est dans le classeur, sur la feuille « Outil ».
- Vous mettez une date de début et une date de fin. Si c'est la même date, vous avez un seul jour.
- Vous mettez « Oui » devant les groupes qui vous intéressent.
- Les ventes s'affichent tout de suite : le total, la moyenne par jour et le détail jour par jour.
- Il n'y a pas de macro et pas besoin de Python.
- **Faire la démonstration en direct si possible.**

## Questions possibles du pharmacien

| Question | Réponse |
|---|---|
| C'est en boîtes, les quantités ? | On ne sait pas. L'unité n'est pas précisée dans l'export, et il y a des valeurs comme 0,33. C'est pour ça qu'on compare chaque groupe à lui-même, avec des indices. |
| Quels médicaments exactement dans chaque groupe ? | L'export donne seulement le code du groupe (code ATC), pas les produits. |
| Et si je veux voir plus de 3 mois dans l'outil ? | Le total fonctionne sur n'importe quelle période. Le détail jour par jour s'arrête à 93 jours. |
| L'outil se met à jour comment ? | On relance le code avec les nouveaux exports et le classeur est refait. |
| Pourquoi la grippe fait monter les antiasthmatiques ? | On constate que ça monte en même temps. On n'a pas prouvé que c'est la cause : le froid peut jouer aussi. |

---

# Partie 3 – Le propriétaire (diapositives 11 à 15)

**Ce qu'il veut savoir :** que changer dans la pharmacie, et quoi répondre au laboratoire ?

## Diapositive 11 – Trois décisions pour votre pharmacie (45 s)

- Vous vouliez savoir ce qui dépend de vous et ce qui dépend de l'extérieur, et quoi répondre au laboratoire.
- On a trois réponses : une sur l'organisation de la journée, une sur l'hiver, une sur vos données.

## Diapositive 12 – Deux pics par jour (1 min)

- Les ventes se concentrent sur deux moments : de 10 h à 14 h, et de 18 h à 21 h.
- C'est là qu'il faut que l'équipe soit au complet.
- À 7 h et à 22 h, on a moins de 1 % des ventes.
- **Attention à ne pas aller trop loin :** on ne connaît pas vos vrais horaires, et on n'a que 8 groupes. C'est une question à voir avec vous, pas un conseil de fermer plus tôt.

## Diapositive 13 – L'hiver et la grippe expliquent une partie de vos ventes (1 min 15)

- C'est notre réponse à votre question sur l'environnement.
- On est allés chercher les chiffres de la grippe en France, semaine par semaine, sur le site du réseau Sentinelles. Ce sont des données publiques.
- On les a comparés à vos ventes.
- Les semaines de forte grippe, le paracétamol et les antiasthmatiques se vendent environ 45 % de plus.
- Ça, ce n'est pas la pharmacie, c'est l'extérieur.
- Les anxiolytiques et les somnifères, eux, ne bougent pas avec la grippe.
- Notre conseil : suivre le bulletin de la grippe chaque semaine et commander avant que les ventes montent.

**Chiffre à retenir :** +46 % de paracétamol.

## Diapositive 14 – Offre du laboratoire : le danger est dans le détail (1 min)

- Dans vos données, il n'y a aucun nom. Mais ça ne suffit pas.
- Exemple : un voisin voit quelqu'un entrer à 9 h. Si le fichier montre une seule vente de somnifère entre 9 h et 10 h, il sait ce que cette personne a acheté.
- On a mesuré ce risque. Par heure, plus de 8 ventes sur 10 sont isolées comme ça.
- Par mois, il n'y en a plus aucune.
- Donc tout dépend du niveau de détail qu'on donne.

**Chiffre à retenir :** 86 % par heure, 0 % par mois.

## Diapositive 15 – Notre conseil : un partage limité et encadré (1 min)

- On vous conseille de ne pas donner le fichier complet.
- Vous pouvez proposer à la place des chiffres par mois, et par trimestre pour les somnifères.
- Avec un contrat écrit : à quoi servent les données, interdiction de les revendre, durée limitée.
- Et avant de signer, demandez l'avis de l'Ordre des pharmaciens ou d'un juriste.
- Parce qu'en plus du RGPD, il y a le secret professionnel, votre indépendance vis-à-vis des fournisseurs, et la règle qui encadre les avantages donnés par les laboratoires.
- On est consultants en données, pas juristes : c'est pour ça qu'on vous renvoie vers eux sur ce point.

## Questions possibles du propriétaire

| Question | Réponse |
|---|---|
| Je dois fermer plus tôt le soir ? | On ne peut pas le dire. On n'a que 8 groupes et pas vos horaires. Il faudrait regarder toutes les ventes de la pharmacie. |
| Combien je gagne avec l'offre du laboratoire ? | On ne peut pas le calculer, il n'y a pas de prix dans les données. C'est à vous de comparer l'avantage proposé avec les risques. |
| Mes données sont anonymes, où est le problème ? | Il n'y a pas de nom, mais quand il y a une seule vente dans l'heure, quelqu'un qui a vu la personne entrer peut deviner. Pour le RGPD, ça reste une donnée personnelle, et ici une donnée de santé. |
| C'est légal ou pas de les donner ? | Par mois, le risque est faible. Par heure ou par jour, non. Et l'avantage en échange doit être vérifié par l'Ordre ou un juriste. |
| Pourquoi la grippe de toute la France et pas de ma ville ? | On ne savait pas où se trouve la pharmacie. Avec votre région, ce serait plus précis. |
| Qu'est-ce qui dépend vraiment de moi alors ? | L'organisation de l'équipe selon les pics, le stock préparé avant les saisons, et la décision sur vos données. |
