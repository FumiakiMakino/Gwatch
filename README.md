# Gwatch
Gwatch: a pipeline program for quick evaluation of sample quality in CryoEM 

## Overview
This software is a python program developed for electron cryomicroscope (cryoEM) users collecting data for single-particle image analysis. 


The function is very simple,

-  It watches a directory and performs MotionCor 2 and Gctf immediately after image data transfer (or for existing stack files).
-  When any number of images you preset is reached, Gautomatch, Particle extraction (By Relion2), and 2D-classification (By Relion2) are performed.

This is an On-the-fly Pipeline program that runs at once.

The aim of this software development is to offer a quickest way to determine whether the three-dimensional (3D) reconstruction will go smoothly and whether the image analysis will lead to high resolution.

While there may be a voice of "HUH? I want to use other motion correction program." "Isn't ctffind4 better?", the purpose of this program is just to speed up the preprocessing by MotionCor 2 and make two-dimensional (2D) class averages as quickly as possible. This is the main concept of this software. Please use your favorite programs for actual image analysis later using your GPGPU.

It is also assumed that the user is able to judge whether the 3D reconstruction would be successful from the 2D class average images. I commented on how many images we should have for the "Number required for judgment", but please wait for a while for more detailed information until I finish writing up a paper.

## Preparations

Prepare a GPGPU system connected via optical fiber or Gigabit Ethernet to the microscope PC that controls Gatan K2 or other direct electron detector cameras. This software works if Linux (ubuntu or CentOS) runs on the PC. It is desirable to have more than two GPUs. In case of Gatan K2, one of the four optical fiber ports is available for connection. I recommend to use it effectively.

## About the Hard Disk Drive (HDD) connected to GPGPU

In our case, we connect HDD directly to GPGPU (At a hard drive stand) and configure it to access both the microscope PC and GPGPU via a samba server. In addition, the captured CryoEM images are set to be copied directly to this HDD.

## What is required for installation

The following single particle image analysis programs (Be sure to work with GPU)
```
MotionCor2, Gctf, Gautomatch, eman2, IMOD, Relion2
```

- My program wraps these programs.
- Be sure to use them in accordance with their terms of use and license.
#### IMPORTANT!!
- For MotionCor2, Gautomatch, and Gctf, pass the path or alias from the shell to "MotionCor2", "Gautomatch", "Gctf".


## Required python libraries (Only Ubuntu and CentOS confirmed):
```
python3, watchdog, pyqt5, numpy
```


### About Installing in Ubuntu (16.04 confirmed via pip)
1. Installing Python3 and Pip
```
$ sudo apt-get install python3-dev python3-pip
```

Upgrade Pip
```
$ sudo python3 -m pip install —upgrade pip
```

Installing numpy
```
$ sudo python3 -m pip install numpy
```

Installing watchdog
```
 $ sudo python3 -m pip install watchdog
```

Installing Pyqt5
```
$ sudo  python3 -m pip install pyqt5
```

### Installing in the CentOS (Confirmed 7 via pip, 6 See comments below)
1.Install python 3.6
```
$ sudo yum install -y https://centos7.iuscommunity.org/ius-release.rpm
$ sudo yum search python36
$ sudo yum install python36u python36u-libs python36u-devel python36u-pip
```


Install Pyqt5
```
$python3.6 -m pip install pyqt5
```

Install watchdog
```
$python3.6 -m pip install watchdog
```

Install Numpy
```
$python3.6 -m pip install numpy
```

#### Installing in CentOS 6 (Comments from Mr. Y)

I received the following comment. 
```
In the CentOS 6 environment, Gwatch did not work because pyqt5 is dependent on the new version of glibc (glibc 2.17 or higher)
```
Pyqt5 will work by updating glibc at the following site: https://gist.github.com/harv/f86690fcad94f655906ee9e37c85b174



