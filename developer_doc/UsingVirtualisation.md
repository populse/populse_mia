
**Short**:  
  *Read-only container*:
  - "for Linux, two software must be installed: Python (version >= 2.7) and Singularity (version > 3.6)"
  - mkdir -p $HOME/casa_distro/brainvisa-opensource-master # create an installation directory
  - "[download the last casa-dev image](https://brainvisa.info/download/) (ex. casa-dev-5.0-1.sif), preferably into the $HOME/casa_distro directory"
  - singularity run -B $HOME/casa_distro/brainvisa-opensource-master:/casa/setup $HOME/casa_distro/casa-dev-5.0-1.sif branch=master distro=opensource #Execute the container image using Singularity
  - "set the bin/ directory of the installation directory in the PATH environment variable of the host system, typically add `export PATH="$HOME/casa_distro/brainvisa-opensource-master/bin:$PATH"` in $HOME/.bashrc if unix bash shell
  - "add `cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3` in the [ build $CASA_BUILD ] section of the $HOME/casa_distro/brainvisa-opensource-master/conf/bv_maker.cfg file (host) to make python3 as default"
  - bv_maker #  to build from within container terminal or from outside the container
  - bv # to run the configuration GUI
  - bv bash # to open a terminal in the container

  *To create a container within a writable directory*:
  - sudo singularity build --sandbox $HOME/casa_distro/casa-dev-5.0-1_wr $HOME/casa_distro/casa-dev-5.0-1.sif # To make an editable image (casa-dev-5.0-1_wr)
  - sudo singularity run --writable $HOME/casa_distro/casa-dev-5.0-1_wr bash # To modify the image
  - "It is now possible to modify the image. For example let's update all packages and install emacs:"
  - Singularity> apt update  # Singularity> is the prompt
  - Singularity> apt-get install -y software-properties-common
  - Singularity> add-apt-repository ppa:kelleyk/emacs
  - Singularity> apt install emacs26
  - "Edit the $HOME/casa_distro/brainvisa-opensource-master/conf/casa_distro.json file and change the value of the `image` key (ex. "image": "/home/econdami/casa_distro/casa-dev-5.0-1_wr" in place of "image": "/home/econdami/casa_distro/casa-dev-5.0-1.sif")"
  - "Then using `bv` or `bv bash` will use the casa-dev-5.0-1_wr image" 

**[Longer](https://brainvisa.info/web/download.html)**
