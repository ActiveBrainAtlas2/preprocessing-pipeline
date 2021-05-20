# Bili's Workspace

I'm wrapping up all my work here, to make it easier for someone else to pick up.

## Directory Structure

- `backup`: a temparory place for code and notebook to be refined and brought back later
- `data`: a place for data files
- `notebook`: polished notebooks
- `script`: command line scripts
- `toolbox`: reusable code to be integrated into the pipeline

## Reproduction Notes

- Everything are assumed to run on ratto.
- The root repo is assumed to be placed as `~/programming/pipeline_utility`.
- I manage my Python environment using Conda. And that's the easiest way to set up the reproduction environment. Use `conda env create -f environment.yml` to create a Conda environment named `pipeline`, and `conda activate pipeline` to activate it.
- Database credentials are needed to access the database. Ask Ed for it.
