# Julia

The latest version of Julia can be downloaded from [the Julia website](https://julialang.org/install/).
It will install the *juliaup* installation manager, which allows you to install and update any Julia version.
By default, you will receive the latest release, which is 1.11.2 at the moment of writing. 
Please do not use the version of Julia shipped by Linux package managers, as they are often outdated.

To reproduce the code examples in this chapter, you will need to do:

```bash
juliaup add 1.11  # Install Julia 1.11
julia +1.11 --project -e 'using Pkg; Pkg.instantiate()'  # Install dependencies
```

Now you can execute the code in this chapter by running the Julia REPL with `julia +1.11 --project` and then including (snippets from) `main.jl`.
