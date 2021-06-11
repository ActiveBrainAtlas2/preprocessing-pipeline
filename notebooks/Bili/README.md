# Bili's Workspace

I'm wrapping up all my work here, to make it easier for someone else to pick up.

## Directory Structure

- `data`: data files generated and used by the notebooks
- `notebook`: the main place for my work
- `old`: all the old stuff not useful for the current work

## Notebook List
Some of the notebooks contain large graphics, and are easier to view in nbviewer.

### Rough Alignment
- [[nbviewer](https://nbviewer.jupyter.org/github/eddyod/pipeline_utility/blob/master/notebooks/Bili/notebook/rough-alignment-1-image-registration.ipynb)]
[Rough Alignment 1: Image Registration](notebook/rough-alignment-1-image-registration.ipynb)
demonstrates doing image registrations (affine & Demons) using SimpleITK.
- [[nbviewer](https://nbviewer.jupyter.org/github/eddyod/pipeline_utility/blob/master/notebooks/Bili/notebook/rough-alignment-2-diagnostic-plot.ipynb)]
[Rough Alignment 1: Diagnostic Plot](notebook/rough-alignment-2-diagnostic-plot.ipynb) demonstrates how to generate diagnostic plots for the SimpleTK transformations the in the format of PDF.
- [[nbviewer](https://nbviewer.jupyter.org/github/eddyod/pipeline_utility/blob/master/notebooks/Bili/notebook/rough-alignment-3-initial-coms.ipynb)]
[Rough Alignment 3: Initial COMs](notebook/rough-alignment-3-initial-coms.ipynb)
demonstrates how to also transform the COMs along with the images.

### Landmark Registration
- [[nbviewer](https://nbviewer.jupyter.org/github/eddyod/pipeline_utility/blob/master/notebooks/Bili/notebook/landmark-registration-analytical.ipynb)]
[Landmark Registration: Analytical](notebook/landmark-registration-analytical.ipynb)
describes a closed-form analytical solution of landmark registration assuming the rigid + unform scaling transformation and the squared error metric.
- [[nbviewer](https://nbviewer.jupyter.org/github/eddyod/pipeline_utility/blob/master/notebooks/Bili/notebook/landmark-registration-pytorch.ipynb)]
[Landmark Registration: PyTorch](notebook/landmark-registration-pytorch.ipynb)
demonstrates how to set up a general framework for landmark registration using PyTorch.

### Miscellaneous
- [[nbviewer](https://github.com/eddyod/pipeline_utility/blob/master/notebooks/Bili/notebook/alignment-error-visualization.ipynb)]
[Alignment Error Visualization](notebook/alignment-error-visualization.ipynb)
generates the box plots for alignment errors. It can be easily extended to include more brains in the future.

## Reproduction Notes
- Everything were ran on ratto. But they shall work on other machines too, assuming there is access to the required data.
- The root repo is assumed to be placed as `~/programming/pipeline_utility`.
- I manage my Python environment using Conda. And I think that's the easiest way to set up the reproduction environment.
    - Use `conda env create -n pipeline -f environment.yml` to create a Conda environment named `pipeline`.
    - Use `conda activate pipeline` to activate the environment.
    - Use `conda env update -n pipeline -f environment.yml --prune` to update the environment.
- Database credentials are needed to access the database. Ask Ed for it.
