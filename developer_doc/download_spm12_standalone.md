Linux
=====

Before following the steps, make sure your are on your root directory ( /home ) and outside the container .
This allows to avoid root accesses issues.
Chose the user account folder on your host to make the installations : /home/<your_lacal_user_account>/ . 


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

P.S. Tested on linux with http://www.fil.ion.ucl.ac.uk/spm/download/restricted/bids/spm12_r7487_Linux_R2018b.zip (part 1 above), https://ssd.mathworks.com/supportfiles/downloads/R2018b/deployment_files/R2018b/installers/glnxa64/MCR_R2018b_glnxa64_installer.zip (part 2 above) and without using parts 5 and 6 above: It works! We can now launch Mia. 

8- Setting MIA with smp12 and MATLAB paths.
In **MIA** go to:

File> MIA preferences > Pipelines:

In the **MATLAB section**:
   
   -Check on the box use Matlab standalone.
  
   -Click on browse and add the installation path of your MATLAB Runtime supposed to look like:
       /usr/local/MATLAB/MATLAB_Runtime/v95.


In the **SMP section** :
  
   -Check on the box use SPM standalone.
  
   -Click on browse and add the path of the unzip file of spm12 supposed to look like:
       /home/<your_lacal_user_account>/smp12.

Then validate your changes by clicking on **OK button** 

You can now use MATLAB and SPM with MIA!

MacOS
=====

1- Download the spm12_r7771.zip file: https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/
Unzip it. In the same directory where run_spm12.sh can be found unzip spm12_maci64.zip

2- Download the corresponding MCR for MATLAB Compiler Runtime (MCR) v4.13 (MATLAB R2010a) MCRInstaller.dmg file: https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/MCR/maci64/

3- Start the MATLAB Runtime installer: double click in MCRInstaller.dmg then right click on MCRInstaller.pkg, then choose Open with > Installer (default). The MATLAB Runtime installer starts, it displays a dialog box. Read the information and then click Next (or continue) to proceed with the installation. Then click Install. The default MATLAB Runtime installation directory is now in /Applications/MATLAB/MATLAB_Compiler_Runtime/v713.

4- Usage: Go where run_spm12.sh file can be found, then just type ./run_spm12.sh /Applications/MATLAB/MATLAB_Compiler_Runtime/v713/
If No Java runtime is already installed, a pop-up is opened with a `No Java runtime present, requesting install` message.

5- Download Java for OS X 2017-001: https://support.apple.com/kb/DL1572?locale=en_US
Click on Download then Open with > DiskImageMounter (default) > Ok.
Right click on the JavaForOSX.pkg then choose Open with Installer (default).
The Java for OS X 2017-001installer starts, it displays a dialog box. Answer the questions  then install.

6- `./run_spm12.sh /Applications/MATLAB/MATLAB_Compiler_Runtime/v713/ fmri` works fine now !!!

P.S. Tested on macOS 10.13.6. The run_spm12.sh fle for this version is not compatible with mia. While `./run_spm12.sh /Applications/MATLAB/MATLAB_Compiler_Runtime/v713/ fmri` works fine in a terminal, using this version of spm standalone results in an error with this message: `/Volumes/Users/econdami/Documents/spm/spm12Standalone/spm12Stndalone_r7771/run_spm12. sh: line 60: ./spm12.app/Contents/MacOS/spm12_maci64: No such file or directory`. We need a run_spm12.sh like as in spm12_r7532_BI_macOS_R2018b.zip (https://www.fil.ion.ucl.ac.uk/spm/download/restricted/utopia/dev/) with MCR_R2018b_maci64_installer.dmg.zip (https://fr.mathworks.com/products/compiler/matlab-runtime.html). With the last two, mia works fine !

