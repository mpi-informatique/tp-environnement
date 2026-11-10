#!/usr/bin/env python3
"""Préparer les clones et dépendances du Codespace personnel."""

import argparse
import json
import os
from pathlib import Path
import subprocess

REPOSITORIES = ("exercices", "exercices-prive", "lib", "cours")
ROOT = Path(__file__).resolve().parents[2]


def install_extensions():
    config = json.loads((ROOT / ".devcontainer/personnel/devcontainer.json").read_text())
    installed = set(subprocess.check_output(["code", "--list-extensions"], text=True).lower().splitlines())
    for extension in config["customizations"]["vscode"]["extensions"]:
        if extension.lower() not in installed:
            subprocess.run(["code", "--install-extension", extension], check=True)
    env = dict(os.environ,
        MPI_TP_EXTENSION_URL="https://github.com/mpi-informatique/vscode-mpi-exercices/releases/latest/download/vscode-mpi-exercices.vsix",
        MPI_TP_EXTENSION_CACHE=str(Path.home() / ".cache/mpi-exercices-extension"),
        MPI_EXTENSION_NAME="Exercices MPI",
    )
    subprocess.run(["sh", str(ROOT / ".devcontainer/install-extension.sh")], env=env, check=True)


def open_workspace(marker=Path("/tmp/mpi-personnel-workspace-opened")):
    # Ouvrir le workspace reconnecte VS Code et relance postAttachCommand.
    try:
        marker.mkdir()
    except FileExistsError:
        return
    try:
        subprocess.run(["code", "--reuse-window", str(ROOT / "personnel.code-workspace")], check=True)
    except (OSError, subprocess.CalledProcessError):
        marker.rmdir()
        raise


def normalize_origin(origin):
    return origin.replace("git@github.com:", "https://github.com/").replace("ssh://git@github.com/", "https://github.com/").rstrip("/").removesuffix(".git")


def clone_repositories(parent, origins=None):
    parent.mkdir(parents=True, exist_ok=True)
    origins = origins or {name: f"https://github.com/mpi-informatique/{name}.git" for name in REPOSITORIES}
    for name, origin in origins.items():
        target = parent / name
        if target.exists():
            result = subprocess.run(["git", "-C", str(target), "rev-parse", "--show-toplevel"], text=True, capture_output=True)
            if result.returncode or Path(result.stdout.strip()).resolve() != target.resolve():
                raise RuntimeError(f"Le dossier {target} existe et n'est pas un dépôt Git autonome.")
            current_origin = subprocess.check_output(["git", "-C", str(target), "remote", "get-url", "origin"], text=True).strip()
            if normalize_origin(current_origin) != normalize_origin(origin):
                raise RuntimeError(f"Le dépôt {target} n'a pas l'origine attendue.")
            print(f"Conservé : {target}", flush=True)
            continue
        print(f"Clonage de mpi-informatique/{name}", flush=True)
        subprocess.run(["git", "clone", "--filter=blob:none", origin, str(target)], check=True)


def install_dependencies(parent):
    private = parent / "exercices-prive"
    subprocess.run(["nix", "develop", ".", "-c", "just", "install"], cwd=private, check=True)
    for project in (parent / "cours", parent / "exercices/web"):
        subprocess.run(["npm", "ci", "--no-audit", "--no-fund"], cwd=project, check=True)
    subprocess.run(["nix", "develop", ".", "-c", "dune", "build"], cwd=parent / "lib", check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clones-only", action="store_true", help="Cloner les dépôts sans préparer les dépendances.")
    parser.add_argument("--open-workspace", action="store_true", help="Ouvrir l'espace de travail une seule fois par conteneur.")
    parser.add_argument("--attach", action="store_true", help="Installer les extensions puis ouvrir l'espace de travail.")
    args = parser.parse_args()
    if args.attach:
        install_extensions()
        open_workspace()
        return
    if args.open_workspace:
        open_workspace()
        return
    try:
        clone_repositories(ROOT.parent)
        if not args.clones_only:
            install_dependencies(ROOT.parent)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Préparation interrompue : {error}") from error
    print(f"Espace de travail : {ROOT / 'personnel.code-workspace'}")


if __name__ == "__main__":
    main()
