#!/bin/sh
# Codespaces fournit la commande code ; Node est installé par la feature du conteneur.
set -eu
build_dir="$HOME/.cache/mpi-tp-extension"
# Mettre à jour ces révisions pour déployer une nouvelle construction dans le conteneur.
extension_revision=fdc1b601de86e093866c8f319d8cf912bcae1c6c
shared_revision=d80dd95c7adc63a6f2ec222e413698c8eeb848f1

checkout_sources() {
    repository=$1
    revision=$2
    directory=$3
    subdirectory=$4
    if [ ! -d "$directory/.git" ]; then
        git clone --depth 1 --filter=blob:none --sparse "$repository" "$directory"
    fi
    git -C "$directory" sparse-checkout set "$subdirectory"
    if [ "$(git -C "$directory" rev-parse HEAD)" != "$revision" ]; then
        git -C "$directory" fetch --depth 1 origin "$revision"
        git -C "$directory" checkout --detach FETCH_HEAD
    fi
}

mkdir -p "$build_dir"
checkout_sources https://github.com/mpi-informatique/vscode-mpi-exercices.git "$extension_revision" "$build_dir/vscode-mpi-exercices" tp
checkout_sources https://github.com/mpi-informatique/exercices.git "$shared_revision" "$build_dir/exercices" shared
extension_dir="$build_dir/vscode-mpi-exercices/tp"
package_file=$(node -e 'const p = require(process.argv[1]); process.stdout.write(`${p.name}-${p.version}.vsix`)' "$extension_dir/package.json")
vsix="$extension_dir/releases/$package_file"
build_key="$extension_revision:$shared_revision"
# Une révision déjà construite ne nécessite ni réseau ni réinstallation des dépendances.
if [ ! -f "$vsix" ] || [ ! -f "$build_dir/build.key" ] || [ "$(cat "$build_dir/build.key")" != "$build_key" ]; then
    (cd "$extension_dir" && npm ci && npm run package)
    printf '%s\n' "$build_key" > "$build_dir/build.key"
fi
code --install-extension "$vsix" --force
