#!/usr/bin/python
import numpy as np
import pandas as pd
import sys, io, os
from readEPrime import ReadEPrimeFile

def EPrimeCSVtoFSL_MID(filename, verbose=True):
    dataFrame = ReadEPrimeFile(filename)
    path, fname = os.path.split(filename)
    behave = ''

    responseDict = {'Success':'Correct', 'Failure':'pressed'}

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

        for trialType in sorted({'WinBig', 'WinSmall', 'Neutral', 'LoseSmall', 'LoseBig'}):
            label = subFrame['Cue'].str.contains(trialType, na=False)
            indices = subFrame.index[label]
            trialTime = (subFrame.loc[indices, 'Cue.OnsetTime'] - startTime)*0.001
            trialDuration = (subFrame.loc[indices, 'Cue.Duration']
                           + subFrame.loc[indices, 'Anticipation.Duration']
                           + subFrame.loc[indices, 'Probe.Duration'])*0.001

            if verbose:
                print('{0:20} {1} {2} trials'.format(trialType, run+1, len(trialTime)))
        
            FSLoutput = pd.DataFrame(trialTime)
            FSLoutput['duration']=trialDuration
            FSLoutput['value']=1.0

            FSLoutput.to_csv(path+'/{0}-Antic-{1}.txt'.format(trialType, run+1), header=False, index=False, \
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
                    FSLoutput['duration']=subFrame.loc[indices, 'Feedback.Duration']*0.001
                    FSLoutput['value']=1.0

                    FSLoutput.to_csv(path+'/{0}-{1}-{2}.txt'.format(trialType, response, run+1), \
                                     header=False, index=False, sep='\t', float_format='%.3f')

    return behave

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: {0} <E-Prime .CSV file>".format(sys.argv[0]))
        sys.exit(1)

    EPrimeCSVtoFSL_MID(sys.argv[1])
