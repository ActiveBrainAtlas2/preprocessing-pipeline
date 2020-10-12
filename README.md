# Utilities for the Active Atlas Pipeline
## Creating a sandbox on your computer
1. git clone this reposititory `git clone git@github.com:eddyod/pipeline_utility.git`
1. create a virtual environment in your home dir: python3 -m venv ~/.virtualenvs/pipeline
1. cd pipeline_utility
1. source ~/.virtualenvs/pipeline3/bin/activate
1. pip install -r requirements.txt
1. We are currently using Ubuntu 18.04 as of October 2020. Either install this on your local machine or install it
as a VM with Virtualbox or VMware. Note, using Ubuntu 20.04 also works, and since our servers will eventually 
get upgraded to that, you may as well install 20.04 
1. Create this directory to start with: `sudo mkdir -p /net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK52/preps/CH1` 
1. Make yourself user: `sudo chown -R myloginname: /net`
1. Set up ssh keys on ratto with ssh-copy-id
1. Get some thumbnails to start with 
`rsync -auv ratto.dk.ucsd.edu:/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK52/preps/CH1/thumbnails/ 
/net/birdstore/Active_Atlas_Data/data_root/pipeline_data/DK52/preps/CH1/thumbnails/`
1. You can now experiment with some of the thumbnails for DK52
### Setup the database portal on your local machine
1. Get repo: `git clone git@github.com:eddyod/ActiveBrainAtlasAdmin.git`
1. create a virtual environment in your home dir: python3 -m venv ~/.virtualenvs/activebrainatlas
1. cd activebrainatlas
1. source ~/.virtualenvs/activebrainatlas/bin/activate
1. pip install -r requirements.txt
### Mysql for the database portal on Ubuntu
1. For complete instructions, look at this page: https://www.digitalocean.com/community/tutorials/how-to-install-mariadb-on-ubuntu-20-04
1. Or, just:
    1. sudo apt update
    1. sudo apt install mariadb-server
    1. sudo mysql_secure_installation
    1. go into the new mysql installation: sudo mysql
    1. at the mysql prompt create a new user: `GRANT ALL ON active_atlas_development.* TO 'dklab'@'localhost' IDENTIFIED BY 'newpasshere';`
    1. create a new database `create database active_atlas_development`
    1. populate the database with a backup from ratto:
    1. ssh into ratto.dk.ucsd.edu
    1. look for our database backups: `ls -lhtr /net/birdstore/Active_Atlas_Data/data_root/database/backups/`
    1. Get the gzipped file that appears as the last one in the ls command from above
    1. You can get it from your local machine: 
    `rsync -auv ratto.dk.ucsd.edu:/net/birdstore/Active_Atlas_Data/data_root/database/backups/active_atlas_production.2020-10-XXXXXX.sql.gz ./`
    1. Create file: ~/.my.cnf in your home directory on your local machine:
    `[client]
    user						= dklab
    password					= newpasshere
    port						= 3306
    host						= localhost`
    1. From your local machine do: 
        1. `gunzip active_atlas_production.2020-10-XXXXXX.sql.gz`
        1. `mysql active_atlas_development < active_atlas_production.2020-10-XXXXXX.sql`
    1. Test by going into the database and running some commands:
        1. `mysql active_atlas_development`
        2. `show tables`
### Tools we use
1. Here is a list of the software we use on a daily basis
1. Jetbrains pycharm - IDE for python, the professional version is available to UCSD, check blink.ucsd.edu
1. Jetbrains datagrip - database GUI tool, use same license as above
1. Jetbrains webstorm - useful for javascript, typescript. Feel free to use atom, Code or eclipse
1. imagemagick - used for converting images.
1. matlab - we are just starting to use this. UCSD license is also available
1. jupyter notebooks
1. Fiji, port of ImageJ
1. 3D Slicer 
1. Gimp - image editing software
1. Geeqie - image viewer

### For Neuroglancer scripts,
1. git clone https://github.com/HumanBrainProject/neuroglancer-scripts.git
2. python3 -m venv ~/.virtualenvs/neuroglancer
3. source ~/.virtualenvs/neuroglancer/bin/activate
4. cd neuroglancer-scripts
5. python setup.py install
6. Look in ~/.virtualenvs/neuroglancer/bin/ for the precomputed scripts
### Directory structure of the pipeline
1. The base directory is located on birdstore at: /net/birdstore/Active_Atlas_Data/data_root/pipeline_data
2. All brains are located in the base directory.
3. To view the post tif pipeline process go here: [Neuroglancer process](PROCESS.md)
4. The directory structure of a 3 channel brain will look like this:
![MD589](./docs/images/MD589.tree.png)
### Annotations
1. Annotation keys are viewable: [here](https://activebrainatlas.ucsd.edu/annotation-keys.html)
### Database backups
1. The development and production databases are backed up multiple times each day on basalis
1. If you need a backup, look on basalis at: /net/birdstore/Active_Atlas_Data/data_root/database/backups/
1. The development database is named active_atlas_development
1. The production database is named active_atlas_production
