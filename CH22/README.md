# CHAPTER 22 – Applications in Geomorphology

## 22.8 Physical Geomorphometry in Digital Geomorphological Mapping

Subchapter Physical geomorphometry in digital geomorphological mapping (DGM) recommends a detailed digital geomorphological mapping procedure that uses the theory and methods of physical geomorphometry ([Minár et al., 2024](https://doi.org/10.1016/j.earscirev.2023.104631)). Physical geomorphometry is used in DEM preprocessing, which involves generalizing it to a level most suitable for finding elementary forms, selecting and calculating physically most interpretable local point-based geomorphometric variables, and finally in the actual segmentation procedure, using GEOBIA.

To replicate the basic steps of physically based digital geomorphological mapping (Fig. 22.11), you can use the following software packages from the [Physical Geomorphometric Tools](https://xiceph.github.io/physical-geomorphometry-tools/):

1. [generalization](https://github.com/xiceph/physical-geomorphometry-tools/tree/main/generalization) – for generalizing DEMs using Quadric Error Metrics (QEM),
2. [lsp-calculator](https://github.com/xiceph/physical-geomorphometry-tools/tree/main/lsp-calculator) – for the calculation of a comprehensive set of local land surface parameters used as an input to the physically based segmentation,
3. [segmentation](https://github.com/xiceph/physical-geomorphometry-tools/tree/main/segmentation) – for the physically based elementary land surface segmentation.

Each package includes detailed installation and usage instructions, including access to the source codes.
