#!/usr/bin/env nix-shell
with import <nixpkgs> {};
stdenv.mkDerivation {
    name = "kantek";
    buildInputs = [ arangodb ];
    GLIBCXX_FORCE_NEW=1;
    ICU_DATA=/nix/store/56c165jppakz3g0pz725hz9h9sjfsjaj-arangodb-3.4.7/share/arangodb3;
    shellHook = ''
        sudo -Eu arangodb arangod --configuration /etc/arangodb3/arangod.conf
        exit
     '';

}

