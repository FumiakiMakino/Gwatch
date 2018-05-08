#!/usr/bin/env /usr/bin/python3


#********************************************
# Author: Fumiaki Makino (h1839@fbs.osaka-u.ac.jp)
#         Frontier BioScience, Osaka University
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#----------------------------------------------
#       Gwatch.py (v3.2.3)
#               written by Fumiaki Makino
#               since 2017.03.05
# 
# This program run automatically MotionCor2 and 2D-Classification in a folder watching by watchdog
# Usage : Gwatch_v32.py
#
#********************************************


import sys
import datetime
import time
import os
import re
import os.path
from stat import *
import fnmatch
import subprocess
import glob
import fcntl
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from watchdog.events import FileSystemEventHandler
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from gui.Gwatch_Gui_v321 import *
import numpy as np
import struct as st

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

#Initial value
hpath=os.environ['HOME']
path=os.getcwd()
refnameg=" "
refnameice=" "
iniische=1
ische=iniische
list4cal=[]
list4gpu=[]
proclist=[]
fnamelist=[]
flg_single=0
mot2_flg=0
flag_con=0  # Flag for calculate 2D classification every batch
num_bat=0   # Number of batch
opath=os.path.abspath(__file__)
flag_refice=0 # Flag for ice ratio
mean_ref=1.0  # mean value of reference of ice thickness
num4cls = 1 # Global value to count number of images
ti=5
#read initial parameter from file
try:
    with open("%s/.Gwatch_setting"%hpath,"r") as iniparaFile: 
        #Automatic MotionCor2
        inifname=iniparaFile.readline() #File name
        fname=inifname
        inifnum=iniparaFile.readline()  #stack number 
        fnum=inifnum
        iniadopi=iniparaFile.readline() #option for motionCor2
        adopi=iniadopi
        #Automatic 2D classificaiton
        iniMicro=iniparaFile.readline() #number of file for automatic 2D classification
        iniPix=iniparaFile.readline()   #Pixel size
        iniCs=iniparaFile.readline()    #Cs
        iniKv=iniparaFile.readline()    #kV
        iniDia=iniparaFile.readline()   #diameter of particle
        refnameg=iniparaFile.readline() #Gain referencefile
        inibin=iniparaFile.readline()   #bin
        refnameice=iniparaFile.readline() #Referencefile image for ice thickness
        iniadopigctf=iniparaFile.readline() #option for gctf
        iniadopi2dcls=iniparaFile.readline() #option for 2d classification
except:
    inifname= "*.tiff"#File name
    fname=inifname
    inifnum="32"  #stack number 
    fnum=inifnum
    iniadopi="-Patch 5 5 -FmDose 3.0 -Kv 300 -PixSize 1.00 -Cs 2.7 -FmRef 1 -FlipGain 1 -RotGain 1" #option for motionCor2
    adopi=iniadopi
    #Automatic 2D classificaiton
    iniMicro="50" #number of file for automatic 2D classification
    iniPix="1.0"  #Pixel size
    iniCs="2.7"    #Cs
    iniKv="300"    #kV
    iniDia="100"   #diameter of particle
    refnameg=" "    #Gain referencefile
    inibin="2"      #binning
    inirefnameice=" "
    iniadopigctf= "--ac 0.1" #option for gctf
    iniadopi2dcls="--dont_combine_weights_via_disc --no_parallel_disc_io --pool 3 --iter 25 --tau2_fudge 2 --K 32 --flatten_solvent  --zero_mask --ctf --oversampling 1 --psi_step 12 --offset_range 5 --offset_step 2 --norm --scale --dont_check_norm --j 1 --gpu" #option for 2d classification
    
    with open("%s/.Gwatch_setting"%hpath,"w") as iniparaFile:
        iniparaFile.write(inifname.replace('\n','')+"\n") #File name
        iniparaFile.write(inifnum.replace('\n','')+"\n")  #stack number 
        iniparaFile.write(iniadopi.replace('\n','')+"\n") #option for motionCor2
        iniparaFile.write(iniMicro.replace('\n','')+"\n")  #number of file for automatic 2D classification
        iniparaFile.write(iniPix.replace('\n','')+"\n")  #Pixel size
        iniparaFile.write(iniCs.replace('\n','')+"\n")    #Cs
        iniparaFile.write(iniKv.replace('\n','')+"\n")    #kV
        iniparaFile.write(iniDia.replace('\n','')+"\n")  #diameter of particle
        iniparaFile.write(refnameg.replace('\n','')+"\n")     #Gain referencefile
        iniparaFile.write(inibin.replace('\n','')+"\n")  #binning
        iniparaFile.write(inirefnameice.replace('\n','')+"\n")  #Referencefile for ice thickness
        iniparaFile.write(iniadopigctf.replace('\n','')+"\n")  #option for gctf
        iniparaFile.write(iniadopi2dcls.replace('\n','')+"\n") #option for 2D classification
     
     
       
def delspa(filename):
    nf=""
    for i in filename:
        if(i==" "):
            nf+="\ "
        else:
            nf+=i
    return nf

def getext(filename):
    return os.path.splitext(filename)[-1].lower()

def getname(filename):
    return os.path.split(filename)[-1]

def getwholename(filename):
    return os.path.splitext(filename)[0]

def list2ReGPU(list): #making printable list of GPU for 2D classification
    plist=""
    for i in list:
        plist = plist+str(i)+" "
    return plist

