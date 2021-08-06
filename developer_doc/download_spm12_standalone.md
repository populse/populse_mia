Linux
=====

1- Download the desired version of spm: https://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/
Unzip it

2- Download the corresponding MCR for linux: https://uk.mathworks.com/products/compiler/matlab-runtime.html
Unzip it in a MCR/ folder 

3- Install it following these steps:
https://fr.mathworks.com/help/compiler/install-the-matlab-runtime.html

4- After the installation, you get the following message (ex. for R2018b (9.5) MCR):
On the target computer, append the following to your LD_LIBRARY_PATH environment variable: 
/usr/local/MATLAB/MATLAB_Runtime/v95/runtime/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v95/bin/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v95/sys/os/glnxa64:/usr/local/MATLAB/MATLAB_Runtime/v95/extern/bin/glnxa64
If MATLAB Runtime is to be used with MATLAB Production Server, you do not need to modify the above environment variable.

5- Create a .conf file in the /etc/ld.so.conf.d/ folder and add those previous paths in the file:
/etc/ld.so.conf.d/your_lib.conf

6- Run ldconfig to update the cache:
sudo ldconfig

7- Go back to spm12 folder
Execute SPM12, the second path being the path of the MCR (that has been chosen during the installation):
./run_spm12.sh /usr/local/MATLAB/MATLAB_Runtime/v93

P.S. Tested on linux with http://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/spm12_r7487_Linux_R2018b.zip (part 1 above), https://ssd.mathworks.com/supportfiles/downloads/R2018b/deployment_files/R2018b/installers/glnxa64/MCR_R2018b_glnxa64_installer.zip (part 2 above) and without using parts 5 and 6 above: It works!
