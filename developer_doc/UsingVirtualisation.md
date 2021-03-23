
**Short**:
  - add "cmake_options += -DPYTHON_EXECUTABLE=/usr/bin/python3" in the [ build ] section of conf/bv_maker.cfg (host) to make python3 as default  
  - sudo singularity build --sandbox /somewhere/casa-dev-5.0-1_wr /somewhere/casa-dev-5.0-1.sif # To make an editable image
  - sudo singularity run --writable /somewhere/casa/casa-dev-5.0-1_wr bash # To modify the image
  - Singularity> apt update  # Singularity> is the prompt
  - Singularity> apt-get install -y software-properties-common
  - Singularity> add-apt-repository ppa:kelleyk/emacs
  - Singularity> apt install emacs26
  - Edit the /somewhere/conf/casa_distro.json file and remove the ".sif" from the image name. ex. "image": "/home/econdami/casa_distro/casa-dev-5.0-1_wr" in place of "image": "/home/econdami/casa_distro/casa-dev-5.0-1.sif"
  - Then using `bv` or `bv bash` will use the casa-dev-5.0-1_wr image in the container



to 

**[Longer](https://brainvisa.info/web/download.html)**
