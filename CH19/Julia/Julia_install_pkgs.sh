juliaup add 1.11  # Install Julia 1.11
julia +1.11 --project -e "using Pkg; Pkg.instantiate()"  # Install dependencies