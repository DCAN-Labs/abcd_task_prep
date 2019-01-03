#!/usr/bin/env python

import numpy as np
import pandas as pd
import sys, io, os
from readEPrime import ReadEPrimeFile


# Extract a single run from a data frame
def GetRun(dataFrame, run, scanner, software_version="NONE", verbose=True):

    indexC = dataFrame['Procedure[Trial]'].str.contains('WaitScreen', na=False)
    waitIndex = dataFrame.index[indexC]

    if scanner in ['Siemens', 'Philips']:
        scannerType = "SIEMENS/PHILIPS"
        startIndices = waitIndex
        if run>len(startIndices)-1:
            raise AttributeError('Run not found')
        startTime = dataFrame['SiemensPad.OnsetTime'][startIndices[run]]

    elif scanner == 'GE':
        scannerType = "GE"
        indexC = dataFrame['Procedure[Block]'].str.contains('Cue', na=False)
        if software_version == 'DV25':
            drop_frames = 5
        elif software_version == 'DV26':
            drop_frames = 16
        startIndices = (dataFrame.index[indexC]-1).intersection(waitIndex) - drop_frames
        if run>len(startIndices)-1:
            raise AttributeError('Run not found')
        startTime = dataFrame['GetReady.RTTime'][startIndices[run]]

    else:
        raise AttributeError('Scanner not identified')

    if run>len(startIndices):
        print('***** Asked for run {0}, but only {1} runs in file', run, len(startIndices))

       
    if verbose:
        print('Scanner is {0}, start time is {1}'.format(scannerType, startTime))

    startIndex = startIndices[run]
    if run==len(startIndices)-1:
        endIndex = len(dataFrame)
    else:
        endIndex = startIndices[run+1]
        
    if verbose:
        print('Run {0}, indices {1} to {2}'.format(run, startIndex, endIndex-1))
    subFrame = dataFrame[startIndex:endIndex]

    return subFrame, startTime


def EPrimeCSVtoFSL_nBack(filename, scanner, software_version="NONE", verbose=True):
    dataFrame = ReadEPrimeFile(filename)

    # We have both GetReady and GetReady2. Combine them.
    dataFrame['GetReady.RTTime'] = dataFrame[['GetReady.RTTime','GetReady2.RTTime']].fillna(0).max(axis=1)

    # We have both CueTarget.OnsetTime and Cue2Back.OnsetTime. Combine them.
    dataFrame['Cue.OnsetTime'] = dataFrame[['CueTarget.OnsetTime','Cue2Back.OnsetTime']].fillna(0).max(axis=1)

    path, fname = os.path.split(filename)
    behave = ''

    includeCue = False
    wmDict = {'0Back':'Cue0BackPROC', '2Back':'Cue2BackPROC'}

    for run in range(0,2):
        if verbose:
            print('Processing run {0}'.format(run))
    
        subFrame, startTime = GetRun(dataFrame, run, scanner, software_version, verbose)

        for wm in wmDict:
            wmLoad = subFrame['Procedure[Block]'].str.contains(wmDict[wm], na=False)
            wmIndices = subFrame.index[wmLoad]
    
            for emotion in {'NegFace', 'NeutFace', 'PosFace', 'Place'}:
                matchStim = subFrame['StimType'].str.contains(emotion, na=False)
                indices = (subFrame.index[matchStim]-1).intersection(wmIndices)

                if includeCue:
                    trialTime = (subFrame.loc[indices, 'Cue.OnsetTime'] - startTime)*0.001
                    duration = 27.5
                else:
                    trialTime = (subFrame.loc[indices+1, 'Stim.OnsetTime'] - startTime)*0.001
                    duration = 25.0

                if verbose:
                    print('{0:6} {1:10} {2} {3} trials'.format(wm, emotion, run+1, len(trialTime))) 

                FSLoutput = pd.DataFrame(trialTime)
                FSLoutput['duration']=duration
                FSLoutput['value']=1.0

                FSLoutput.to_csv(os.path.join(path,'{0}-{1}-{2}.txt'.format(wm,emotion,run+1)), \
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

            FSLoutput.to_csv(os.path.join(path,'nBack-Instructions-{0}.txt'.format(run+1)), \
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
