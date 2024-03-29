#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
This application is a use case from the EU-Brazil Atmosphere project. For more
information on the project, visit our website at https://www.atmosphere-eubrazil.eu/.
The original application is hosted at the project's GitHub repository at
https://github.com/eubr-atmosphere/radiomics.

Copyright: QUIBIM SL – Quantitative Imaging Biomarkers in Medicine - www.quibim.com
"""

import sys, getopt
import os
import numpy as np
import video_frames as vf
import view_classification as vc
import doppler_segmentation as ds
import texture_analysis as tex
import textures_classification as tc
import hashlib
import PIL.Image

import warnings
warnings.filterwarnings("ignore")

def extract_and_anonymise(videos_path,input_v,videos_path_out,output_v):
    vfull_in=os.path.join(videos_path, input_v)
    print('Extracting and anonymising: %s' % vfull_in)
    frames = vf.load_video(vfull_in)
    index = 0
    for fr in frames:
        dimy, dimx, depth = fr.shape
        for i in range(0,int(dimy/6)):
            for j in range(int(2*dimx/3)-10,dimx):
                fr[i][j][0]=0
                fr[i][j][1]=0
                fr[i][j][2]=0
                
        directory=os.path.join(videos_path_out, output_v)
        if not os.path.exists(directory):
            os.makedirs(directory)

        vfull_out=os.path.join(directory, str(index)+'.png')
        index = index+1
        imagen=PIL.Image.fromarray(fr)
        imagen.save(vfull_out, 'png')



if __name__ == '__main__':
    try:
       opts, args = getopt.getopt(sys.argv[1:],"hi:o:",["help=","folder=","inputfolder=","outputfolder="])

    except getopt.GetoptError:
       print('main.py -i <inputvideosfolder> -o <output videos folder>')
       sys.exit(2)

    for opt, arg in opts:
       print("opt: %s, arg: %s" % (opt, arg))
       if opt == '-h':
          print('main.py -i <input videos folder> -o <output videos folder>')
          sys.exit()
       elif opt in ("-i", "--inputfolder"):
          input_videos_path = arg
       elif opt in ("-o", "--outputfolder"):
          output_videos_path = arg

#    print("Input dir: %s" % input_videos_path)
#    print("Output dir: %s" % output_videos_path)

    videos = os.listdir(input_videos_path)
    videos_path_out = output_videos_path 
    for v in videos:
        if not v.startswith('.') and v.lower().endswith('.mp4'):
            file_path=os.path.join(input_videos_path, v)
            print('Check %s' % file_path)
            if vf.if_doppler(file_path):
                hash_object = hashlib.md5(file_path.encode())
                output_v=hash_object.hexdigest()
                extract_and_anonymise(input_videos_path,v,videos_path_out,output_v)