def cal_2dcls(diameter, apix, kv, cs, binn, num, cmd2dcls):		
    global path	
    global list4gpu
    global num_bat
          
    #Read write micrographs
    with open(path+"/micrographs_all_gwatch.star","r") as fb:
        allines=fb.readlines()

    if(len(allines) < num*num_bat+16):
        print("Error! loading %s/micrographs_all_gwatch.star"%path)
        print("Cannot calculate 2D classification!")
        myapp.report_result_status("Error! cannot loading %s/micrographs_all_gwatch.star"%path,1)
        myapp.report_result_status("Check number of micrographs which have been done MotionCor2 and micrographs_all_gwatch.star"%path,1)
        myapp.report_result_status("Cannot calculate 2D classification!",1)
        return 

    with open(path+"/micrographs_all_gwatch%02d.star"%num_bat,"w") as fb:
        fb.write("\n")
        fb.write("data_ \n")
        fb.write("\n")
        fb.write("loop_ \n")
        fb.write("_rlnMicrographName #1\n")
        fb.write("_rlnCtfImage #2\n")
        fb.write("_rlnDefocusU #3\n")
        fb.write("_rlnDefocusV #4\n")
        fb.write("_rlnDefocusAngle #5\n")
        fb.write("_rlnVoltage #6\n")
        fb.write("_rlnSphericalAberration #7\n")
        fb.write("_rlnAmplitudeContrast #8\n")
        fb.write("_rlnMagnification #9\n")
        fb.write("_rlnDetectorPixelSize #10\n")
        fb.write("_rlnCtfFigureOfMerit #11\n")
        fb.write("_rlnFinalResolution #12\n")
        fb.write("_rlnEnergyLoss #13\n")
        for ij in allines[17+num*(num_bat-1):17+num*num_bat]:
           fb.write(ij)
         
    bin=binn

    box_size=int(diameter/apix*1.5/8)*8  #box size is 1.5 times and apply  multiples of eight for binning
    
    #Gautomatch
    cmd2nd="`which Gautomatch` --apixM %f --diameter %d *_SumCor.mrc --gid 0"%(apix,diameter) 

    #Particle extract, particles are  binning here
    cmd3rd0="mkdir -p Extract/job000_%02d/"%(num_bat) 
    cmd3rd="`which relion_preprocess` --i micrographs_all_gwatch%02d.star --coord_dir ./ --coord_suffix _automatch.star --part_star Extract/job000_%02d/particles.star --part_dir Extract/job000_%02d/ --extract --extract_size %d --scale %d --norm --bg_radius %d --white_dust -1 --black_dust -1 --invert_contrast 1> Extract/job000_%02d/run.out 2> Extract/job000_%02d/run.err"%(num_bat,num_bat,num_bat,box_size,box_size/bin,int(box_size/bin*0.75/2),num_bat)

    #2D classification
    cmd4th0="mkdir -p Class2D/job000_%02d/"%(num_bat)
    cmd4th="mpirun -np %d `which relion_refine_mpi` --o Class2D/job000_%02d/run --i Extract/job000_%02d/particles.star --particle_diameter %d  %s 1> Class2D/job000_%02d/run.out 2> Class2D/job000_%02d/run.err"%(len(list4gpu)+1,num_bat,num_bat,(int(diameter*1.4)),cmd2dcls,num_bat) 

    #See picking up paritcle in Relion2
    cmd5th0="mkdir -p ManualPick/job000_%02d/"%(num_bat) 
    cmd5th1="cp *automatch.star ManualPick/job000_%02d/"%(num_bat)
    cmd5th="`which relion_manualpick` --i micrographs_all_gwatch%02d.star --selection selected_micrographs_ctf%02d.star --odir ManualPick/job000_%02d/ --pickname automatch --scale 0.2 --sigma_contrast 3 --black 0 --white 0 --lowpass 0 --angpix %f --ctf_scale 1 --particle_diameter %i"%(num_bat,num_bat,num_bat,apix,diameter)

    #See class2D result
    cmd6th="`which relion_display` --i Class2D/job000_%02d/run_it025_model.star --gui"%(num_bat)

    time.sleep(1)
    os.chdir(path) #"cd <path>

    with open("%s/gwatch_cmd%02d.log"%(path,num_bat),"w") as flog:
        flog.write(cmd2nd+"\n")
        flog.write(cmd3rd+"\n")
        flog.write(cmd4th+"\n")
        flog.write(cmd5th+"\n")
        flog.write(cmd6th+"\n")

    print("Running 2D classification procedure....")
    myapp.report_result_status("==> Start 2D classification using %05d - %05d micrographs"%(num*(num_bat-1)+1,num*num_bat),0)
    myapp.report_result_cmd("==> writing logfile in gwatch_cmd%02d.log"%(num_bat))

    try:
        myapp.report_result_status("Start particle pick up by Gautomatch...",0)
        print("Start particle pick up by Gautomatch...")
        subprocess.check_call(cmd2nd,shell=True)
        myapp.report_result_cmd(cmd2nd) 
        myapp.report_result_cmd(" ")
        myapp.report_result_status("Done: particle picking up by Gautomatch",0) 
    except:
        myapp.report_result_status("Error in Gautomatch",1) 
        #QMessageBox.critical(myapp,"Error","Error in Gautomatch")
        return
    
    try:
        myapp.report_result_status("Start particle extraction by relion2...",0)
        print("Start particle extraction by relion2...")
        subprocess.check_call(cmd3rd0,shell=True)
        subprocess.check_call(cmd3rd,shell=True)
        myapp.report_result_cmd(cmd3rd)
        myapp.report_result_cmd(" ") 
        myapp.report_result_status("Done: particle extraction by relion2",0) 

    except:
        myapp.report_result_status("Error in particle extract by Relion2",1) 
        myapp.report_result_status("Continue automatic MotionCor2...",0)
        #QMessageBox.critical(myapp,"Error","Error in particle extract by Relion2")
        return
            
    try:
        myapp.report_result_status("Start 2D-classification by relion2...",0)
        print("Start 2D-classification by relion2...")
        subprocess.check_call(cmd4th0,shell=True) 
        subprocess.check_call(cmd4th,shell=True) 
        myapp.report_result_cmd(cmd4th)
        myapp.report_result_cmd(" ") 
        myapp.report_result_status("Done: 2D-classification by relion2",0) 

    except:
        myapp.report_result_status("Error in 2D-classification by Relion2",1)
        myapp.report_result_status("Continue automatic MotionCor2...",0)
        return

    #Disply Result *temporary
    time.sleep(3)
    subprocess.call(cmd5th0,shell=True) 
    subprocess.call(cmd5th1,shell=True)     
    subprocess.Popen(cmd5th,shell=True) 
    myapp.report_result_status("Show picking up and 2D-classification results by Relion2 ",0)
    myapp.report_result_cmd(" ")
    myapp.report_result_cmd(cmd5th)
    myapp.report_result_cmd(" ")
    time.sleep(3)
    subprocess.Popen(cmd6th,shell=True) 
    myapp.report_result_cmd(cmd6th)
    myapp.report_result_cmd(" ")
    myapp.report_result_cmd(" ")
    time.sleep(1)
    myapp.report_result_status("==> Finish 2D classification using %05d - %05d micrographs"%(num*(num_bat-1)+1,num*num_bat),0)
    myapp.report_result_status("",0)
   


def get_gpu_num():
    cmd="nvidia-smi -L"
    try:
        output=subprocess.check_output(cmd,shell=True).decode()
        gpu_num=len(output.split("\n"))-1
        #print("gpu:%d"%int(gpu_num))
    except:
        gpu_num=1
    return gpu_num


def rw_gctf_log(file,fname,flag_refice_local,mean_ref_local):

    with open(getwholename(fname)+"_SumCor.mrc","rb") as fh:
        header=fh.read(1024)
    headeri=st.unpack("256i",header)
    headerf=st.unpack("256f",header)
    mean = float(headerf[21]) #mean number 21
    nz=int(headeri[2])
    mean = nz*mean
    
    with open(file,"a") as f:
        fcntl.flock(f.fileno(),fcntl.LOCK_EX) # avoid file crash
        cmd = "grep -a -A 1 \"AmpCnst\" %s_SumCor_gctf.log | awk '{if(NR==2)print}'"%getwholename(fname)
        cmd2 = "awk '/Final Values/{print}' %s_SumCor_gctf.log "%getwholename(fname)
        cmd3 = "awk '/RES_LIMIT/{print}' %s_SumCor_gctf.log "%getwholename(fname)
                                                                           
        em_para=subprocess.check_output(cmd,shell=True).split()
        defocus_val=subprocess.check_output(cmd2,shell=True).split()
        res_limi=subprocess.check_output(cmd3,shell=True).split()

        rlnDefocusU = float(defocus_val[0])
        rlnDefocusV = float(defocus_val[1])
        rlnDefocusAngle = float(defocus_val[2])
        rlnVoltage = float(em_para[1])
        rlnSphericalAberration = float(em_para[0])
        rlnAmplitudeContrast = float(em_para[2])
        rlnMagnification = float(em_para[3])
        rlnDetectorPixelSize = float(em_para[4])
        rlnCtfFigureOfMerit = float(defocus_val[3])
        rlnEnergyLoss = float(mean*flag_refice_local/mean_ref_local)
        rlnFinalResolution = float(res_limi[-1])

        f.write("%s_SumCor.mrc %s_SumCor.ctf %12.6f %12.6f %12.6f %12.6f %12.6f %12.6f %12.6f %12.6f %12.6f %12.6f %12.6f\n"%(getwholename(getname(fname)), getwholename(getname(fname)), rlnDefocusU, rlnDefocusV, rlnDefocusAngle, rlnVoltage, rlnSphericalAberration, rlnAmplitudeContrast, rlnMagnification, rlnDetectorPixelSize, rlnCtfFigureOfMerit,rlnFinalResolution,rlnEnergyLoss))


def rw_gctf_log_read(fname):

    global mean_ref
    global flag_refice

    with open(getwholename(fname)+"_SumCor.mrc","rb") as fh:
        header=fh.read(1024)
    headerf=st.unpack("256f",header)
    mean = float(headerf[21]) #mean number 2
    
    cmd = "grep -a -A 1 \"AmpCnst\" %s_SumCor_gctf.log | awk '{if(NR==2)print}'"%getwholename(fname)
    cmd2 = "awk '/Final Values/{print}' %s_SumCor_gctf.log "%getwholename(fname)

    em_para=subprocess.check_output(cmd,shell=True).split()
    defocus_val=subprocess.check_output(cmd2,shell=True).split()

    rlnDefocusU = float(defocus_val[0])
    rlnDefocusV = float(defocus_val[1])
    rlnDefocusAngle = float(defocus_val[2])
    rlnVoltage = float(em_para[1])
    rlnSphericalAberration = float(em_para[0])
    rlnAmplitudeContrast = float(em_para[2])
    rlnMagnification = float(em_para[3])
    rlnDetectorPixelSize = float(em_para[4])
    rlnCtfFigureOfMerit = float(defocus_val[3])
    rlnEnergyLoss = float(mean*flag_refice/mean_ref)

    return rlnDefocusU, rlnDefocusV, rlnDefocusAngle, rlnCtfFigureOfMerit, rlnEnergyLoss


