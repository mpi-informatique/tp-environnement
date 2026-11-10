#!/usr/bin/env python3
"""Préparer les clones et dépendances du Codespace personnel."""

import argparse
from pathlib import Path
import subprocess

REPOSITORIES = ("exercices", "exercices-prive", "lib", "cours")
ROOT = Path(__file__).resolve().parents[2]


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
    args = parser.parse_args()
    try:
        clone_repositories(ROOT.parent)
        if not args.clones_only:
            install_dependencies(ROOT.parent)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f"Préparation interrompue : {error}") from error
    print(f"Espace de travail : {ROOT / 'personnel.code-workspace'}")


if __name__ == "__main__":
    main()
