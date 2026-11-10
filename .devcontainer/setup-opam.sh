#!/bin/sh
set -eu
. /etc/mpi-environment.sh
opam init --bare --disable-sandboxing --no-setup -y
opam switch create default ocaml-system -y
eval "$(opam env --switch=default --set-switch)"
opam pin add mpi-informatique 'git+https://github.com/mpi-informatique/lib.git#main' -y --jobs=2
opam clean --all-switches --download-cache -y
