#!/usr/bin/env python

import numpy as np
import sys, math, os

def createCensorFile(filename, scanner, software_version="NONE"):
    nDiscardSiemens = 8
    nDiscardGEDV25 = 5
    nDiscardGEDV26 = 16

    threshold = 0.8
    ignoreY = True
    filterFile = True

    path, fname = os.path.split(filename)
    # filename is now a directory higher than it originally was - AP 20180926
    path = os.path.dirname(path)
    #print('Creating censor file based on {0}'.format(path))

    mr = np.genfromtxt(filename)
    nTimePoints = mr.shape[0]

    # set number of frames to censor from cifti time series
    if scanner == 'GE':
        if software_version == 'DV25':
            nDiscard = nDiscardGEDV25
        elif software_version == 'DV26'
            nDiscard = nDiscardGEDV26
        else:
            print('scanner software must be provided for GE: {}'.format(software_version))
    elif scanner in ['Siemens', 'Philips']:
        nDiscard = nDiscardSiemens
    else:
        print('Scanner not identified {} GE software: {}'.format(scanner, software_version))
        sys.exit(1)


    #print(nTimePoints)
 
    if filterFile:
        tmp = np.zeros([nTimePoints, 12])
        tmp[:,0:6] = mr[:,0:6]
        tmp[1:,6:12] = mr[1:,0:6] - mr[:-1,0:6]
        mr = tmp

    #np.set_printoptions(formatter={'float': '{: 0.3f}'.format})
    #np.set_printoptions(threshold=np.inf, formatter={'float': '{: 0.3f}'.format}, linewidth=100)
    #print(mr)

 
    censorVolume = np.zeros(nTimePoints, dtype=int)
    censorVolume[0:nDiscard] = 1

    for i in range(nDiscard,nTimePoints):
        dr = mr[i,6:12]
        if ignoreY:
            fwd = abs(dr[0])              + abs(dr[2]) \
                + 50*( abs(math.radians(dr[3])) + abs(math.radians(dr[4])) + abs(math.radians(dr[5]))); 
        else:
            fwd = abs(dr[0]) + abs(dr[1]) + abs(dr[2]) \
                + 50*( abs(math.radians(dr[3])) + abs(math.radians(dr[4])) + abs(math.radians(dr[5]))); 
        if fwd>threshold:
            censorVolume[i] = 1
            censorVolume[i-1] = 1

    nCensor = np.count_nonzero(censorVolume)
    if nTimePoints>nDiscard:
        prop = float(nTimePoints-nCensor)/(nTimePoints-nDiscard)
    else:
        prop = 0.0

    #print(nCensor)
    #print('{0} {1:.3f}'.format(path, prop))

    matrix = np.zeros([nTimePoints, nCensor])

    j=0
    for i in range(0,nTimePoints):
        if censorVolume[i]==1:
            matrix[i,j] = 1
            j=j+1
    np.savetxt(path+'/censor.txt', matrix, delimiter='\t', fmt='%d')

    return prop

if __name__ == "__main__":
    createCensorFile(sys.argv[1])
