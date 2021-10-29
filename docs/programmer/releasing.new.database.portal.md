### Using rsync to upload new code to the web server
1. On your local development machine, copy this data into a file called excludefiles.txt one directory above your code base:
<pre>
data
settings.py
*.pyc
.git*
.idea*
parameters.yaml
*__pycache__*
*~
*migrations*
notebooks/.ipynb_checkpoints*
</pre>
1. Login into activebrainatlas.ucsd.edu and backup the current code base that works. Copy the directory to your home folder or another tmp directory: `rsync -auv /var/www/activebrainatlas/ ~/tmp/activebrainatlas/`
1. On your local machine in the same directory with the excludefiles.txt file, do an rsync `rsync -auvn --exclude-from=exclude.files.txt ./activebrainatlas/ activebrainatlas:/var/www/activebrainatlas/` That will test which files you are sending to the server. When you are happy with what is being sent, remove the n from the options in the command above so it looks like `rsync -auv --exclude-from=exclude.files.txt ./activebrainatlas/ activebrainatlas:/var/www/activebrainatlas/`
1. The code is now on the web server.
1. Login back to activebrainatlas.ucsd.edu and check the code:
    1. `cd /var/www/activebrainatlas`
    1. `source /var/www/venvs/activebrainatlas/bin/activate`
    1. `python manage check`
    1. `python manage runserver`
1. Those last two commands should report no errors.
1. You need to reload apache with:
    1. `sudo apachectl configtest`
    1. `sudo apachectl graceful`
1. The server has been reloaded, now go to https://activebrainatlas.ucsd.edu/activebrainatlas/admin and click relevant links to make sure the server is running correctly.