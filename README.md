# StockageCloud

## Prérequis

* Python 3.7 ou supérieur
* `pip` (gestionnaire de paquets Python)

## Installation

### 1. Cloner le dépôt

```bash
git clone <votre-url-du-dépôt>
cd StockageCloud
```

### 2. Installer les dépendances

Installez les paquets requis :

```bash
pip install flask
```

Ou via le fichier `requirements.txt` :

```bash
pip install -r requirements.txt
```

## Configuration de la base de données

### 1. Initialiser la base de données

Exécutez la commande suivante pour créer et initialiser la base :

```bash
flask --app app.py init-db
```

Cette commande va :

* Créer le fichier `database.db` s’il n’existe pas
* Créer les tables nécessaires pour les utilisateurs et les fichiers
* Initialiser le schéma de base de données

## Lancement de l’application

### 1. Démarrer le serveur Flask

Lancez l’application avec :

```bash
flask --app app.py run
```

### 2. Accéder à l’application

Après l’exécution de la commande, vous devriez voir une sortie semblable à :

```
 * Serving Flask app 'app.py'
 * Debug mode: off
 * Running on http://127.0.0.1:5000
```

Cliquez sur le lien (`http://127.0.0.1:5000`) ou copiez-collez-le dans votre navigateur.

## Utilisation

### 1. Inscription

* Rendez-vous sur la page d’inscription
* Créez un compte avec votre e-mail et votre mot de passe
* **Votre mot de passe sera haché de manière sécurisée avant d’être stocké**

### 2. Connexion

* Connectez-vous avec vos identifiants
* Vous serez redirigé vers votre tableau de bord personnel

### 3. Gestion des fichiers

* **Téléverser des fichiers** : Glissez-déposez vos fichiers ou cliquez pour les sélectionner
* **Télécharger des fichiers** : Cliquez sur le bouton de téléchargement à côté du fichier
* **Supprimer des fichiers** : Cliquez sur le bouton de suppression (avec confirmation)

## Structure du projet

```
StockageCloud/
├── app.py               # Application Flask principale
├── db.py                # Opérations sur la base de données
├── schema.sql           # Schéma de la base de données
├── database.db          # Base SQLite (créée après init-db)
├── static/              # Contenus statiques
│   ├── css/
│   │   └── styles.css   # Feuille de style principale
│   └── js/
│       ├── dashboard.js # Scripts pour le tableau de bord
│       ├── login.js     # Scripts de la page de connexion
│       └── register.js  # Scripts de la page d'inscription
├── templates/           # Modèles HTML
│   ├── dashboard.html   # Tableau de bord utilisateur
│   ├── index.html       # Page d’accueil
│   ├── login.html       # Page de connexion
│   ├── mainpage.html    # Page principale
│   └── register.html    # Page d'inscription
└── uploads/             # Dossier de stockage des fichiers
```