def mot2_call(cmd,prl,fn):
    global num4cls
    global proclist
    global flg_single
    global fnamelist

    myapp.report_result_status("start MotionCor2 and Gctf ==> %s "%(fn.split("/")[-1]),0) #writing report
    proc=subprocess.Popen(cmd,shell=True)
    proclist.append(proc)
    fnamelist.append(fn)
    if(num4cls%prl==0):
        while proclist:
            i=proclist.pop(0)
            fname=fnamelist.pop(0) 
            try:
                out,errs=i.communicate(timeout=600) # wait MotionCor2 until finish, but 10 min in maximum 
                time.sleep(1)
                def1,def2,defang,fom,fil = rw_gctf_log_read(fname) 
                myapp.report_result("%s_SumCor.mrc  %10.3f %10.3f %10.3f %10.3f %10.3f"%(getwholename(fname.split("/")[-1]),def1,def2,defang,fom,fil)) #writing report
                myapp.report_result_status("Done MotionCor2 and Gctf ==> %s "%(fname.split("/")[-1]),0) #writing report
                time.sleep(1)
            except:
                i.kill()
                print("Error in calling commands: %s"%cmd)
                myapp.report_result_status("Error in calling commands: %s"%cmd,1) 
                time.sleep(1)
                print("To Be Continued...")  
                myapp.report_result_status("To Be Continued",0) 
                out,errs=i.communicate()
                time.sleep(1)
    else:  
        time.sleep(5)

def cal_mot2(command,num,diameter,apix,kv,cs,frames,binn,cmdgctf,cmd2dcls):
    global list4cal	
    global num4cls
    global list4gpu
    global mot2_flg
    global num_bat
    global mean_ref
    global flag_refice
    global flg_single
    
    prl=len(list4gpu) #number of parallel processing for MotionCor2
    
    if(get_gpu_num() < prl):
        prl=get_gpu_num()
    
    while list4cal: # Reading File
        fname=list4cal.pop(0)
        #print(fname)
        try:
            if str(getext(fname)) != ".raw":
                cmdinfo="e2iminfo.py %s"%fname #reading header of file
                ret=subprocess.check_output(cmdinfo,shell=True).decode()
            else:
                print(fname)
                ret="0 1 2 3 4 5 6 7 8 9 10 dummy"
                pass
        except:
            print("Error in file format %s"%fname)
            break
        
        flg_single=0
        if(int(ret.split()[1])==1 and len(ret.split())==12): #In the case of Single image
            try:
                c_name=os.path.splitext(fname)[-2][:-5]        #read file name except last 4 digits
                c_extnum=int(os.path.splitext(fname)[-2][-4:]) #read last 4 digits
            except:
                pass
            else:
                flg_single=1 # change flag for single image, when finishing single data copy, go to 0

            if(flg_single == 0):
                try:
                    c_name =os.path.splitext(fname)[-2][:-3]    #read file name except last 2 digits
                    c_extnum=int(os.path.splitext(fname)[-2][-1:])+1
                    flg_single=1
                except:
                    print("%s is single image or done MotionCor2"%fname)
                    continue

            if (c_extnum==frames):   #In the case of finishing data reading
                if not os.path.isfile("%s_SumCor.mrc"%(c_name)): #working in only new file
                    cmd_new="newstack %s* %s.mrc"%(c_name,c_name)
                    subprocess.check_call(cmd_new,shell=True)
                    fname=c_name
                    flg_single=0
                else:
                    #During reading images
                    continue
        #In the case of Stack
        #print(flg_single)
        if os.path.isfile("%s_SumCor.mrc"%(getwholename(fname))) and flg_single == 0:
            myapp.report_result_status("Done MotionCor2 and Gctf ==> %s"%(fname.split("/")[-1]),0)
        if not os.path.isfile("%s_SumCor.mrc"%(getwholename(fname))) and flg_single == 0:  #working in only new file
            if ((str(getext(fname)) != ".mrc") and (str(getext(fname)) != ".mrcs") and  (str(getext(fname)) != ".tiff") and (str(getext(fname)) != ".tif")):
                cmd_trs="newstack %s %s.mrcs"%(fname,getwholename(fname))
                #cmd_rm="rm %s"%(event.src_path) #remove original image stack
                subprocess.check_call(cmd_trs,shell=True)
                print("Finished %s "%cmd_trs)
                #subprocess.check_call(cmd_rm,shell=True)
                fname=getwholename(fname)+".mrcs"
                time.sleep(2)
                
            cmd_gpu="-gpu %d"%(list4gpu[num4cls%prl])
            cmd_gctf="`which Gctf` --apix %f --kV %d --Cs %f %s --defL 2000 --ctfstar %s/temp_gctf.star %s_SumCor.mrc" %(apix, kv, cs,cmdgctf,path,getwholename(fname)) 
            cmd_gctflog= opath+" --generatelog %s/micrographs_all_gwatch.star %s %d %f "%(path,fname,flag_refice,mean_ref)
            cmd_thum="e2proc2d.py %s_SumCor.mrc %s_SumCor.png --meanshrink 4"%(getwholename(fname),getwholename(fname))
            
            if(getext(fname)==".tif" or getext(fname)==".tiff"):
                cmd="`which MotionCor2` -InTiff %s -OutMrc %s_SumCor.mrc %s %s && %s && %s && %s"%(fname,getwholename(fname), command,cmd_gpu,cmd_gctf,cmd_gctflog,cmd_thum)
            else:
                cmd="`which MotionCor2` -InMrc %s -OutMrc %s_SumCor.mrc %s %s && %s && %s && %s"%(fname,getwholename(fname), command,cmd_gpu,cmd_gctf,cmd_gctflog,cmd_thum)
            mot2_call(cmd,prl,fname)  
	
        if((num4cls/(flag_con*num_bat+1))== num) and (num4cls !=0): #when number of micrographs reached to setting number, they calculate 2D classification
            #print("Cal 2D class",num4cls)
            while proclist:# Wait to finish subprocess
                i=proclist.pop(0)
                fn=fnamelist.pop(0)
                try:
                    out,errs=i.communicate(timeout=600) # wait MotionCor2 process, but 10 min in maximum
                    time.sleep(1)
                    def1,def2,defang,fom,fil = rw_gctf_log_read(fn)
                    myapp.report_result("%s  %10.3f %10.3f %10.3f %10.3f %10.3f"%(fn.split("/")[-1],def1,def2,defang,fom,fil)) #writing report 
                    myapp.report_result_status("Done MotionCor2 and Gctf ==> %s "%(fn.split("/")[-1]),0) #writing report
                    time.sleep(1)
                except:
                    i.kill()
                    print("Error in calling commands: %s"%cmd)
                    myapp.report_result_status("Error in calling commands: %s"%cmd,1) 
                    time.sleep(1)
                    print("To Be Continued...")  
                    myapp.report_result_status("To Be Continued",0)
                    out,errs=i.communicate()
                    time.sleep(1)
            num_bat += 1
            cal_2dcls(diameter,apix,kv,cs,binn,num,cmd2dcls)
        num4cls += 1
    mot2_flg = 1 # finished cal_2dcls

def message_autoMot2(cmd1):
    app=QApplication(sys.argv)
    msgBox=QMessageBox()
    msgBox.setText(cmd1)
    #pickButton=msgBox.addButton("Picked up particles",QMessageBox.ActionRole)
    #clsButton=msgBox.addButton("Show 2D class",QMessageBox.ActionRole)
    abortButton=msgBox.addButton(QMessageBox.Close)
    msgBox.exec_()
    
