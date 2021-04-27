JanWP commented on Sep 10, 2019

For information, here are my notes on how to install MIA in a virtual environment from the sources, with populse_db, capsul and mia_processes installed from sources as well.
The different steps are noted such that they are independent - obviously the "workon" command is only necessary once in a terminal session if several of the steps are performed.
All the code will reside in a directory called "populse_mia_dir", and the virtual environment in this example is populse_mia_env.
Both can be adapted at will (and possibly have the same name if desired).

***Prepare virtual environment and working directory***

mkvirtualenv --no-site-packages --python=/usr/bin/python3 populse_mia_env
mkdir ~/my_code_directory/populse_mia_dir

***Install populse_db***

cd ~/my_code_directory/populse_mia_dir
git clone git@github.com:populse/populse_db.git
cd populse_db
workon populse_mia_env
python3 setup.py install --prefix ~/.virtualenvs/populse_mia_env

***Install capsul***

cd ~/my_code_directory/populse_mia_dir
git clone git@github.com:populse/capsul.git capsul
cd capsul
workon populse_mia_env
python3 setup.py install --prefix ~/.virtualenvs/populse_mia_env

***Install mia_processes***

cd ~/my_code_directory/populse_mia_dir
git clone git@github.com:populse/mia_processes.git mia_processes
cd mia_processes
workon populse_mia_env
python3 setup.py install --prefix ~/.virtualenvs/populse_mia_env

***Install populse_mia***

cd ~/my_code_directory/populse_mia_dir
git clone git@github.com:populse/populse_mia.git populse_mia
cd populse_mia
workon populse_mia_env
python3 setup.py install --prefix ~/.virtualenvs/populse_mia_env

***Run populse_mia***

cd ~/my_code_directory/populse_mia_dir/populse_mia
workon populse_mia_env
python3 python/populse_mia/main.py
