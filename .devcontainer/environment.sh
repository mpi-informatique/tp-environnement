# Activation du socle Nix et du switch opam personnel.
. /opt/mpi-environnement/activate
if [ -d "$HOME/.opam/default" ]; then
    eval "$(opam env --switch=default --set-switch 2>/dev/null)"
    export OCAMLPATH="$HOME/.opam/default/lib:$OCAMLPATH"
fi
