#!/bin/sh
# Codespaces fournit la commande code ; Node est installé par la feature du conteneur.
set -eu
repo_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
build_dir="$HOME/.cache/mpi-tp-extension"
mkdir -p "$build_dir/tp-environnement"
# Le package partagé est construit avec les deux extensions, sans dépendance au site à l'exécution.
if [ ! -d "$build_dir/exercices/.git" ]; then
    git clone --depth 1 --filter=blob:none --sparse https://github.com/mpi-informatique/exercices.git "$build_dir/exercices"
    git -C "$build_dir/exercices" sparse-checkout set shared
fi
# Ne reconstruire qu'après une modification des sources de cette extension.
if [ ! -f "$build_dir/extension.sha256" ] || ! (cd "$repo_dir/extension" && find src scripts media -type f -exec sha256sum {} + && sha256sum package.json package-lock.json) | cmp -s - "$build_dir/extension.sha256"; then
    git -C "$build_dir/exercices" pull --ff-only
    rm -rf "$build_dir/tp-environnement/extension"
    mkdir -p "$build_dir/tp-environnement/extension"
    cp -R "$repo_dir/extension/src" "$repo_dir/extension/scripts" "$repo_dir/extension/media" "$build_dir/tp-environnement/extension/"
    cp -R "$repo_dir/extension/test" "$build_dir/tp-environnement/extension/"
    cp "$repo_dir/extension/package.json" "$repo_dir/extension/package-lock.json" "$repo_dir/extension/tsconfig.json" "$repo_dir/extension/.vscodeignore" "$repo_dir/extension/README.md" "$build_dir/tp-environnement/extension/"
    (cd "$build_dir/tp-environnement/extension" && npm ci && npm run package)
    (cd "$repo_dir/extension" && find src scripts media -type f -exec sha256sum {} + && sha256sum package.json package-lock.json) > "$build_dir/extension.sha256"
fi
code --install-extension "$build_dir/tp-environnement/extension/releases/vscode-mpi-tp-0.1.0.vsix" --force