## Installation 
1. Download Gwatch (git clone git://github.com/FumiakiMakino/Gwatch.git)
2. Pass the path to the extracted folder
- IMPORTANT!! For MotionCor2, Gautomatch, and Gctf, pass the path or alias from the shell to "MotionCor2", "Gautomatch", "Gctf".

## About Gwatch Usage and Features

Launch the console and enter ```Gwatch_v32.py``` 

## About Automatic MotionCor2
1. For "Watching Directory", select the directory where data is copied
2. For "Watching File Name", enter the name of the file. You should use wildcards to specify a name and format,  (Example: *.mrc, *.mrcs, *.tif, *.tiff) I do not recommend to use it except ".mrc",".mrcs",".tif" and ".tiff"
3. For "Number of Frame", specify the number of sheets. Only valid for data saved as a single image. When the specified number is reached, create stack data with newstack and start MotionCor2. (I do not recommend to save them in single images because it is slow due to stack making procedure!)
4. "Do Gain-reference?": If you want to use Gain-reference in MotionCor2, select YES and select a file from the "Name of Gain-Reference". The data for the extension dm4 is also automatically converted. After conversion, it is saved as "gain.mrc" in the monitoring folder.
5. "Do Measure Ice?": If YES, the percentage of electron transmission with/without the energy filter is recorded in the _rlnEneryLoss row of micrograph_all_ gwatch.star.  In that case, choose a file from the "Name of Image without energy filter" file that you recorded the image without filtering. Here, the ratio is determined from the intensity recorded in the header.
6. "Additional Option For MotionCor2": This allows you to enter options for MotionCor2. Input all necessary items other than input and output or gain reference.
7. "Which GPUs": Specify the GPU used here. Only one specification if not specified. In addition, when MotionCorr2 is used, one GPU is allocated per one process. The maximum is four processes on four GPUs. Why? Because it is faster!
8. For "Pixel Size", "Cs", "Acceleration Voltage", enter the numbers required for calculating Gctf. If you change these, it works with the MotionCor 2 option above.

### About Automatic 2D-classification

1. For "Calculate 2D classification?", when YES is selected, 2D class average is performed with Relion2 when the preset number of images is reached in the folder. The parameters required for calculation can be typed in here. So you must enter them. The results are popped up using the Relion display and stored in Class2D/job000_01, Extract/job000_01.
2. "Calculate 2D classification every batch?": When YES is selected, the calculation for the 2D class average is repeatedly carried out when the preset number of images is reached in the folder. The results are popped up using the Relion display and stored in Class 2D / job000_01, 02... Extract/job000_01, 02....
3. "How hard Micrographs use to calculate?": The number of copies of the 2D class average image. About 10 -50 sheets are desirable.
4. "Particle Diameter": This is the value required to pick up particles by Gautomatch. If this is set smaller than the particle diameter, it will pick up many, but there will be a lot of garbage. It seems to be good to match the size of the long axis for particles with an elliptical shape.
5. "Binning": This is applied when the particle images are extracted, and the 2D class average is calculated. Although it depends on the pixel size, it is preferable to set the number to 2 for the data collected in the counting mode and to 4 for those collected in the super resolution mode.
6. "Run" and "Cancel": Press "Run" button to start Gwatch.
Gwatch can run offline. Therefore it is possible to calculate it after several dozen images are collected. If the calculation failed, set it up again and press “Run ”. You need to select the watching directory again. "Cancel" button stops calculation. If MotionCor2 is running, the calculation will be continued.

The result will be available for Relion as micrographs_all_gwatch.star. This format is almost the same as that in Gctf.

### About Tabs Results
The results of MotionCor2 and Gctf are read from micrograph_all_gwatch.star and display in [Results of MotionCor 2 and Gctf] in the order of `"Defocus_U Defus_V Angle FoM RationOfIcethinkness"`

 The command lines at the 2D-classification runtime are displayed in [Commands For Auomatic 2D-classificaiton] and are recorded in gwatch_cmd01.log
 
Other statuses of the process are displayed in [status] 
The error in each program is displayed in red.

### Save and open in the setting file

The settings for MotionCor2, Gctf, and Relon2 are recorded when save setting is selected. 
(The default is ~ / .Gwatch_setting in default.) You can open the setting file from open setting.

## Current Problems and Solutions

- Do Not Launch → Verify library installation. If not, remove the initial setting file with "rm-rf ~ / .Gwatch _ setting" 
- Crash occasionally → Restart Gwatch, start from continuation
- MotionCor 2 does not work→ it is possible that the data transfer failed. Start with ```Gwatch_v32.py -t <# time>```.

<# time> should be set in seconds, such as 10 or 15. Although the default interval time is 5 seconds by default, since Gwatch monitors the increment of the file size, it would be safer to set a longer waiting time for completion of the data copy .

## Future implementation features

Display and display results via the net. Changing the GUI and the System (June 2018)
Automatic judgment of data quality using machine learning or deep learning (TBD)


## Number of cryoEM images required for judgment of data quality

About 10 to 50 images that would allow 3,000-5,000 particle images to be picked up would be sufficient to make a judgement on the data quality (Writing papers). If there are 2D class average images showing the secondary structures of proteins, the images are good and the image analysis will probably go well. Then, just continue collecting data with confidence until your cryoEM machine time runs out! Otherwise, keep trying to make better samples with the spirit of “Never Give Up”.

## Question
If you have a question and request, send e-mail `h1839<at>fbs.osaka-u.ac.jp`




