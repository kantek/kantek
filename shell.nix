#!/usr/bin/env nix-shell
with import <nixpkgs> {};
stdenv.mkDerivation {
    name = "postgres";
    buildInputs = [ postgresql ];
    shellHook =
  ''
    export PGDATA=~/main/db/postgres
    mkdir -p $PGDATA
    initdb
    sudo mkdir /run/postgresql
    sudo chown $USER:users /run/postgresql
    pg_ctl -l /tmp/postgres.log start
    tail -f /tmp/postgres.log
    exit
  '';
}

