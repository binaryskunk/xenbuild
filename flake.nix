{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  
  outputs = { self, nixpkgs, ... }: let
    systems = [ "x86_64-linux" "aarch64" ];

    forEachSystem = f: with nixpkgs.lib; foldAttrs mergeAttrs {}
      (lists.forEach systems (system:
        mapAttrs (name: value: { ${system} = value; }) (f system)
      ));
  in forEachSystem (system: let
    pkgs = nixpkgs.legacyPackages.${system};
  in rec {
    devShells.default = pkgs.mkShell {
      packages = with pkgs; [
        clang
        ccache
        graphviz
        python313
        python313Packages.graphviz
        pre-commit
        cppcheck
        cpplint
        include-what-you-use
      ];

      shellHook = ''
        export PKG_CONFIG_PATH=${pkgs.sdl3.dev}/lib/pkgconfig:${pkgs.fmt.dev}/lib/pkgconfig:$PKG_CONFIG_PATH

        export CC=$(readlink -f $(which clang))
        export CXX=$(readlink -f $(which clang++))

        export PS1="\u:\w $ "
      '';
    };
  });
}