class ChangeHandler(FileSystemEventHandler, QtCore.QThread):
    def __init__(self,command,fname,frames,flag,numM,diameter,apix,kv,cs,binn,path,cmdgctf,cmd2dcls):
        super(ChangeHandler, self).__init__()
        self.fname=fname #getname(fname)
        self.command=command
        self.frames=int(frames)
        self.flag=int(flag)
        self.num=int(numM)
        self.diameter=int(diameter)
        self.apix=float(apix)
        self.kv=int(kv)
        self.cs=float(cs)
        self.binn=int(binn)
        self.path=path
        self.cmdgctf=cmdgctf
        self.cmd2dcls=cmd2dcls

    def on_created(self, event):
        initime=time.time()
        global list4cal
        global mot2_flg
        global ti
        
        #print(str(getname(event.src_path)),str(self.fname),fnmatch.fnmatch(str(getname(event.src_path)),str(self.fname)))
        if not event.is_directory and fnmatch.fnmatch(str(getname(event.src_path)),str(self.fname)):
            #print(fname)
            for i in range(120):#waiting copy for 6 min
                file_size_bf=os.path.getsize(event.src_path)
                time.sleep(ti) #time interval waiting for data copy 
                if(os.path.getsize(event.src_path) == file_size_bf): # If file size not changed, it means finishing file copy.	
                    time.sleep(1) # For safety copy
                    list4cal.append(event.src_path) #Inputs
                    if mot2_flg == 1: # if finished running cal_mot2
                        cal_mot2(self.command,self.num,self.diameter,self.apix,self.kv,self.cs,self.frames,self.binn,self.cmdgctf,self.cmd2dcls) #call motionCor2 program
                    break
            if(time.time()-initime>360):
                print("Caution!!: Please check file name and so on!!")
        if not event.is_directory and str(getname(event.src_path)) == ".dummy.txt": #calling cal_mot2 for initial running
            cal_mot2(self.command,self.num,self.diameter,self.apix,self.kv,self.cs,self.frames,self.binn,self.cmdgctf,self.cmd2dcls) #call motionCor2 program
            subprocess.call("rm -f %s/.dummy.txt"%path,shell=True)

class WatchOutForFile(QtCore.QThread):
    def __init__(self, path, command,fname,frames,flag,numM,diameter,apix,kv,cs,binn,cmdgctf,cmd2dcls):
        super(WatchOutForFile, self).__init__()
        self.path = path
        self.fname=fname #getname(fname)
        self.command=command
        self.frames=frames
        self.flag=flag
        self.num=int(numM)
        self.diameter=int(diameter)
        self.apix=float(apix)
        self.kv=int(kv)
        self.cs=float(cs)
        self.binn=int(binn)
        self.cmdgctf=cmdgctf
        self.cmd2dcls=cmd2dcls
	#Run watchdog
        self.observer = Observer()
        self.event_handler = ChangeHandler(self.command,self.fname,self.frames,self.flag,self.num,self.diameter,self.apix,self.kv,self.cs,self.binn,self.path,self.cmdgctf,self.cmd2dcls)
        self.observer.schedule(self.event_handler, self.path, recursive=False)
        self.observer.start()

    def run(self):
        pass

