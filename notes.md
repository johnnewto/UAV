
#### Gstreamer fail to load deepstream plugins in TX2NX
https://forums.balena.io/t/gstreamer-fail-to-load-deepstream-plugins-in-tx2nx/368378

#### Building on jetson orin nx deepstream 6.4 ubuntu 22 #95
https://github.com/basler/gst-plugin-pylon/issues/95

####  Unable to build 7.4.0 with NVMM support on Linux / Jetson Orin #82 
https://github.com/basler/gst-plugin-pylon/issues/82

#### Remove gstreamer cach to rescan plugins
```bash
rm -rf ~/.cache/gstreamer-1.0
```

#### Problems with avdec_h264 running on the jetson orin
- see [Unable find avdec_h264 after intsalled gstreamer plug-ins into Jetson AGX Orin](https://forums.developer.nvidia.com/t/unable-find-avdec-h264-after-intsalled-gstreamer-plug-ins-into-jetson-agx-orin/226575/5    )

 Run this first  
```bash
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1
```
Alternativily place in .bashrc
```bash
echo 'export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1' >> ~/.bashrc
```
