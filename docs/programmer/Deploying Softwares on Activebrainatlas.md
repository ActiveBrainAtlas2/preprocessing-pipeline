## Deploying Softwares on Activebrainatlas

this document covers the procedure for deploying softwares on the activebrainatlas.ucsd.edu server.  activebrainatlas.ucsd.edu is a virtual machine running on a computer at the Physics department at UCSD, currently configured as an apache server

### Accessing the server via ssh

Ask Kelvin to obtain ssh access to activebrainatlas.ucsd.edu

### Deploying Django

1. ssh into activebrainatlas
2. move the /var/www/activebrainatlas folder to a backup location
3. create a new /var/www/activebrainatlas folder and use git to clone and checkout the desired version of code
4. copy the settings.py files from muralis,basalis or ratto.  Make sure the settings files point to the production database
5. edit the activebrainatlas/neuroglancer/admin.py file to change the API endpoint used for the neuroglancer state admin page.
6. run **Deploying abakit** section to install abakit
7. try python manage.py runserver at /var/www/activebrainatlas folder see if django runs propperly
8. run sudo systemctl restart httpd and check the https://activebrainatlas.ucsd.edu/activebrainatlas portal
9. if Error occurs, check the /etc/httpd/logs/error_log
   - You might need to change permission of django folder and subfolders

###  Deploying Neuroglancer

1. login to a computer with node setup, if non exists, checkout the setup guide on the neuroglancer github
2. clone and checkout the version of neuroglancer you want in your folder
3. compile the neuroglancer version you have with npm run <build script>
4. copy all the files in neuroglancer/dist/dev to activebrainatlas:/var/www/activebrainatlas/html/ng with scp
5. ssh into activebrainatlas
6. run sudo systemctl restart httpd and check the https://activebrainatlas.ucsd.edu/ng portal



### Deploying Abakit

1. ssh into activebrainatlas
2. clone/checkout the version of abakit you want
3. run `pip install . --extra-index-url --trusted-host`
4. you might need to change file permissions



### Updating Abakit,Django or Neuroglancer

1. under the corresponding folder, run `git pull origin <branch>` and confirm merge results
2. run sudo systemctl restart httpd and check the appropriate portal

### Usability checklist

Here is a list of things to check after deploying any of these softwares

1. login to https://activebrainatlas.ucsd.edu/activebrainatlas/admin
2. Check https://activebrainatlas.ucsd.edu/activebrainatlas/admin/neuroglancer/urlmodel/ and click on a url
3. Check each link in the neuroglancer and brain app and confirm they are working
4. access https://activebrainatlas.ucsd.edu/ng and check if you can save/load url and annotations.  
5. Save some test annotations and see if you can find them in the database or database portal.

### Transferring data from active_atlas_development to active_atlas_production

active_atlas_development and active_atlas_production are two mariadb databases hosted on db.dk.ucsd.edu

To copy everything from development to production:

1. login a computer that has database credentials setup
2. make a copy of production `mysqldump active_atlas_production > production.bck`
3. make a copy of development `mysqldump active_atlas_development> development.bck`
4. populate the active_brain_production server with data from production `mysql active_atlas_production < development.bck`

