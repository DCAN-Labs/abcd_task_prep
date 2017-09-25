#!/usr/bin/python

import numpy as np
import pandas as pd
import sys, io, os
from readEPrime import ReadEPrimeFile

def EPrimeCSVtoFSL_nBack(filename, verbose=True):
    dataFrame = ReadEPrimeFile(filename)
    path, fname = os.path.split(filename)
    behave = ''

    includeCue = False
    wmDict = {'0Back':'Cue0BackPROC', '2Back':'Cue2BackPROC'}

    indexC = dataFrame['Procedure[Trial]'].str.contains('WaitScreen', na=False)
    waitIndex = np.flatnonzero(indexC)

    if verbose:
        print('Found {0} runs'.format(len(waitIndex)))

    for run in range(len(waitIndex)):
        if verbose:
            print('Processing run {0}'.format(run))
    
        startIndex = waitIndex[run]
        if run==len(waitIndex)-1:
           endIndex = len(dataFrame)
        else:
            endIndex = waitIndex[run+1]
        
        if verbose:
            print('Run {0}, indices {1} to {2}'.format(run, startIndex, endIndex-1))
    
        subFrame = dataFrame[startIndex:endIndex]
        startTime = subFrame['SiemensPad.OnsetTime'][startIndex]

        for wm in wmDict:
            wmLoad = subFrame['Procedure[Block]'].str.contains(wmDict[wm], na=False)
            wmIndices = subFrame.index[wmLoad]
    
            for emotion in {'NegFace', 'NeutFace', 'PosFace', 'Place'}:
                matchStim = subFrame['StimType'].str.contains(emotion, na=False)
                indices = (subFrame.index[matchStim]-1).intersection(wmIndices)

                if includeCue:
                    # Alternative is CueTarget.OnsetTime and Cue2Back.OnsetTime
                    trialTime = (subFrame.loc[indices, 'CueFix.OffsetTime'] - startTime)*0.001
                    duration = 27.5
                else:
                    trialTime = (subFrame.loc[indices+1, 'Stim.OnsetTime'] - startTime)*0.001
                    duration = 25.0

                if verbose:
                    print('{0:6} {1:10} {2} {3} trials'.format(wm, emotion, run+1, len(trialTime))) 

                FSLoutput = pd.DataFrame(trialTime)
                FSLoutput['duration']=duration
                FSLoutput['value']=1.0

                FSLoutput.to_csv(path+'/{0}-{1}-{2}.txt'.format(wm,emotion,run+1), \
                                 header=False, index=False, sep='\t', float_format='%.3f')

   
        if includeCue == False:
            cue = subFrame['Procedure[Block]'].str.contains('Cue', na=False)
            cueIndices = subFrame.index[cue]
            trialTime = (subFrame.loc[cueIndices, 'CueFix.OffsetTime'] - startTime)*0.001

            if verbose:
                print('Found {0} trials of type Instructions'.format(len(cueIndices)))

            FSLoutput = pd.DataFrame(trialTime)
            FSLoutput['duration']=2.5
            FSLoutput['value']=1.0

            FSLoutput.to_csv(path+'/nBack-Instructions-{0}.txt'.format(run+1), \
                                 header=False, index=False, sep='\t', float_format='%.3f')

        # Behavior data: Success rates and reaction times for each run and WM load
        for wmLoad in sorted({'0-Back', '2-Back'}):
            trials = subFrame['BlockType'].str.contains(wmLoad, na=False)
            wmIndices = subFrame.index[trials]
            acc = np.mean(subFrame.loc[wmIndices,'Stim.ACC'])
            # Calculate the mean reaction time with responses only
            tmp = subFrame.loc[wmIndices,'Stim.RT']
            if tmp.astype(bool).sum()>0:
                rt = tmp.sum() // tmp.astype(bool).sum()
            else:
                rt = 0.0

            #behave = behave + wmLoad
            behave = behave + '{0:.3f},'.format(acc)
            behave = behave + '{0:.0f},'.format(rt)

           

    return behave


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: {0} <E-Prime .CSV file>".format(sys.argv[0]))
        sys.exit(1)

    EPrimeCSVtoFSL_nBack(sys.argv[1])
