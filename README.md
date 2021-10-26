### Table of contents for the pipeline process
1. [Active Brain Atlas home page](https://github.com/ActiveBrainAtlas2)
1. [Installing the pipeline software](docs/SETUP.md)
1. [A description of the pipeline process with detailed instructions](docs/PROCESS.md)
1. [HOWTO run the entire pipeline process with step by step instructions](docs/RUNNING.md)
1. [The entire MySQL database schema for the pipeline and the Django portal](schema.sql)
1. [Software design and organization](docs/Design.md)

## A high level description of the Active Brain Atlas pipeline process

The ability to view and share high resolution microsopy data among anatomists in
different labs around the world has given rise for the need for a set of tools
to perform this task. Going from tissue slides to data that can be viewed, edited
and shared is an involved process. The popular phrase "big data" comes into play
here quite visibly. Intermediary data can run around 5TB per mouse. The finished
web data will take another 5TB. This finished data also needs to be stored in
an efficient and secure format that is accessible by web servers. The following
steps are used to process this data, from slide scanning all the way to web
accessible data.

### Raw data processing

### Masking and cleaning

### Section to section alignment

### Preparation of aligned data for use in Neuroglancer