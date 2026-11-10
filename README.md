# Environnement de développement MP2I/MPI

Contient :
- `utop` comme interpréteur interactif OCaml
- `gcc` comme compilateur C (exemple : `gcc test.c` puis ./a.out)
- `ocaml` pour exécuter un fichier OCaml (exemple : `ocaml test.ml`)
- `ocamlopt` pour compiler un fichier OCaml (exemple : `ocamlopt test.ml` puis ./a.out)
- `sqlite3` pour gérer des bases de données SQLite.

## Socle Nix commun

`flake.nix` définit les outils utilisés aussi par [`lib`](https://github.com/mpi-informatique/lib) et [`exercices`](https://github.com/mpi-informatique/exercices). OCaml 5.5.2 et les autres versions sont verrouillés dans `flake.lock`. Plateformes : Linux x86_64/ARM64 et macOS ARM64.

```sh
nix develop
utop
nix flake check
```

Les dépôts consommateurs importent `github:mpi-informatique/tp-environnement`, suivent son entrée `nixpkgs` et étendent `environnement.lib.mkShell system { packages = [ … ]; }`. Pour adopter une nouvelle version du socle : `nix flake update environnement` dans ces dépôts.

## Bibliothèque OCaml

Le Codespace contient [`mpi-informatique`](https://github.com/mpi-informatique/lib) dans un switch opam personnel, accessible en écriture. Pour la mettre à jour :

```sh
opam upgrade mpi-informatique
```

Relancer ensuite `utop` et charger la bibliothèque avec `#require "mpi-informatique";;`. Les mises à jour de l'image demandent une reconstruction du conteneur ; celles de la bibliothèque n'en demandent pas.

## Codespace personnel

À la création d'un Codespace de ce dépôt, choisir la configuration **MPI personnel** (`.devcontainer/personnel/devcontainer.json`). GitHub demande les droits d'écriture sur `exercices`, `exercices-prive`, `lib` et `cours`.

Les cinq dépôts sont ouverts dans [personnel.code-workspace](personnel.code-workspace). Le profil ajoute Typst, Python, Just, Node.js 22, GitHub CLI, MDX et odoc ; il prépare les dépendances des deux sites et les liens vers le clone public pour Tinymist. Les ports 3000 et 4321 sont prévus pour les sites de cours et d'exercices ; le lecteur des cours pointe vers le site d'exercices du Codespace.

La préparation peut être relancée avec `python3 .devcontainer/personnel/setup.py`. Les clones existants et leurs branches sont conservés. En local, le même outillage est disponible avec `nix develop .#personnel`.

À chaque connexion, les extensions manquantes (Tinymist, OCaml Platform, C/C++, Python…) sont installées et **Exercices MPI**, l’extension enseignant, est récupérée depuis la dernière release GitHub. Pour relancer cette installation : `python3 .devcontainer/personnel/setup.py --attach`.

Le Makefile est celui donné au TP d'informatique à CCINP et permet de simplifier les commandes.  
Par exemple, `make main` est un raccourci pour `gcc -o main.exe -Wall *.c -lm` : il compile tous les fichiers C et produit un exécutable `main.exe`.

> Extrait du rapport CCINP 2024  
> La ligne de compilation gcc -o main.exe -Wall *.c -lm vous permet de créer un exécutable main.exe à partir du ou des fichiers C fournis. Vous pouvez également utiliser l’utilitaire make. En ligne de commande, il suffit d'écrire make. Dans les deux cas, si la compilation réussit, le programme peut être exécuté avec la commande ./main.exe
> Il est possible d'activer davantage d'avertissements et un outil d'analyse de la gestion de la mémoire avec la ligne de compilation gcc -o main.exe -g -Wall -Wextra -fsanitize=address *.c -lm ou en écrivant make safe. L’examinateur pourra vous demander de compiler avec ces options.
> Si vous désirez forcer la compilation de tous les fichiers, vous pouvez au préalable nettoyer le répertoire en faisant make clean et relancer une compilation.

## Utilisation du Codespace par navigateur

1. S'incrire sur [GitHub](https://github.com) (Sign Up).
2. Si vous n'avez pas encore de Codespace : aller sur https://github.com/mpi-informatique/tp-environnement et cliquer sur le bouton Code puis "Create Codespace on main".
   Puis retrouver votre Codespace en cliquant sur le menu en haut à gauche puis "Codespaces".
3. Dans les options du Codespace, déselectionner "Auto-delete codespace" pour éviter qu'il ne soit supprimé après 2 semaines d'inutilisation.

Par défaut, GitHub donne 120h/mois d'utilisation gratuite (180h/mois pour les étudiants).

## Utilisation en local

1. Installez [Docker Desktop](https://www.docker.com/products/docker-desktop/) et [Visual Studio Code](https://code.visualstudio.com/).
2. Clonez ce dépôt, puis installez l’extension [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).
3. Ouvrez le dossier dans VS Code et lancez la commande `Dev Containers: Reopen in Container` ; l’environnement est alors prêt à l’emploi.

## Image Docker

Le Codespace construit l'image à partir de ce dépôt et de `flake.lock` : Debian 13, le même socle Nix et un utilisateur `vscode` avec sudo. La CI vérifie les outils sur Linux/macOS et, en parallèle, construit puis teste l'image Linux avant de la publier sous `ghcr.io/mpi-informatique/tp-environnement:latest`.

```sh
docker build -f .devcontainer/Dockerfile -t mpi-environnement:test .
docker run --rm -i mpi-environnement:test sh -s < .devcontainer/smoke-test.sh
```

## Panneau des TP

Le conteneur installe l'extension [TP MPI](https://github.com/mpi-informatique/vscode-mpi-exercices/tree/main/tp), qui propose les TP commencés, ceux du cours et la banque complète. Cliquer sur un TP ouvre son squelette à gauche et son énoncé PDF à droite. Les travaux sont conservés dans `tp/` ; penser à les sauvegarder dans un dépôt personnel ou à les télécharger.

Les sources de l’extension sont maintenues dans `vscode-mpi-exercices/tp`. À chaque connexion, `.devcontainer/install-extension.sh` récupère [le VSIX de la dernière release stable](https://github.com/mpi-informatique/vscode-mpi-exercices/releases/latest/download/vscode-mpi-tp.vsix) et l’installe avec VS Code. Un fichier inchangé est réutilisé ; la copie en cache reste disponible si le téléchargement ou l’installation de la nouvelle version échoue. Le conteneur n’a plus besoin de compiler l’extension. Recharger la fenêtre après une mise à jour si nécessaire.

La première connexion nécessite une release contenant `vscode-mpi-tp.vsix` et un accès à GitHub. En cas d’échec sans copie en cache, le script affiche un message et réessaie à la prochaine connexion. Le cache est conservé dans `~/.cache/mpi-tp-extension/`.

Pour vérifier le téléchargement, les mises à jour et le fonctionnement hors connexion :

```sh
python3 -m unittest discover -s tests -v
```
