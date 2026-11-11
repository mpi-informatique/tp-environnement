# syntax=docker/dockerfile:1
FROM nixos/nix:2.34.7 AS tools
ENV NIX_CONFIG="experimental-features = nix-command flakes"
COPY flake.nix flake.lock /src/
RUN nix build "/src#default" --out-link /opt/mpi-environnement && nix store gc

FROM debian:trixie-slim AS locale-data
RUN apt-get update \
    && apt-get install -y --no-install-recommends locales \
    && localedef -i en_US -f UTF-8 en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

FROM debian:trixie-slim
LABEL org.opencontainers.image.source="https://github.com/mpi-informatique/tp-environnement"
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git openssh-client procps sudo \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 --shell /bin/bash vscode \
    && printf 'vscode ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

COPY --from=tools --chown=vscode:vscode /nix /nix
COPY --from=tools /opt/mpi-environnement /opt/mpi-environnement
COPY --from=locale-data /usr/lib/locale/locale-archive /usr/lib/locale/locale-archive
RUN mkdir -p /etc/nix \
    && printf '%s\n' 'experimental-features = nix-command flakes' 'build-users-group =' 'sandbox = false' > /etc/nix/nix.conf
ENV PATH="/opt/mpi-environnement/bin:/home/vscode/.opam/default/bin:/nix/var/nix/profiles/default/bin:${PATH}" \
    LANG=C.UTF-8

COPY .devcontainer/environment.sh /etc/mpi-environment.sh
COPY .devcontainer/setup-opam.sh /etc/mpi-setup-opam.sh
COPY .devcontainer/terminal-help.sh /etc/mpi-terminal-help.sh
RUN printf '\n. /etc/mpi-environment.sh\n' >> /etc/bash.bashrc \
    && printf '. /etc/mpi-environment.sh\n' > /etc/profile.d/mpi.sh \
    && printf '\n. /etc/mpi-terminal-help.sh\n' >> /home/vscode/.bashrc

USER vscode
WORKDIR /home/vscode
RUN sh /etc/mpi-setup-opam.sh
CMD ["/bin/bash"]