class MyForm(QMainWindow):
    def __init__(self,parent=None):

        super(MyForm,self).__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        #Help message about automatic motionCor2
        self.ui.help_autoMot2.clicked.connect(self.message_help_autoMot2)

        #Open Directory
        self.ui.pushButton.clicked.connect(self.openDirectory)
        self.ui.help_directory.clicked.connect(self.message_directory)

        #open setting
        self.ui.actionOpen.triggered.connect(self.openSetting)

        #save setting
        self.ui.actionSave.triggered.connect(self.saveSetting)

        #File Name
        self.ui.lineEdit.setText(inifname)
        self.ui.help_watch_fn.clicked.connect(self.message_watch_fn)

        #Number of Frames
        self.ui.lineEdit_2.setText(inifnum)
        self.ui.horizontalSlider.setValue(int(inifnum))
        self.ui.lineEdit_2.textChanged.connect(self.on_slider)
        self.ui.horizontalSlider.valueChanged.connect(self.on_draw)
        self.ui.help_num_of_fra.clicked.connect(self.message_num_of_fra)

        #Do gain-reference
        self.ui.comboBox.setCurrentIndex(1) #set to No
        self.ui.comboBox.activated.connect(self.setting_combo1)
        self.ui.help_do_gain.clicked.connect(self.message_do_gain)

        #Do measure ice thickness
        self.ui.comboBox_4.setCurrentIndex(1) #set to No
        self.ui.comboBox_4.activated.connect(self.setting_combo3)
        self.ui.help_do_gain_2.clicked.connect(self.message_do_measure_ice)

        #Name of gain reference
        self.ui.lineEdit_3.setText(refnameg)
        self.ui.lineEdit_3.setEnabled(False)
        self.ui.pushButton_2.setEnabled(False)
        self.ui.label_6.setEnabled(False)
        self.ui.pushButton_2.clicked.connect(self.openFile)
        self.ui.help_gain_name.clicked.connect(self.message_gain_name)

        #Name of measure ice thickness
        self.ui.lineEdit_11.setText(refnameice)
        self.ui.lineEdit_11.setEnabled(False)
        self.ui.label_20.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.pushButton_3.clicked.connect(self.openFile_ice)
        self.ui.help_gain_name_2.clicked.connect(self.message_measure_ice_name)

        #Option for motionCor2
        self.ui.lineEdit_4.setText(iniadopi)
        self.ui.help_option.clicked.connect(self.message_help_option)

        #Run button
        self.ui.buttonBoxOK.clicked.connect(self.exeValue)
	
        #Cancel button
        self.ui.buttonBoxCancel.clicked.connect(self.closeWindow)
        
        #pixel size , Change additional value in MotionCor2
        self.ui.lineEdit_5.textChanged.connect(self.change_pix)

        #CS
        self.ui.lineEdit_6.textChanged.connect(self.change_cs)

        #kV
        self.ui.lineEdit_7.textChanged.connect(self.change_kv)
        
        #Option for GCTF
        self.ui.lineEdit_12.setText(iniadopigctf)
        #QtCore.QObject.connect(self.ui.help_option_3,QtCore.SIGNAL("clicked()"),self.message_help_option_gctf) #message
        self.ui.help_option_3.clicked.connect(self.message_help_option_gctf)

        #Binning
        self.ui.lineEdit_10.setText(inibin)
        #Automatcic classification initial value
        self.ui.label_14.setEnabled(False)   #How many Micrograph?
        self.ui.lineEdit_9.setText(iniMicro)	
        self.ui.lineEdit_9.setEnabled(False)
        self.ui.label_10.setEnabled(True)   #pix size
        self.ui.lineEdit_5.setText(iniPix)		
        self.ui.label_11.setEnabled(True)   #cs
        self.ui.lineEdit_6.setText(iniCs)		
        self.ui.label_12.setEnabled(True)   #kv
        self.ui.lineEdit_7.setText(iniKv)		
        self.ui.label_13.setEnabled(False)   #diameter
        self.ui.lineEdit_8.setEnabled(False)
        self.ui.lineEdit_8.setText(iniDia)
        self.ui.label_15.setEnabled(False)   #binning
        self.ui.lineEdit_10.setEnabled(False)
        self.ui.label_21.setEnabled(False)   #option for 2D class
        self.ui.lineEdit_13.setEnabled(False)
        
        #cal 2D classification
        self.ui.comboBox_2.setCurrentIndex(1) #set to No
        self.ui.comboBox_2.activated.connect(self.setting_combo2)
        #cal 2D classification every batch
        self.ui.comboBox_3.setCurrentIndex(1) #set to No
        self.ui.comboBox_3.activated.connect(self.setting_combo4)
        
        #Help automatic 2D classification
        self.ui.help_autoEva.clicked.connect(self.message_help_autoEva)

        #Help automatic 2D classification in batch mode
        self.ui.help_do_eva_2.clicked.connect(self.message_do_eva_batch)

        #Help GPU
        self.ui.help_option_2.clicked.connect(self.message_gpu)

        #Help Do classification
        self.ui.help_do_eva.clicked.connect(self.message_do_eva)

        #Help how many micrographs?
        self.ui.help_pixsize_5.clicked.connect(self.message_howmany)

        #Help Pixel size?
        self.ui.help_pixsize.clicked.connect(self.message_pixsize)

        #Help CS?
        self.ui.help_pixsize_2.clicked.connect(self.message_cs)

        #Help acceleration voltage?
        self.ui.help_pixsize_3.clicked.connect(self.message_av)

        #Help Particle diameter?
        self.ui.help_pixsize_4.clicked.connect(self.message_pd)

        #Help binning?
        self.ui.help_pixsize_6.clicked.connect(self.message_bin)

        #Option for relion2
        self.ui.lineEdit_13.setText(iniadopi2dcls)
        self.ui.help_option_4.clicked.connect(self.message_help_option_2dcls)

    def closeWindow(self):
        #print("Are you sure to close?")
        #event.accept()
        subprocess.call("rm -f %s/.dummy.txt"%path,shell=True)
        subprocess.call("rm -f %s/temp_gctf.star"%path,shell=True)
        
        import sys
        sys.exit()
        #event.accept()
                
    # Help message
    def report_result(self,text):
        self.ui.textBrowser.append(text)
        
    def report_result_cmd(self,text):
        self.ui.textBrowser_2.append(text)
        
    def report_result_status(self,text,err):
        if err:
            self.ui.textBrowser_3.setTextColor(QtGui.QColor(255,0,0))
        else:
            self.ui.textBrowser_3.setTextColor(QtGui.QColor(0,0,0))
        self.ui.textBrowser_3.append(text)
        
    def message_help_autoMot2(self):
        QMessageBox.information(self, "About Automatch MotionCor2", str("This program aumaticaly runs MotionCor2 and Gctf in a specified directory"
										"(Watching Directory) by a Python library called WatchDog. "
"At the same time, Gwatch make a file \" micrographs_all_gwatch.star for Relion2 \" "))

    def message_directory(self):
        QMessageBox.information(self, "About Watching Directory", str("Set a Watching Directory\n"
                                                                      "Defult is the current directory."))
        
    def message_watch_fn(self):
        QMessageBox.information(self, "About Watching File name", str("Set a File name \n"
                                                                      "This program runs on a stack/singles of frame data of movie mode."
                                                                      "You can use any file extension (e.g. .dm4, etc)."
                                                                      "This program automaticaly convert the file to mrc-file with  Newstack module in IMOD."
                                                                      "Strongly recommand use question marks for filename characters used for numbering images in digits, e.g. mrc_????.mrc, mrc_????_????.mrc in singles's case\n"))

    def message_num_of_fra(self):
        QMessageBox.information(self, "About Number of frame", str("Set number of frames in each stack.\n" 
                                                                   "You must enter this number correctly only when using single images "
                                                                   "because Gwatch reads the frame data up to this number in each stack before start processing\n"))
        
    def message_do_gain(self):
        QMessageBox.information(self, "About Do gain-reference", str("If set to Yes, MotionCor2 use a gain-reference before motion correction.\n"
                                                                     "You must type in the name of Gain-Refernece file. " 
                                                                     "Gwatch can automatically convert any file extension (e.g. .dm4 etc) to mrc with Newstack before performing MotionCor2\n"))

    def message_gain_name(self):
        QMessageBox.information(self, "About name of Gain-Refernece", str("Set the name of Gain-Refenrece.\n"
                                                                          "You set the path and type in the name of Gain-Refernece file\n"))
    def message_do_measure_ice(self):
        QMessageBox.information(self, "About Do Measure Ice-thickness ratio", str("If set to Yes, Gwatch can calcualte Ice-thickness ratio with/without every filter using an image (stack) without energy filter\n"
                                                                                  "So, you should prepare an unfiltered image(stack). Its value recored in \" micrographs_all_gwatch.star\" as EnergyLoss column."))

    def message_measure_ice_name(self):
        QMessageBox.information(self, "About Name of Image without energy filter", str("Set the name and path of an image(stack) without energy filter\n"))
    
    def message_gpu(self):
        QMessageBox.information(self, "About GPUs", str("Which GPUs to calculate MotionCor2?\n"
                                                        "Gwatch can use multi GPUs in MotionCor2 and Relion2. If you set check boxes of GPU lists, MotionCor2 run on a stack per each GPU. " 
                                                        "Because it's fast! \n"))

    def message_help_option(self):
        QMessageBox.information(self, "About option for MotionCor2", str("Set options for MotionCor2\n"
                                                                         "Below is the help message from MotionCor2 (See detail in MotionCor2 --help)\n"
                                                                         "-Gain     \n"
                                                                         "   MRC file that stores the gain reference. If not "
                                                                         "  specified, MRC extended header will be visited "
                                                                         "   to look for gain reference. \n"
                                                                         "-TmpFile     Temporary image file for debugging.\n"
                                                                         "-LogFile     Log file storing alignment data.\n"
                                                                         "-Patch    \n"
                                                                         "   Number of patches to be used for patch based"
                                                                         " alignment, default 0 0 corresponding full frame"
                                                                         " alignment.\n"
                                                                         "-MaskCent    Center of subarea that will be used for alignement,"
                                                                         " default 0 0 corresponding to the frame center.\n"
                                                                         "-MaskSize    The size of subarea that will be used for alignment,"
                                                                         " default 1.0 1.0 corresponding full size.\n"
                                                                         "-Iter        Maximum iterations for iterative alignment,"
                                                                         " default 5 iterations.\n"
                                                                         "-Tol         Tolerance for iterative alignment,"
                                                                         " default 0.5 pixel.\n"
                                                                         "-Bft         B-Factor for alignment, default 100.\n"
                                                                         "-FtBin       Binning performed in Fourier space, default 1.0.\n"
                                                                         "-InitDose    Initial dose received before stack is acquired\n"
                                                                         "-FmDose   \n"
                                                                         "   Frame dose in e/A^2. If not specified, dose"
                                                                         " weighting will be skipped.\n"
                                                                         "-PixSize  \n"
                                                                         "   Pixel size in A of input stack in angstrom. If not"
                                                                         " specified, dose weighting will be skipped.\n"
                                                                         "-kV          High tension in kV needed for dose weighting."
                                                                         " Default is 300.\n"
                                                                         "-Align       Generate aligned sum (1) or simple sum (0)\n"
                                                                         "-Throw       Throw initial number of frames, default is 0\n"
                                                                         "-Trunc       Truncate last number of frames, default is 0\n"
                                                                         "-Group       Group every specified number of frames by adding"
                                                                         " them together. The alignment is then performed"
                                                                         " on the summed frames. By default, no grouping"
                                                                         " is performed.\n"
                                                                         "-Crop        1. Crop the loaded frames to the given size.\n"
                                                                         "             2. By default the original size is loaded.\n"
                                                                         "-FmRef    \n"
                                                                         "   Specify which frame to be the reference to which"
                                                                         " all other frames are aligned. By default (-1) the"
                                                                         " the central frame is chosen. The central frame is"
                                                                         " at N/2 based upon zero indexing where N is the"
                                                                         " number of frames that will be summed, i.e., not"
                                                                         " including the frames thrown away.\n"
                                                                         "-Mag      \n"
                                                                         "   1. Correct anisotropic magnification by stretching"
                                                                         " image along the major axis, the axis where the"
                                                                         " lower magificantion is detected.\n"
                                                                         "   2. Three inputs are needed including magnifications"
                                                                         " along major and minor axes and the angle of the"
                                                                         " major axis relative to the image x-axis in degree.\n"
                                                                         "   3. By default no correction is performed.\n"))

    def message_help_option_gctf(self):
        QMessageBox.information(self, "About option for Gctf", str("Set options for Gctf\n"
                                                                "See help message from Gctf\n"))

    def message_help_option_2dcls(self):
        QMessageBox.information(self, "About option for 2D classification of Relion2", str("Set options for 2D classification by Relion2\n"
                                                                   "See help message from Relion2\n"))
        
    def message_help_autoEva(self):
        QMessageBox.information(self, "About automatic 2D-classification", str("Automatically starts running Gautomatch for particle image pick up, Relion2 for particle image extraction and 2D classification when the number of motion-corrected micrographs in the watching directory has reached the number you preset in the second box below. We strongly recommend to do automatically 2D-classification every 10-50 micrographs (~3,000 particles) using batch mode\n"))
        
    def message_do_eva(self):
        QMessageBox.information(self, "About calculate 2D-classification?", str("If set to Yes, "
"it automatically starts running Gautomatch for particle image pick up, Relion2 for particle image extraction and 2D classification when the number of motion-corrected micrographs in the watching directory has reached the number you preset in the second box below."
" Parameters for automatic 2D-classificaiton should be set in the boxes below. If set to No, Motion-corrected micrographs will simply be accumulated.\n"))

    def message_do_eva_batch(self):
        QMessageBox.information(self, "About calculate 2D-classification every batch?", str("If set to Yes, "
"it automatically starts running above 2D-classification procedure every number of motion-corrected micrographs you preset in the second box below.\n"))

    def message_howmany(self):
        QMessageBox.information(self, "About The number of Micrographs to be processed", str("Set number of micrograph to be processed by automatic 2D-classification, "
"When the number of motion-corrected micrographs in the watching directory has reached this number, it automatically runs Gautomatch and Relion2 for particle extraction and 2D classification. "
"A recommanded number would be 10-50 micrographs (~3,000 particles).\n"))

    def message_pixsize(self):
        QMessageBox.information(self, "About Pixel Size", str("Set the pixel size of micrographs.\n"
                                                              "In cryoARM, 0.59 in a magnification of 40k\n"
                                                              "0.56 in a magnification of 50k\n"
                                                              "0.44 in a magnification of 60k\n"
                                                              "0.34 in a magnification of 80k\n"))

    def message_av(self):
        QMessageBox.information(self, "About Acceleration Volatage", str("Set the value of acceleration voltage"))
        
    def message_cs(self):
        QMessageBox.information(self, "About Cs", str("Set the Cs value of the microscope in mm"))
        
    def message_pd(self):
        QMessageBox.information(self, "About Particle Diameter", str("Set value of particle diameter in angstrom\n"
                                                                     "When a slightly smaller diameter than the target particele (x0.8-0.9) is set, Gautomatch tends to pick up all particle images, but with many wrong ones. "
                                                                     "When a larger diameter (x1.0-1.1) is set, Gautomatch tends to pick up correct images but some of them will be missed.\n"))
        
    def message_bin(self):
        QMessageBox.information(self, "About Binning", str("Set value of binning factor (1,2,4...)\n"))

    def on_draw(self):
        self.ui.lineEdit_2.setText(str(self.ui.horizontalSlider.value()))

    def on_slider(self,string):
        self.ui.horizontalSlider.setValue(int(string))

    def setting_combo1(self,i): #setting reference name name
        #print self.ui.comboBox.currentIndex()	
        if(i==0): #YES
            self.ui.lineEdit_3.setEnabled(True)
            self.ui.label_6.setEnabled(True)
            self.ui.pushButton_2.setEnabled(True)  
        else:   #NO
            self.ui.lineEdit_3.setEnabled(False)
            self.ui.label_6.setEnabled(False)
            self.ui.pushButton_2.setEnabled(False)
            
    def setting_combo3(self,i): #setting refname ice thickness
        #print self.ui.comboBox.currentIndex()	
        if(i==0): #YES
            self.ui.lineEdit_11.setEnabled(True)
            self.ui.label_20.setEnabled(True)
            self.ui.pushButton_3.setEnabled(True)  
        else:   #NO
            self.ui.lineEdit_11.setEnabled(False)
            self.ui.label_20.setEnabled(False)
            self.ui.pushButton_3.setEnabled(False)
            
    def setting_combo2(self,i):
        #ind_com1=self.ui.comboBox.count()
        #print self.ui.comboBox_2.currentIndex()	
        if(i==0): #YES
            self.ui.label_14.setEnabled(True)   #How many Micrograph?
            self.ui.lineEdit_9.setEnabled(True)
            self.ui.label_10.setEnabled(True)   #pix size
            self.ui.lineEdit_5.setEnabled(True)
            self.ui.label_11.setEnabled(True)   #cs
            self.ui.lineEdit_6.setEnabled(True)
            self.ui.label_12.setEnabled(True)   #kv
            self.ui.lineEdit_7.setEnabled(True)
            self.ui.label_13.setEnabled(True)   #diameter
            self.ui.lineEdit_8.setEnabled(True)
            self.ui.label_15.setEnabled(True)   #diameter
            self.ui.lineEdit_10.setEnabled(True)
            self.ui.label_21.setEnabled(True)   #diameter
            self.ui.lineEdit_13.setEnabled(True)

        else:   #NO
            self.ui.label_14.setEnabled(False)   #How many Micrograph?
            self.ui.lineEdit_9.setEnabled(False)
            self.ui.label_13.setEnabled(False)   #diameter
            self.ui.lineEdit_8.setEnabled(False)
            self.ui.label_15.setEnabled(False)   #diameter
            self.ui.label_21.setEnabled(False)   #diameter
            self.ui.lineEdit_10.setEnabled(False)
            self.ui.lineEdit_13.setEnabled(False)
            
    def setting_combo4(self,i):
        global flag_con
        if(i==0): #YES
            flag_con = 1
        else:
            flag_con = 0

    def openDirectory(self):
        global path
        try:
            path=str(QFileDialog().getExistingDirectory(self,"open"))
        except:
            pass
        if path=="":
            print("Error in open directory, set current directory")
            path=os.getcwd()
        self.ui.pushButton.setText(path)
        self.ui.pushButton.setToolTip(path)
        
    def openFile(self):
        global refnameg
        global path
        refnameg=delspa(QFileDialog().getOpenFileName(self,"open",path)[0])
        self.ui.lineEdit_3.setText(refnameg)
        self.ui.lineEdit_3.setToolTip(refnameg)

    def message_opensetting(self):
        QMessageBox.information(self, "About open setting", str("Cannot open setting file. Error in setting file"))
   	
    def openSetting(self):
        setname=str(QFileDialog().getOpenFileName(self,"open",hpath)[0])
        if setname:
            print("Open setting file %s"%setname)
        else :
            print("Open setting file, No file... saving setting in ~/.Gwatch_setting ")

        try:
            with open(setname,"r") as iniparaFile: 
                #Automatic MotionCor2
                inifname=iniparaFile.readline() #File name
                fname=inifname
                inifnum=iniparaFile.readline()  #stack number 
                fnum=inifnum
                iniadopi=iniparaFile.readline() #option for motionCor2
                adopi=iniadopi
                
                #Automatic 2D classificaiton
                iniMicro=iniparaFile.readline() #number of file for automatic 2D classification
                iniPix=iniparaFile.readline()   #Pixel size
                iniCs=iniparaFile.readline()    #Cs
                iniKv=iniparaFile.readline()    #kV
                iniDia=iniparaFile.readline()   #diameter of particle
                refnameg=iniparaFile.readline() #Gain referencefile
                inibin=iniparaFile.readline()   #bin
                refnameice=iniparaFile.readline()   #Referencefile image for ice thickness
                iniadopigctf=iniparaFile.readline() #option for gctf
                iniadopi2dcls=iniparaFile.readline() #option for 2d classification
            
            int(str(delspa(inifnum)))
            float(str(delspa(iniPix)))
            float(str(delspa(iniCs)))
            float(str(delspa(iniKv)))
            float(str(delspa(iniDia)))
            int(str(delspa(iniMicro)))
            int(str(delspa(inibin)))

            self.ui.lineEdit_12.setText(iniadopigctf)
            self.ui.lineEdit_2.setText(inifnum)
            self.ui.lineEdit.setText(inifname)
            self.ui.lineEdit_3.setText(refnameg)
            self.ui.lineEdit_11.setText(refnameice)
            self.ui.lineEdit_4.setText(iniadopi)
            self.ui.lineEdit_9.setText(iniMicro)	
            self.ui.lineEdit_5.setText(iniPix)		
            self.ui.lineEdit_6.setText(iniCs)		
            self.ui.lineEdit_7.setText(iniKv)		
            self.ui.lineEdit_8.setText(iniDia)
            self.ui.lineEdit_13.setText(iniadopi2dcls)
            
        except:
            print("Error in reading %s"%setname)
            self.message_opensetting()
            #return
            #sys.exit()


    def saveSetting(self):
        setname=delspa(QFileDialog().getSaveFileName(self,"open",hpath)[0])
        tmpname,ext=os.path.splitext(setname)
        if ext=="":
            setname=tmpname+".txt"
        if setname:
            print("Save setting file %s"%setname)
        else :
            print("Save setting file, No file... saving setting in ~/.Gwatch_setting ")

        fname=self.ui.lineEdit.text().replace('\n','')
        fname=str(fname).strip().replace('\n','')
        fnum=self.ui.lineEdit_2.text().replace('\n','')
        adopi=self.ui.lineEdit_4.text().replace('\n','')
        refname=str(self.ui.lineEdit_3.text().replace('\n',''))
        refnameice=self.ui.lineEdit_11.text().replace('\n','')
        mnum=self.ui.lineEdit_9.text().replace('\n','')
        diameter=self.ui.lineEdit_8.text().replace('\n','')
        apix=self.ui.lineEdit_5.text().replace('\n','')
        cs=self.ui.lineEdit_6.text().replace('\n','')
        kv=self.ui.lineEdit_7.text().replace('\n','')
        binn=self.ui.lineEdit_10.text().replace('\n','')
        adopigctf=self.ui.lineEdit_12.text().replace('\n','')
        adopi2dcls=self.ui.lineEdit_13.text().replace('\n','')
        try:
            int(str(delspa(fnum)))
            float(str(delspa(apix)))
            float(str(delspa(cs)))
            int(str(delspa(kv)))
            float(str(delspa(diameter)))
            int(str(delspa(mnum)))
            int(str(delspa(binn)))
        except:
            print("Error in parameter, please check file number, apix, cs, kv, number of micrographs, bin, diameter, ")
        with open(setname,"w") as paraFile:
            paraFile.write(fname.replace('\n','')+"\n") #File name
            paraFile.write(fnum.replace('\n','')+"\n")  #stack number 
            paraFile.write(adopi.replace('\n','')+"\n") #option for motionCor2
            paraFile.write(mnum.replace('\n','')+"\n")  #number of file for automatic 2D classification
            paraFile.write(apix.replace('\n','')+"\n")  #Pixel size
            paraFile.write(cs.replace('\n','')+"\n")    #Cs
            paraFile.write(kv.replace('\n','')+"\n")    #kV
            paraFile.write(diameter.replace('\n','')+"\n")  #diameter of particle
            paraFile.write(refname.replace('\n','')+"\n")     #Gain referencefile
            paraFile.write(binn.replace('\n','')+"\n")
            paraFile.write(refnameice.replace('\n','')+"\n") #Referencefile for ice thickness
            paraFile.write(adopigctf.replace('\n','')+"\n")  #option for gctf
            paraFile.write(adopi2dcls.replace('\n','')+"\n") #option for 2D classification
            
    def openFile_ice(self):
        global refnameice
        global path
        refnameice=str(QFileDialog().getOpenFileName(self,"open",path)[0])
        self.ui.lineEdit_11.setText(refnameice)

    def change_pix(self):
        try:
            pix=float(self.ui.lineEdit_5.text())
            add_option=str(self.ui.lineEdit_4.text()).lower() # transfer additional option command to lower case letter
            add_option_org=str(self.ui.lineEdit_4.text())
            pix_org=add_option.split()[add_option.split().index("-pixsize")+1]
            spn=re.search("-pixsize "+pix_org,add_option).span()
            add_option_org=add_option_org.replace(add_option_org[spn[0]:spn[1]],"-Pixsize %.3f"%pix)
        except ValueError:
            print("No Pixel size in additional option or Invalid value in Pixel size")
            return
        except:
            print("Invalid value in Pixel size")
            return   
        self.ui.lineEdit_4.setText(add_option_org)

    def change_kv(self):
        try:
            kv=int(self.ui.lineEdit_7.text())
            add_option=str(self.ui.lineEdit_4.text()).lower() # transfer additional option command to lower case letter
            add_option_org=str(self.ui.lineEdit_4.text())
            kv_org=add_option.split()[add_option.split().index("-kv")+1]
            spn=re.search("-kv "+kv_org,add_option).span()
            #print(add_option_org[spn[0]:spn[1]])
            add_option_org=add_option_org.replace(add_option_org[spn[0]:spn[1]],"-Kv %d"%kv)
        except ValueError:
            print("No kV in additional option or Invalid value in kV")
            return
        except:
            print("Invalid value in kV")
            return                
       
        self.ui.lineEdit_4.setText(add_option_org)
        
        
    def change_cs(self):
        try:
            cs=float(self.ui.lineEdit_6.text())
            add_option=str(self.ui.lineEdit_4.text()).lower() # transfer additional option command to lower case letter
            add_option_org=self.ui.lineEdit_4.text()   
            cs_org=add_option.split()[add_option.split().index("-cs")+1]
            spn=re.search("-cs "+cs_org,add_option).span()
            add_option_org=add_option_org.replace(add_option_org[spn[0]:spn[1]],"-Cs %2.2f"%cs)
        except ValueError:
            print("No CS in additional option or Invalid value in CS")
            return
        except:
            print("Invalid value in CS")
            return                
            
        self.ui.lineEdit_4.setText(add_option_org)
    
    def exeValue(self):	
        global list4cal
        global list4gpu
        global path
        global flag_refice
        global mean_ref

        fname=self.ui.lineEdit.text().replace('\n','')
        fname=str(fname).strip().replace('\n','')
        fnum=self.ui.lineEdit_2.text().replace('\n','')
        adopi=self.ui.lineEdit_4.text().replace('\n','')
        refname=str(self.ui.lineEdit_3.text().replace('\n',''))
        refnameice=self.ui.lineEdit_11.text().replace('\n','')
        mnum=self.ui.lineEdit_9.text().replace('\n','')
        diameter=self.ui.lineEdit_8.text().replace('\n','')
        apix=self.ui.lineEdit_5.text().replace('\n','')
        cs=self.ui.lineEdit_6.text().replace('\n','')
        kv=self.ui.lineEdit_7.text().replace('\n','')
        binn=self.ui.lineEdit_10.text().replace('\n','')
        adopigctf=self.ui.lineEdit_12.text().replace('\n','')
        adopi2dcls=self.ui.lineEdit_13.text().replace('\n','')
	
        #Check GPU index
        gpu0=self.ui.checkBox_0.isChecked() 
        gpu1=self.ui.checkBox_1.isChecked()
        gpu2=self.ui.checkBox_2.isChecked()
        gpu3=self.ui.checkBox_3.isChecked()
        list4gpu=[ii for ii, x in enumerate([gpu0,gpu1,gpu2,gpu3]) if x==True] #making GPU list
        if (list4gpu ==[]):  #if empty, return [0]
            list4gpu=[0]
            
        if (self.ui.comboBox_3.currentIndex()==0):  #1 No, 0 Yes 
            flag_con=1 # Flag for continous 2D classification
            
        if (self.ui.comboBox_2.currentIndex()==1): #1 No, 0 Yes
            mnum="10000" #If set "no" on automatic 2Dclassification
            
        self.ui.buttonBoxOK.setEnabled(False)
        self.ui.label_2.setEnabled(False)   #wacthing directory
        self.ui.pushButton.setEnabled(False)   
        self.ui.label_3.setEnabled(False)   #wacthing file name
        self.ui.lineEdit.setEnabled(False)   
        self.ui.label_4.setEnabled(False)   #number of frame
        self.ui.lineEdit_2.setEnabled(False)   
        self.ui.horizontalSlider.setEnabled(False)   
        self.ui.label_5.setEnabled(False)   #do gain?
        self.ui.comboBox.setEnabled(False)   
        self.ui.label_6.setEnabled(False)   #name gain reference
        self.ui.lineEdit_3.setEnabled(False)   
        self.ui.pushButton_2.setEnabled(False)   
        self.ui.label_7.setEnabled(False)   #option
        self.ui.lineEdit_4.setEnabled(False)   
        self.ui.label_9.setEnabled(False)   #do 2Dclassfication?
        self.ui.comboBox_2.setEnabled(False)  
        self.ui.label_18.setEnabled(False)   #do 2Dclassfication every batch?
        self.ui.comboBox_3.setEnabled(False)  
        self.ui.label_19.setEnabled(False)   #do measure ice thickness
        self.ui.comboBox_4.setEnabled(False)
        self.ui.label_14.setEnabled(False)   #How many Micrograph?
        self.ui.lineEdit_9.setEnabled(False)
        self.ui.label_10.setEnabled(False)   #pix size
        self.ui.lineEdit_5.setEnabled(False)
        self.ui.label_11.setEnabled(False)   #cs
        self.ui.lineEdit_6.setEnabled(False)
        self.ui.label_12.setEnabled(False)   #kv
        self.ui.lineEdit_7.setEnabled(False)
        self.ui.label_13.setEnabled(False)   #diameter
        self.ui.lineEdit_8.setEnabled(False)
        self.ui.label_15.setEnabled(False)   #binning
        self.ui.lineEdit_10.setEnabled(False) 
        self.ui.label_16.setEnabled(False)
        self.ui.lineEdit_11.setEnabled(False)
        self.ui.label_21.setEnabled(False)
        self.ui.lineEdit_13.setEnabled(False) 
        self.ui.label_17.setEnabled(False)
        self.ui.lineEdit_12.setEnabled(False) 
        
        self.ui.label_20.setEnabled(False)
        self.ui.pushButton_3.setEnabled(False)
        self.ui.checkBox_0.setEnabled(False)
        self.ui.checkBox_1.setEnabled(False)
        self.ui.checkBox_2.setEnabled(False)
        self.ui.checkBox_3.setEnabled(False)


        self.report_result("Recording results to micrographs_all_gwatch.star ...")
        self.report_result("Show result from micrographs_all_gwatch.star")
        self.report_result("Filename  DefocusU   DefocusV    angle     FoM    IcethicknessRatio")

        #making initial file for next open
        with open("%s/.Gwatch_setting"%hpath,"w") as iniparaFile:
            iniparaFile.write(fname.replace('\n','')+"\n") #File name
            iniparaFile.write(fnum.replace('\n','')+"\n")  #stack number 
            iniparaFile.write(adopi.replace('\n','')+"\n") #option for motionCor2
            iniparaFile.write(mnum.replace('\n','')+"\n")  #number of file for automatic 2D classification
            iniparaFile.write(apix.replace('\n','')+"\n")  #Pixel size
            iniparaFile.write(cs.replace('\n','')+"\n")    #Cs
            iniparaFile.write(kv.replace('\n','')+"\n")    #kV
            iniparaFile.write(diameter.replace('\n','')+"\n")  #diameter of particle
            iniparaFile.write(refname.replace('\n','')+"\n")     #Gain referencefile
            iniparaFile.write(binn.replace('\n','')+"\n")
            iniparaFile.write(refnameice.replace('\n','')+"\n") #Referencefile for ice thickness
            iniparaFile.write(adopigctf.replace('\n','')+"\n")  #option for gctf
            iniparaFile.write(adopi2dcls.replace('\n','')+"\n") #option for 2D classification
     
        if (self.ui.comboBox.currentIndex()==0): # and os.path.isfile(refname)): 
            flgRef=1  #flag for gain reference
            if(getext(refname) !="mrc"):  
                subprocess.call("e2proc2d.py %s %s/gain.mrc"%(refname,path),shell=True)
                out_name = path+"/"+"gain.mrc"
                print("Convert %s to gain.mrc"%refname)
                refname=out_name
                    
            if(os.path.isfile(refname)):
                ref="-Gain %s"%refname
                command="%s %s"%(adopi.replace('\n',''),ref)  
            else:
                print("Error! %s is invalid file"%refname)
                sys.exit()
                
        else:		
            flgRef=4  #file size is 4 times when Gain reference included in header
            ref=""
            command=adopi
                
        if (self.ui.comboBox_4.currentIndex()==0): 
            if(getext(refnameice) != "mrc"): #if referecen file of ice thickness is not mrc file, convert  
                try:
                    subprocess.call("newstack %s %s/temp_ice.mrc"%(refnameice,path),shell=True)
                    refnameice="%s/temp_ice.mrc"%path
                except:
                    print("Error! %s is invalid file"%refnameice)
                    sys.exit()
            refnameice=str(refnameice)
                  
            if(os.path.isfile(refnameice)):
                with open(refnameice,"rb") as f: # Read header and record mean
                    header=f.read(1024)
                headeri=st.unpack("256i",header)
                headerf=st.unpack("256f",header)
                mean = float(headerf[21]) #mean number 21
                nz=int(headeri[2])
                mean = nz*mean
                   
                flag_refice=1 # Flag for ice ratio
                mean_ref=mean
            else:
                print("Error! %s is invalid file"%refnameice)
                sys.exit()

        else:			
            mean_ref=1.0

        #Read current directory and find existed files
        fildir=str(path)+"/"+fname
                
        for ii in sorted(glob.glob(str(fildir))):
            list4cal.append(ii)

        file_gall=str(path)+"/micrographs_all_gwatch.star"
        if os.path.isfile(file_gall) != True:
            #print(file_gall)
            try:
                with open(file_gall,"w") as fg:
                    fg.write("\n")
                    fg.write("data_ \n")
                    fg.write("\n")
                    fg.write("loop_ \n")
                    fg.write("_rlnMicrographName #1\n")
                    fg.write("_rlnCtfImage #2\n")
                    fg.write("_rlnDefocusU #3\n")
                    fg.write("_rlnDefocusV #4\n")
                    fg.write("_rlnDefocusAngle #5\n")
                    fg.write("_rlnVoltage #6\n")
                    fg.write("_rlnSphericalAberration #7\n")
                    fg.write("_rlnAmplitudeContrast #8\n")
                    fg.write("_rlnMagnification #9\n")
                    fg.write("_rlnDetectorPixelSize #10\n")
                    fg.write("_rlnCtfFigureOfMerit #11\n")
                    fg.write("_rlnFinalResolution #12\n")
                    fg.write("_rlnEnergyLoss #13\n")
            except:
                print("Error in loading relion_procedure, Please check relion files")
                sys.exit()
        print("Reading %4d existed files..."%(len(list4cal)))
        myapp.report_result_status("Reading %4d existed files..."%(len(list4cal)),0)

        self.fileWatcher=WatchOutForFile(path,command,fname,fnum,flgRef,mnum,diameter,apix,kv,cs,binn,adopigctf,adopi2dcls) 
        self.fileWatcher.start() #Start watchdog!
        
        subprocess.call("rm -f %s/.dummy.txt"%path,shell=True)
        time.sleep(1)
        subprocess.call("touch %s/.dummy.txt"%path,shell=True)
        

if __name__=='__main__':
    if len(sys.argv) == 6 and sys.argv[1] == "--generatelog":
        try:
            file = str(sys.argv[2])
            fname = str(sys.argv[3])
            flag_ice_local = int(str(sys.argv[4]))
            ref_mean_local = float(str(sys.argv[5]))
        
            rw_gctf_log(file,fname,flag_ice_local,ref_mean_local)
        except:
            print("USAGE: Gwatch_v32.py --generatelog <file> <filename> <flag> <mean value>")
            sys.exit()
    elif len(sys.argv) == 2 and (sys.argv[1] == "--help" or sys.argv[1] == "-h"):
        print("USAGE:Gwatch_v32.py")
        print("See help on Gwatch_v32.py")
        sys.exit()
    elif len(sys.argv) == 3 and (sys.argv[1] == "--time_interval" or sys.argv[1] == "-t"):
        print("Set time interval to wait data copying")
        ti=int(sys.argv[2])
        app=QApplication(sys.argv)
        myapp=MyForm()
        myapp.show()
        sys.exit(app.exec_())
    else:
        app=QApplication(sys.argv)
        myapp=MyForm()
        myapp.show()
        sys.exit(app.exec_())

