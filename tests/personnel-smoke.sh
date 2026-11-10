#!/usr/bin/env bash
set -euo pipefail
if [[ -f /etc/mpi-environment.sh ]]; then
    . /etc/mpi-environment.sh
fi
for tool in typst just python3 node npm gh rg ocaml-mdx odoc; do
    command -v "$tool"
done
node -e 'if (Number(process.versions.node.split(".")[0]) < 22) process.exit(1)'
python3 -c 'import tomllib'
mpi_test_dir=$(mktemp -d)
trap 'rm -rf "$mpi_test_dir"' EXIT
printf 'MPI $x^2$\n' > "$mpi_test_dir/test.typ"
typst compile "$mpi_test_dir/test.typ" "$mpi_test_dir/test.pdf"
test -s "$mpi_test_dir/test.pdf"
gh --version
