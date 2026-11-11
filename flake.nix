{
  description = "Socle OCaml et C commun aux dépôts MP2I/MPI";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs";

  outputs = { self, nixpkgs }:
    let
      systems = [ "aarch64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
      toolchains = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          # MDX et utop doivent partager la même variante de logs.
          ocaml = pkgs.ocamlPackages.overrideScope (final: previous: {
            mdx = previous.mdx.override { logs = final.logs; };
            # Le parseur DAP ne doit pas chercher un ':' au-delà de la fin des
            # en-têtes, sinon l'initialisation de VS Code attend indéfiniment.
            dap = previous.dap.overrideAttrs (old: {
              postPatch = (old.postPatch or "") + ''
                substituteInPlace src/debug_rpc/debug_rpc.ml \
                  --replace-fail '(take_till is_colon <* colon)' '(take_while1 (fun c -> not (is_colon c || is_eol c)) <* colon)'
              '';
            });
          });
          tools = [
            ocaml.ocaml ocaml.dune_3 ocaml.findlib ocaml.utop ocaml.ocamlformat ocaml.ocaml-lsp ocaml.earlybird
            pkgs.stdenv.cc pkgs.gnumake pkgs.sqlite pkgs.graphviz pkgs.opam pkgs.pkg-config
            pkgs.patch pkgs.diffutils pkgs.bzip2
          ] ++ pkgs.lib.optionals pkgs.stdenv.hostPlatform.isLinux [ pkgs.gdb ];
          toplevel = "${ocaml.findlib}/lib/ocaml/${ocaml.ocaml.version}/site-lib";
          fonts = pkgs.makeFontsConf { fontDirectories = [ pkgs.dejavu_fonts ]; };
        in { inherit pkgs ocaml tools toplevel fonts; });
      mkShell = system: extra:
        let inherit (toolchains.${system}) pkgs tools toplevel fonts; in
        pkgs.mkShell ({ OCAML_TOPLEVEL_PATH = toplevel; FONTCONFIG_FILE = fonts; } // extra // {
          packages = tools ++ (extra.packages or [ ]);
        });
      mkEnvironment = system: extra:
        let
          inherit (toolchains.${system}) pkgs tools toplevel fonts;
          packages = tools ++ (extra.packages or [ ]);
          binaries = pkgs.buildEnv {
            name = "mpi-tools";
            paths = packages;
            pathsToLink = [ "/bin" ];
          };
        in pkgs.runCommand "mpi-environnement" ({ buildInputs = packages; } // builtins.removeAttrs extra [ "packages" ]) ''
          mkdir -p "$out"
          ln -s ${binaries}/bin "$out/bin"
          {
            printf 'export PATH=%s:"$PATH"\n' ${binaries}/bin
            printf 'export OCAML_TOPLEVEL_PATH=%s\n' ${toplevel}
            printf 'export FONTCONFIG_FILE=%s\n' ${fonts}
            for variable in OCAMLPATH CAML_LD_LIBRARY_PATH; do
              if [[ -v "$variable" ]]; then
                printf 'export %s=%q:"''${%s-}"\n' "$variable" "''${!variable}" "$variable"
              fi
            done
            for variable in TYPST_FONT_PATHS TYPST_PACKAGE_PATH; do
              if [[ -v "$variable" ]]; then
                printf 'export %s=%q\n' "$variable" "''${!variable}"
              fi
            done
          } > "$out/activate"
        '';
    in {
      lib = { inherit systems mkShell mkEnvironment; };
      legacyPackages = toolchains;
      devShells = forAllSystems (system: {
        default = mkShell system { };
      });
      packages = forAllSystems (system: {
        default = mkEnvironment system { };
      });
      checks = forAllSystems (system:
        let inherit (toolchains.${system}) pkgs tools toplevel fonts; in {
          tools = pkgs.runCommand "mpi-tools-check" {
            nativeBuildInputs = tools ++ [ pkgs.python3 ];
            OCAML_TOPLEVEL_PATH = toplevel;
            FONTCONFIG_FILE = fonts;
          } ''
            bash ${self}/tests/smoke.sh
            python3 ${self}/tests/earlybird-smoke.py
            touch "$out"
          '';
        });
    };
}
