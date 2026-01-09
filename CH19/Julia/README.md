# Geomorphometry Using Open-Source Programming Languages: Julia

This section of the repository contains code needed to run the Julia code examples from the chapter "Geomorphometry Using Open-Source Programming Languages" from the second edition of the book *Geomorphometry: Software, Concepts, Applications*.

Julia can be downloaded and installed from https://julialang.org/install/

## Packages

To install dependencies:
- Open a terminal:
  - macOS / Linux / [WSL](https://learn.microsoft.com/en-us/windows/wsl/install) / [Git Bash](https://git-scm.com/install/windows), **or**
  - Windows Command Prompt (`cmd`)
  - Navigate to the `Julia` subdirectory of this project using `cd`
  - Then, run the code:
  ```bash
  juliaup add 1.11
  julia +1.11 --project -e "using Pkg; Pkg.instantiate()"
  ```
  or equivalently on macOS/Linux using a shell script via
  ```bash
  bash Julia_install_pkgs.sh
  ```

## Chapter Code

The code examples from the Julia section of the chapter are contained within `Julia_script.jl`.
The code assumes your working directory as the Julia subfolder of this project.

Note: The `Julia_script.jl` is dependent on Julia 1.11. Launching Julia REPL with version 1.11 can be done 
in a terminal or Windows `cmd` by entering `julia +1.11`. There are however compatibility issues between juliaup and and Git Bash,
so attempting to launch julia from within Git Bash may not work. If using VS Code, 
you can also set your default version of Julia to 1.11 using `juliaup default 1.11` 
in a terminal or Windows `cmd` prior to launching VS Code.