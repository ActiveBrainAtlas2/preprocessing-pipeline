# Bili's Workspace

I'm wrapping up all my work here, to make it easier for someone else to pick up.

## Notebooks
Here are the brief descriptions of the notebooks I have:

### Rough Alignment
These notebooks contains the current explorations of the new automatic alignment pipeline. It has 3 steps.

- [automatic-alignment-1-rough-alignment.ipynb](notebook/automatic-alignment-1-rough-alignment.ipynb) describes step 1 of rough alignment.
- [automatic-alignment-1-rough-alignment-diagnostics.ipynb](notebook/automatic-alignment-1-rough-alignment-diagnostics.ipynb) makes some disgnostic plots for step 1.
- [automatic-alignment-2-detection-initial-coms.ipynb](notebook/automatic-alignment-2-detection-initial-coms.ipynb) describes step 2 of preparing the COMs for Kui's detection.

### Landmark-based Alignment
- [rigid alignment](TBD).
- [example-landmark-registration-pytorch.ipynb](notebook/example-landmark-registration-pytorch.ipynb) demonstrates how to use PyTorch to do the landmark registration.

### Error Visualization
- [reference-alignment-error.ipynb](notebook/reference-alignment-error.ipynb) generates the box plots for alignment errors. It can be extended to include more brains in the future.

## Directory Structure

- `old`: all the old stuff
- `data`: a place for data files
- `notebook`: polished notebooks
<!-- - `script`: command line scripts -->
<!-- - `toolbox`: reusable code to be integrated into the pipeline -->

## Reproduction Notes

- Everything are assumed to run on ratto.
- The root repo is assumed to be placed as `~/programming/pipeline_utility`.
- I manage my Python environment using Conda. And that's the easiest way to set up the reproduction environment.
    - Use `conda env create -n pipeline -f environment.yml` to create a Conda environment named `pipeline`.
    - Use `conda activate pipeline` to activate the environment.
    - Use `conda env update -n pipeline -f environment.yml --prune` to update the environment.
- Database credentials are needed to access the database. Ask Ed for it.
