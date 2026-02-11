{
  description = "Strava Gear Stats";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
  };

  outputs =
    {
      self,
      nixpkgs,
    }:
    let
      # Systems supported
      defaultSystems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      # Helper to provide system-specific attributes
      forAllSystems =
        f: nixpkgs.lib.genAttrs defaultSystems (system: f { pkgs = import nixpkgs { inherit system; }; });

      pythonVersion = pkgs: pkgs.python312;

      # Define Python packages
      getPythonPackages =
        pkgs: ps: with ps; [
          fastapi
          uvicorn
          stravalib
          pillow
          types-pillow
        ];

      # Create Python environment
      getPythonEnv =
        pkgs: extraPackages:
        (pythonVersion pkgs).withPackages (ps: getPythonPackages pkgs ps ++ extraPackages ps);

      getFontPath = pkg: pkg.outPath + "/share/fonts/truetype";
    in
    {
      devShells = forAllSystems (
        { pkgs }:
        {
          default = pkgs.mkShell {
            packages = [
              (getPythonEnv pkgs (ps: [ ]))
              pkgs.dinish
            ];
            DINISH_FONT_PATH = getFontPath pkgs.dinish;
          };
        }
      );

      packages = forAllSystems (
        { pkgs }:
        {
          default = pkgs.python3Packages.buildPythonApplication rec {
            pname = "strava-gear-tags";
            version = "0.1.0";
            pyproject = true;

            src = ./.;

            dependencies = getPythonPackages pkgs pkgs.python3Packages;
            build-system = [ pkgs.python3Packages.hatchling ];
            buildInputs = [ pkgs.dinish ];
            makeWrapperArgs = [ "--set DINISH_FONT_PATH ${getFontPath pkgs.dinish}" ];

            meta = {
              mainProgram = pname;
            };
          };
        }
      );

      # Define applications that can be run directly (e.g., `nix run .`)
      apps = forAllSystems (
        { pkgs }:
        {
          default = {
            type = "app";
            program = pkgs.lib.getExe self.packages.${pkgs.system}.default;
          };
        }
      );
    };
}
