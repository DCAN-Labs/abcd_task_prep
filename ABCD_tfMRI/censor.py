#!/usr/bin/python

import numpy as np
import sys, math, os

def createCensorFile(filename):
    nDiscard = 8;
    threshold = 0.8;
    ignoreY = True;

    path, fname = os.path.split(filename)

    #print('Creating censor file based on {0}'.format(path))

    mr = np.genfromtxt(filename)

    nTimePoints = mr.shape[0]

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
    EPrimeCSVtoFSL_nBack(sys.argv[1])
