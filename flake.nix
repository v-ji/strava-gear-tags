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
          python-dotenv
          pillow
          types-pillow
        ];

      # Create Python environment
      getPythonEnv =
        pkgs: extraPackages:
        (pythonVersion pkgs).withPackages (ps: getPythonPackages pkgs ps ++ extraPackages ps);
    in
    {
      devShells = forAllSystems (
        { pkgs }:
        {
          default = pkgs.mkShell {
            packages = [ (getPythonEnv pkgs (ps: [ ])) ];
          };
        }
      );

      # Add uvicorn app
      packages = forAllSystems (
        { pkgs }:
        {
          default = pythonVersion.buildPythonApplication {
            pname = "strava-gear-stats";
            version = "0.1.0";
            format = "setuptools";

            src = ./.;

            propagatedBuildInputs = [ (getPythonEnv pkgs (ps: [ ])) ];
            # meta = with lib; {
            #   ...
            # };
          };
        }
      );

    };
}
