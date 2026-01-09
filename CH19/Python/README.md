# Geomorphometry Using Open-Source Programming Languages: Python

This section of the repository contains code needed to run the Python code examples from the chapter "Geomorphometry Using Open-Source Programming Languages" from the second edition of the book *Geomorphometry: Software, Concepts, Applications*.

The Anaconda/Miniconda Python distribution can be downloaded and installed from https://www.anaconda.com/download

## Packages
- On macOS/Linux open a terminal. On Windows, open Anaconda Prompt.
- If you don't have mamba: 
  - Run the code
   ```bash
   conda install -n base -c conda-forge mamba
   ```
- Navigate to the `Python` subdirectory of this project using `cd`
  - Then, run the code:
  ```bash
  mamba env create -f py_environment.yml
  ```
  or equivalently on macOS/Linux using a shell script via
  ```bash
  bash Python_install_pkgs.sh
  ```
- This has created a new conda environment called `xdem-geomorpho` containing all 
the needed dependency packages. We can confirm this by listing all conda environments 
using the following code:
  ```bash
  conda env list
  ```
      
## Chapter Code

The code examples from the Python section of the chapter are contained within `Python_script.py`.
The code assumes your working directory as the Python subfolder of this project.
Additionally, make sure that the `xdem-geomorpho` conda environment, rather than 
the `base` conda environment, is active. If running through the terminal/Anaconda Prompt, 
this can be done using the following  code which first activates the proper conda 
environment, and then launches python.
```
conda activate xdem-geomorpho
python
```
If working in an IDE, follow instructions specific to that IDE to select a 
"Python interpreter" and set it as the `xdem-geomorpho` conda environment.
