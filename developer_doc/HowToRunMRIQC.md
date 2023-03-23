# 1. Install casa_distro 5.1 (and not lower!) WITHIN A WRITABLE DIRECTORY:
* https://github.com/populse/populse_mia/blob/master/developer_doc/UsingVirtualisation.md

# 2. Install inside the singularity container:
-	TemplateFlow (tested with 0.7.2)
-	StatsModels (tested with 0.12.2)
-	nipype >= 1.7.1
-	dipy >= 1.5.0
-	nipy (tested with 0.5.0)
-	nitime (tested with 0.9)
-	nilearn (tested with 0.9.1) – remark: You might need to manually desinstall joblib (in the casa container) with command 'pip install --ignore-installed' joblib to install nilearn
- reportlab
- statsmodels >= 0.13.5

# 3. Install ANTS

Inside the singularity container:

Last versions of ANTs (that can be compiled on Ubuntu 20.04) require glibc 2.28. When running on casa-distro, MIA uses the glibc library of casa-distro, which is 2.27 version. Moreover, glibc 2.28 or higher cannot be installed on Ubuntu 18.04. That is why ANTS must be installed inside the container.
Install ANTs version 2.2.0 from neuro-debian (https://neuro.debian.net/pkgs/ants.html) using apt-get in the casa-distro image.
!!Warning: there is an error in the tag version of ANTs 2.2.0:
![image](https://user-images.githubusercontent.com/86590799/166933278-45ccbfad-1ed5-45c3-91e8-14c1d32cd5c8.png)

This makes mia_processes.bricks.preprocess.ants.registration fail (when checking minimum version requirement) because it needs some inputs only available from ANTs 2.2.0. To bypass this bug, we need to modify some lines of /casa/home/.local/lib/python3.6/site-packages/nipype/interfaces/ants/base.py :

From:

![image](https://user-images.githubusercontent.com/86590799/166933415-5d415bc2-425b-4850-a65f-a26c762f4c19.png)

To:

![image](https://user-images.githubusercontent.com/86590799/166933450-3bccb30f-3f03-4942-9c80-256958a46bde.png)

This is not a neat solution, but it does the job until we can use casa-distro 5.3 based on Ubuntu 22.04 (as a reminder, the issue with 5.3 is that it’s based on python 3.10 which is not yet supported by dipy, also needed for MRIQC - https://github.com/populse/capsul/issues/207)

Outside the container :
It is also possible to install ANTs outside the container.


# 4. Install AFNI (only tested outside the container)
Following these instructions step-by-step:
https://afni.nimh.nih.gov/pub/dist/doc/htmldoc/background_install/install_instructs/index.html

# 5. Install FSL (only tested outside the container)
Following these instructions step-by-step:
https://fsl.fmrib.ox.ac.uk/fsl/fslwiki/FslInstallation

# 6. Install Freesurfer (only tested outside the container)
For Linux, following the instruction here : https://surfer.nmr.mgh.harvard.edu/fswiki//FS7_linux

Easier to use the tar archive.

Get the Freesurfer License here: https://surfer.nmr.mgh.harvard.edu/registration.html
Copy the license received in the freesurfer folder.

`Fedora 33`: freesurfer-linux-centos8_x86_64-7.3.2.tar.gz (CentOS 8 x86_64 (64b) tar archive) worked fine.


# 7. Your install is ready...
Launch MIA and configure libraries (AFNI, ANTS, Freesurfer and FSL) in preferences.
Run the mia_processes.pipelines.preprocess.anat_mriqc_pipeline or mia_processes.pipelines.preprocess.bold_mriqc_pipeline on your file !
