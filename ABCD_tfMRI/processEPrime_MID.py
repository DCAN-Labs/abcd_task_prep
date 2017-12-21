#!/usr/bin/env python
import numpy as np
import pandas as pd
import sys, io, os
from readEPrime import ReadEPrimeFile


# Extract a single run from a data frame
def GetRun(dataFrame, run, verbose=True):

    indexC = dataFrame['Procedure[Trial]'].str.contains('WaitScreen', na=False)
    waitIndex = dataFrame.index[indexC]

    if len(waitIndex)<3:
        scannerType = "SIEMENS/PHILIPS"
        startIndices = waitIndex
        if run>len(startIndices)-1:
            raise AttributeError('Run not found')
        startTime = dataFrame['SiemensPad.OnsetTime'][startIndices[run]]

    elif (len(waitIndex) % 16) == 0:
        scannerType = "GE"
        indexC = dataFrame['Procedure[Trial]'].str.contains('PrepProc', na=False)
        startIndices = (dataFrame.index[indexC]-1).intersection(waitIndex) - 5
        if run>len(startIndices)-1:
            raise AttributeError('Run not found')
        startTime = dataFrame['GetReady.RTTime'][startIndices[run]]

    else:
        raise AttributeError('Run not found')

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


def EPrimeCSVtoFSL_MID(filename, verbose=True):
    dataFrame = ReadEPrimeFile(filename)
    path, fname = os.path.split(filename)
    behave = ''

    responseDict = {'Success':'Correct', 'Failure':'pressed'}

    for run in range(0,2):
        if verbose:
            print('Processing run {0}'.format(run))
    
        subFrame, startTime = GetRun(dataFrame, run, verbose)
        
        for trialType in sorted({'WinBig', 'WinSmall', 'Neutral', 'LoseSmall', 'LoseBig'}):
            label = subFrame['Cue'].str.contains(trialType, na=False)
            indices = subFrame.index[label]
            trialTime = (subFrame.loc[indices, 'Cue.OnsetTime'] - startTime)*0.001
            #trialDuration = (subFrame.loc[indices, 'Cue.Duration']
            #               + subFrame.loc[indices, 'Anticipation.Duration']
            #               + subFrame.loc[indices, 'Probe.Duration'])*0.001
            trialDuration = 0.0

            if verbose:
                print('{0:20} {1} {2} trials'.format(trialType, run+1, len(trialTime)))
        
            FSLoutput = pd.DataFrame(trialTime)
            FSLoutput['duration']=trialDuration
            FSLoutput['value']=1.0

            FSLoutput.to_csv(os.path.join(path,'{0}-Antic-{1}.txt'.format(trialType, run+1)), header=False, index=False, \
                             sep='\t', float_format='%.3f')

            for response in sorted(responseDict):
                label2 = subFrame['ResponseCheck'].str.contains(responseDict[response], na=False)
                responseIndices = subFrame.index[label2].intersection(indices)
                trialTime = (subFrame.loc[responseIndices, 'Feedback.OnsetTime'] - startTime)*0.001

                if verbose:
                    print('{0:10}{1:10} {2} {3} trials'.format(trialType, response, run+1, len(trialTime)))
                behave = behave + '{0},'.format(len(trialTime))
   
                if len(responseIndices)>0:
                    FSLoutput = pd.DataFrame(trialTime)
                    #FSLoutput['duration']=subFrame.loc[indices, 'Feedback.Duration']*0.001
                    FSLoutput['duration'] = 0.0
                    FSLoutput['value']=1.0

                    FSLoutput.to_csv(os.path.join(path,'{0}-{1}-{2}.txt'.format(trialType, response, run+1)), \
                                     header=False, index=False, sep='\t', float_format='%.3f')

    return behave

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: {0} <E-Prime .CSV file>".format(sys.argv[0]))
        sys.exit(1)

    EPrimeCSVtoFSL_MID(sys.argv[1])
