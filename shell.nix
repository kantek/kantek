#!/usr/bin/env nix-shell
with import <nixpkgs> {};
stdenv.mkDerivation {
    name = "kantek";
    buildInputs = [ arangodb_3_5 ];
    GLIBCXX_FORCE_NEW=1;
    ICU_DATA="${arangodb_3_5.outPath}/share/arangodb3";
    shellHook = ''
        sudo -Eu arangodb arangod --configuration /etc/arangodb3/arangod.conf
        exit
     '';

}

