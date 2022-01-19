#!/usr/bin/env python




#
# Get shower shapes patterns from file
#
def getPatterns( path, cv, sort):

  pidname = 'el_lhmedium'
  from kepler.pandas import load_hdf
  import numpy as np
  df = load_hdf(path)
  df = df.loc[ ((df[pidname]==True) & (df.target==1.0)) | ((df.target==0) & (df['el_lhvloose']==False) ) ]
  df = df.loc[ df['trig_L2_el_hastrack'] == True ] # only rows with track information 

  target      = df['target'].values.astype(np.int16)

  n = target.shape[0]
  data_etOverPt = df['trig_L2_el_etOverPt'].astype(np.float32).to_numpy().reshape((n,1))  / 1
  data_deta     = df['trig_L2_el_trkClusDeta'].astype(np.float32).to_numpy().reshape((n,1))  / 1.
  data_dphi     = df['trig_L2_el_trkClusDphi'].astype(np.float32).to_numpy().reshape((n,1))  / 1.


  # This is mandatory
  splits = [(train_index, val_index) for train_index, val_index in cv.split(data_deta,target)]

  data_trk = np.concatenate( (data_etOverPt, data_deta, data_dphi), axis=1)

  # split for this sort
  x_train = [ data_trk[splits[sort][0]] ]
  x_val   = [ data_trk[splits[sort][1]] ]
  y_train = target [ splits[sort][0] ]
  y_val   = target [ splits[sort][1] ]

  avgmu = df.avgmu.values
  avgmu_train = avgmu[splits[sort][0]]
  avgmu_val = avgmu[splits[sort][1]]

  return x_train, x_val, y_train, y_val, avgmu_train, avgmu_val, splits




import argparse
import sys,os,traceback


parser = argparse.ArgumentParser(description = '', add_help = False)
parser = argparse.ArgumentParser()


parser.add_argument('-t','--tunedFile', action='store',
        dest='tunedFile', required = True,
            help = "The tuned file to be reprocess.")

parser.add_argument('-v','--volume', action='store',
        dest='volume', required = True, default = None,
            help = "The volume.")

parser.add_argument('-d','--dataFile', action='store',
        dest='dataFile', required = True, default = None,
            help = "The data file used to train the model.")

parser.add_argument('-r','--refFile', action='store',
        dest='refFile', required = True, default = None,
            help = "The reference file.")


if len(sys.argv)==1:
  parser.print_help()
  sys.exit(1)

args = parser.parse_args()



try:


  targets = [
                # cutbased!
                ('tight' , 'trig_L2_cl_tight'       ),
                ('medium', 'trig_L2_cl_medium'      ),
                ('loose' , 'trig_L2_cl_loose'       ),
                ('vloose', 'trig_L2_cl_vloose'      ),
                ]


  
  from saphyra.decorators import Summary, Reference,LinearFit



  fit = LinearFit(args.refFile, targets, 
                  xbin_size=0.05, 
                  ybin_size=0.5, 
                  ymin=16, 
                  ymax=60,  
                  min_avgmu=16, 
                  max_avgmu=100, 
                  false_alarm_limit=0.5)



  decorators = [Summary(), Reference(args.refFile, targets), fit]
  
  from sklearn.model_selection import StratifiedKFold
  from saphyra.applications import BinaryClassificationJob
  
  cv = StratifiedKFold(n_splits=10, random_state=512, shuffle=True)
  
  from saphyra import PatternGenerator
  from saphyra.utils import reprocess
  
  reprocess( PatternGenerator( args.dataFile, getPatterns), args.tunedFile, args.volume, cv, decorators )


  # necessary to work on orchestra
  from saphyra import lock_as_completed_job
  lock_as_completed_job(args.volume if args.volume else '.')

  sys.exit(0)

except  Exception as e:
  print(e)
  traceback.print_exc()

  # necessary to work on orchestra
  from saphyra import lock_as_failed_job
  lock_as_failed_job(args.volume if args.volume else '.')

  sys.exit(1)





