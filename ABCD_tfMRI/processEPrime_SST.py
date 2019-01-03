#!/usr/bin/env python

import numpy as np
import pandas as pd
import sys, io, os
from readEPrime import ReadEPrimeFile


# Extract a single run from a data frame
def GetRun(dataFrame, run, scanner, software_version="NONE", verbose=True):

    indexC = dataFrame['Procedure[SubTrial]'].str.contains('WaitScreen', na=False)
    waitIndex = dataFrame.index[indexC]

    if scanner in ['Siemens', 'Philips']:
        scannerType = "SIEMENS/PHILIPS"
        startIndices = waitIndex
        if run>len(startIndices)-1:
            raise AttributeError('Run not found')
        startTime = dataFrame['SiemensPad.OnsetTime'][startIndices[run]]

    elif scanner == 'GE':
        scannerType = "GE"
        indexC = dataFrame['Procedure[SubTrial]'].str.contains('BeginFixTrial', na=False)
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


def writeFSL(filename, run, trialTime, verbose=True):
    if verbose:
        print('{0:16}{1}\t{2} trials'.format(filename, run+1, len(trialTime))) 
    # Optional: Don't create a file if we have no events
    if len(trialTime)>0:
        FSLoutput = pd.DataFrame(trialTime)
        FSLoutput['duration']=0.0
        FSLoutput['value']=1.0

        FSLoutput.to_csv('{0}-{1}.txt'.format(filename, run+1), header=False,index=False, \
                         sep='\t', float_format='%.3f')
    

def EPrimeCSVtoFSL_SST(filename, scanner, software_version="NONE", verbose=True):
    dataFrame = ReadEPrimeFile(filename)
    path, fname = os.path.split(filename)
    behave = ''

    if ('Procedure[SubTrial]' in dataFrame)==False:
        if verbose:
            print('No column Procedure[SubTrial]')

        if 'Procedure[Trial]' in dataFrame:
            if verbose:
                print('...but found Procedure[Trial]')
            dataFrame.rename(columns={'Procedure[Trial]':'Procedure[SubTrial]'}, inplace=True)
        else:
            print('...and no Procedure[Trial] either')


    for run in range(0,2):
        if verbose:
            print('Processing run {0}'.format(run+1))

        subFrame, startTime = GetRun(dataFrame, run, scanner, software_version, verbose)
    
        # Go trials
        label = subFrame['Procedure[SubTrial]'].str.contains('GoTrial', na=False)
        indices = subFrame.index[label]


        # Check if the button box was the right way around
        label2 = (subFrame['Go.RESP'] == subFrame['Go.CRESP'])
        responseIndices = subFrame.index[label2].intersection(indices)    
        nCorrectGo = len(responseIndices)

        label2 = ~np.isnan(subFrame['Go.RESP']) & (subFrame['Go.RESP'] != subFrame['Go.CRESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        nIncorrectGo = len(responseIndices)

        if nCorrectGo<nIncorrectGo & nIncorrectGo>75:
            print('Looks like the button box was switched')
            # This doesn't work...
            #subFrame['Go.Resp'] = 3 - subFrame['Go.Resp']
            #subFrame['Fix.Resp'] = 3 - subFrame['Fix.Resp']
            wrongButton = 1
        else:
            wrongButton = 0

        # Correct go trials
        label2 = (subFrame['Go.RESP'] == subFrame['Go.CRESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'Go.OnsetTime'] - startTime)*0.001
        nCorrectGo = len(responseIndices)
        RTCorrectGo = np.mean(subFrame.loc[responseIndices, 'Go.RT'])
        writeFSL(os.path.join(path,'CorrectGo'),run,trialTime, verbose)
    
        # Incorrect go trials
        label2 = ~np.isnan(subFrame['Go.RESP']) & (subFrame['Go.RESP'] != subFrame['Go.CRESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'Go.OnsetTime'] - startTime)*0.001
        nIncorrectGo = len(responseIndices)
        writeFSL(os.path.join(path,'IncorrectGo'),run,trialTime, verbose)

        # Late correct go trials
        label2 = (subFrame['Fix.RESP'] == subFrame['Go.CRESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'Go.OnsetTime'] - startTime)*0.001
        nLateCorrectGo = len(responseIndices)
        writeFSL(os.path.join(path,'LateCorrectGo'),run,trialTime, verbose)

        # Late incorrect go trials
        label2 = ~np.isnan(subFrame['Fix.RESP']) & (subFrame['Fix.RESP'] != subFrame['Go.CRESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'Go.OnsetTime'] - startTime)*0.001
        nLateIncorrectGo = len(responseIndices)
        writeFSL(os.path.join(path,'LateIncorrectGo'),run,trialTime, verbose)

        # No response go trials
        label2 = np.isnan(subFrame['Go.RESP']) & np.isnan(subFrame['Fix.RESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'Go.OnsetTime'] - startTime)*0.001
        nNoGoResponse = len(responseIndices)
        writeFSL(os.path.join(path,'NoGoResponse'),run,trialTime, verbose)



        # Stop trials
        label = subFrame['Procedure[SubTrial]'].str.contains('VariableStopTrial', na=False)
        indices = subFrame.index[label]

        # Correct stop trials
        label2 = np.isnan(subFrame['StopSignal.RESP']) & np.isnan(subFrame['Fix.RESP']) & np.isnan(subFrame['SSD.RESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'SSD.OnsetTime'] - startTime)*0.001
        nCorrectStop = len(responseIndices)
        SSDCorrect = np.mean(subFrame.loc[responseIndices, 'SSD.OnsetToOnsetTime'])
        writeFSL(os.path.join(path,'CorrectStop'),run,trialTime, verbose)

        # Incorrect stop trials
        label2 = ~np.isnan(subFrame['StopSignal.RESP']) | ~np.isnan(subFrame['Fix.RESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'SSD.OnsetTime'] - startTime)*0.001
        nIncorrectStop = len(responseIndices)
        SSDIncorrect = np.mean(subFrame.loc[responseIndices, 'SSD.OnsetToOnsetTime'])
        writeFSL(os.path.join(path,'IncorrectStop'),run,trialTime, verbose)

        # Early stop trials
        label2 = ~np.isnan(subFrame['SSD.RESP'])
        responseIndices = subFrame.index[label2].intersection(indices)
        trialTime = (subFrame.loc[responseIndices, 'SSD.OnsetTime'] - startTime)*0.001
        nStopTooEarly = len(responseIndices)
        writeFSL(os.path.join(path,'StopTooEarly'),run,trialTime, verbose)


        behave = behave + '{0},{1},{2},{3},{4},{5},{6},{7},{8:.0f},{9:.0f},{10:.0f},'.format(
             nCorrectStop, nIncorrectStop, nStopTooEarly, nCorrectGo, nIncorrectGo, nLateCorrectGo, nLateIncorrectGo, nNoGoResponse,
             RTCorrectGo, SSDCorrect, SSDIncorrect)
    behave = behave + '{0},'.format(wrongButton)
    return behave


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Usage: {0} <E-Prime .CSV file>".format(sys.argv[0]))
        sys.exit(1)

    EPrimeCSVtoFSL_SST(sys.argv[1])

