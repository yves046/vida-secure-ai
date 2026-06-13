GUIDE D’INSTALLATION – VIDA SECURE AI

Version

VIDA Secure AI – On-Premise Edition

Prérequis

* Serveur Linux recommandé (Ubuntu 22.04 LTS)
* Minimum 8 Go de RAM
* Minimum 100 Go d’espace disque
* Accès réseau aux caméras RTSP
* Licence VIDA valide

Installation

1. Copier le projet VIDA sur le serveur.
2. Copier le fichier license.json dans le dossier principal du projet.
3. Vérifier que les flux RTSP contenus dans la licence sont accessibles.
4. Accéder au dossier backend :

cd backend

5. Activer l’environnement Python VIDA :

conda activate vida311

6. Lancer VIDA :

python test_ffmpeg_frame.py

Vérifications

Le système doit afficher :

* Licence valide pour le client.
* Nombre de caméras autorisées.
* Flux vidéo actif.
* Détection des personnes fonctionnelle.

Arrêt du système

Appuyer sur :

Q

dans la fenêtre VIDA.

Ou utiliser :

CTRL + C

dans le terminal.

Support

En cas de problème :

* Vérifier la licence.
* Vérifier les flux RTSP.
* Vérifier la connexion réseau.