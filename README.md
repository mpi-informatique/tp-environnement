# Environnement de développement pour les TP de MPI avec Visual Studio Code

Contient :
- `utop` comme interpréteur interactif OCaml
- `gcc` comme compilateur C (exemple : `gcc test.c` puis ./a.out)
- `ocaml` pour exécuter un fichier OCaml (exemple : `ocaml test.ml`)
- `ocamlopt` pour compiler un fichier OCaml (exemple : `ocamlopt test.ml` puis ./a.out)
- `sqlite3` pour gérer des bases de données SQLite.

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

L'image Docker est [`ghcr.io/mpi-lamartin/environnement:latest`](https://github.com/mpi-lamartin/environnement/pkgs/container/environnement), elle utilise Debian 13 (`trixie-slim`) et un utilisateur `vscode` avec sudo.

```sh
docker build -t mpi-environnement:test .devcontainer
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
