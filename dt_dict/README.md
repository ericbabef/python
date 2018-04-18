# Automatisation des réponses aux DT DICT en python

## Réalisé en python 2.7

## Modules nécessaires : 
- osgeo
- mapnik
- pdfjinja

## Fonctionnement : 
- configuration du config.json : 

chemin vers votre réseau, format shapefile

projection de votre reseau

- les xml à traiter doivent être placés dans le dossier xml

## Résultats : 

Les résultats sont dans le dossier output : 

- le CERFA est rempli
- une image du réseau, et de l'emplacement des travaux est créée

Il y a deux résultats possibles : 

- pas de réseau à l'emplacement des travaux => calcul de la distance, aucun atlas n'est créé, calcul de l'échelle
- présence d'un réseau à l'emplacement des travaux => création d'un atlas, calcul de l'échelle

## Exécution du script dans la console par exemple : 

``` bash
python execution_dt_dict.py
```
 
## Remarques / évolutions du script

- Toutes les informations du xml ne sont pas récupérées,
- Création d'un rapport en pdf avec reportlab par exemple,
- Développer plus particulièrement le deuxième résultats possibles ...