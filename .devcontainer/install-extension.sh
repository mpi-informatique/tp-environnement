#!/bin/sh
# Codespaces fournit la commande code ; curl télécharge le VSIX publié sur GitHub.
set -eu
cache_dir=${MPI_TP_EXTENSION_CACHE:-"$HOME/.cache/mpi-tp-extension"}
release_url=${MPI_TP_EXTENSION_URL:-https://github.com/mpi-informatique/vscode-mpi-exercices/releases/latest/download/vscode-mpi-tp.vsix}
mkdir -p "$cache_dir"
vsix="$cache_dir/vscode-mpi-tp.vsix"
etag="$cache_dir/release.etag"
temporary=$(mktemp -d "$cache_dir/download.XXXXXX")
trap 'rm -rf "$temporary"' EXIT
trap 'exit 1' HUP INT TERM

# L’ETag évite de télécharger un VSIX inchangé. Sans fichier local, forcer le téléchargement.
set --
if [ -s "$vsix" ] && [ -s "$etag" ]; then
    set -- --etag-compare "$etag"
fi
if status=$(curl --fail --location --silent --show-error --connect-timeout 5 --max-time 45 --etag-save "$temporary/release.etag" "$@" --output "$temporary/vscode-mpi-tp.vsix" --write-out '%{http_code}' "$release_url"); then
    if [ "$status" = 304 ] && [ -s "$vsix" ]; then
        code --install-extension "$vsix" --force
        exit 0
    fi
    if [ "$status" = 200 ] && [ -s "$temporary/vscode-mpi-tp.vsix" ]; then
        # VS Code valide le nouveau VSIX avant de remplacer la copie en cache.
        if code --install-extension "$temporary/vscode-mpi-tp.vsix" --force; then
            mv "$temporary/vscode-mpi-tp.vsix" "$vsix"
            mv "$temporary/release.etag" "$etag"
            exit 0
        fi
    fi
fi

if [ -s "$vsix" ]; then
    echo 'TP MPI : mise à jour indisponible, utilisation de la version en cache.' >&2
    code --install-extension "$vsix" --force
else
    echo 'TP MPI : impossible de récupérer la dernière release GitHub et aucune version en cache. Réessayer à la prochaine connexion.' >&2
    exit 1
fi
