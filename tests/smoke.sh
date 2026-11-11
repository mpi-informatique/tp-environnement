#!/usr/bin/env bash
set -euo pipefail

for tool in cc make sqlite3 dot ocaml ocamlc ocamlopt ocamlfind utop ocamlformat ocamllsp ocamlearlybird opam; do
    command -v "$tool"
done

mpi_test_dir=$(mktemp -d)
trap 'rm -rf "$mpi_test_dir"' EXIT
cd "$mpi_test_dir"
printf '#include <stdio.h>\nint main(void) { puts("C OK"); return 0; }\n' > test.c
if [[ $(uname -s) == Linux ]]; then
    cc -Wall -Wextra -fsanitize=address,undefined test.c -o test-c
else
    cc -Wall -Wextra test.c -o test-c
fi
./test-c
test "$(sqlite3 :memory: 'select 6 * 7;')" = 42
printf 'digraph { a -> b }\n' | dot -Tsvg > graphe.svg
test -s graphe.svg
printf 'let () = assert (List.length [1; 2; 3] = 3); print_endline "OCaml OK"\n' > test.ml
ocaml test.ml
ocamlc test.ml -o test-bytecode
./test-bytecode
ocamlopt test.ml -o test-native
./test-native
printf 'assert (List.length [1; 2; 3] = 3);;\nprint_endline "utop OK";;\n' | utop -init /dev/null -stdin
ocamlformat --enable-outside-detected-project --impl test.ml > formatted.ml
ocamlc formatted.ml -o test-formatted
./test-formatted
ocamllsp --version
ocamlearlybird --help > /dev/null
opam --version
