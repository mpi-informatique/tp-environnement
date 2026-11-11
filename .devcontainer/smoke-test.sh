#!/bin/sh
# Run as the normal Codespaces user before publishing an image.
set -eu
. /etc/mpi-environment.sh
for tool in gcc gdb make sqlite3 ocaml ocamlc ocamlopt utop ocamlformat ocamlformat-rpc ocamllsp ocamlearlybird git nix opam; do
    command -v "$tool"
done
test "$(id -u)" -ne 0
test -w "$HOME"

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
cd "$tmp_dir"
# Reproduce the locale inherited by Codespaces terminals. Bash can exit zero
# despite setlocale warnings, so also require empty stderr.
locale -a | grep -Fx 'en_US.utf8'
env -u LC_ALL LANG=en_US.UTF-8 LC_CTYPE=en_US.UTF-8 LC_COLLATE=en_US.UTF-8 \
    bash --noprofile --norc -c 'locale charmap' > locale.out 2> locale.err
test "$(cat locale.out)" = UTF-8
if test -s locale.err; then
    cat locale.err >&2
    exit 1
fi
printf '#include <stdio.h>\nint main(void) { puts("C OK"); return 0; }\n' > test.c
printf 'all:\n\tgcc -g -Wall -Wextra -fsanitize=address,undefined test.c -o test-c\n' > Makefile
make
./test-c
gdb --batch -ex 'file test-c' -ex 'info functions main'
test "$(sqlite3 :memory: 'select 6 * 7;')" = 42
printf 'let () = print_endline "OCaml OK"\n' > test.ml
ocaml test.ml
ocamlc test.ml -o test-bytecode
./test-bytecode
ocamlopt test.ml -o test-native
./test-native
printf 'print_endline "utop OK";;\n' | utop -init /dev/null -stdin
test "$(ocamlc -version)" = "$(opam var ocaml:version)"
printf '#require "mpi-informatique";;\nlet a = Mpi.Automate.creer ~nb_etats:2 ~initiaux:[0] ~finaux:[1] ~transitions:[(0, Some "a", 1)];;\nassert (Mpi.Automate.nb_etats a = 2);;\nMpi.Dot.ecrire "automate.dot" (Mpi.Dot.automate ~symbole:Fun.id a);;\n' | utop -init /dev/null -stdin
dot -Tsvg automate.dot -o automate.svg
grep -q '<text' automate.svg
test -w "$HOME/.opam/default"
nix --version
bash --login -c 'command -v nix; test "$(dune --version)" = "$(/opt/mpi-environnement/bin/dune --version)"'
ocamlformat --enable-outside-detected-project --impl test.ml > formatted.ml
ocamlc formatted.ml -o test-formatted
./test-formatted
ocamllsp --version
ocamlearlybird --help > /dev/null
