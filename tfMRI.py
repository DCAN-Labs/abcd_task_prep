#!/usr/bin/env python

import os, sys
import ABCD_tfMRI as ABCD
import shutil


#FEATfolder = '/users/r/w/rwatts1/bin/FEAT'
#FEATfolder = os.environ["FEATfolder"]
FEATfolder = '/home/exacloud/lustre1/fnl_lab/code/internal/pipelines/HCP_generic_srun/ABCD_tfMRI/FEAT'

verbose = False

def checkEV(filename, fsfname, EV, verbose=True):
    if os.path.isfile(filename)==False:
        if verbose:
            print('Warning: No {0}'.format(filename))

        if os.path.isfile(fsfname)==False:
            print('Warning: Cannot find {0}'.format(fsfname))
        else:
            command = "sed -i -e 's/fmri(shape{0}) 3/fmri(shape{0}) 10/' {1}".format(EV, fsfname)
            if verbose:
                print(command)
            os.system(command)

try:
    filename = sys.argv[1]
except IndexError:
    print("Usage: {0} studyFolder eprimeFolder subject session".format(sys.argv[0]))
    sys.exit(1)


nGoodSST = 0
nBadSST = 0
nMissingSST = 0

studyFolder = sys.argv[1]
print("study folder is:")
print(studyFolder)
eprimeFolder = sys.argv[2]
print("eprime folder is:")
print(eprimeFolder)
subject = 'sub-' + sys.argv[3]
print("subject ID is:")
print(subject)
session = 'ses-' + sys.argv[4]
print("session is:")
print(session)
scanner = sys.argv[5]
software_version = sys.argv[6]
print('scanner make:')
print(scanner)
print('software for GE scanner:')
print(software_version)


# Make an EVs folder and copy the Prime files into it
EVfolder = studyFolder + '/MNINonLinear/Results/EVs'
if not os.path.exists(EVfolder):
    os.makedirs(EVfolder)

# string from task folder to filtered movement regressors
MR_path = '/DCANBOLDProc_v4.0.0/DCANBOLDProc_v4.0.0_bs18.582_25.7263_filtered_Movement_Regressors.txt'


# Process SST
sst1Folder = studyFolder + '/MNINonLinear/Results/task-SST01'
sst2Folder = studyFolder + '/MNINonLinear/Results/task-SST02'
sst1MR = sst1Folder + MR_path 
sst2MR = sst2Folder + MR_path
#sstEPrime = studyFolder + '/' + subject + '/unprocessed/EPRIME/' + subject + '_tfMRI_SST1.txt'
sstEPrime = eprimeFolder + '/' + subject + '/' + session + '/func/' + subject + '_' + session + '_task-SST_run-01_bold_EventRelatedInformation.txt'


good = True
for file in {sst1MR, sst2MR, sstEPrime}:
    if os.path.isfile(file)==False:
        print('No file '+file)
        good = False

if good:
    try:
        # Create censor file for each run
        propCensor1 = ABCD.createCensorFile(sst1MR, scanner, software_version)
        propCensor2 = ABCD.createCensorFile(sst2MR, scanner, software_version)

        # Create EVs
        shutil.copy(sstEPrime, EVfolder+'/')

        behave = ABCD.EPrimeCSVtoFSL_SST(EVfolder+'/' + subject + '_' + session +  '_task-SST_run-01_bold_EventRelatedInformation.txt', 
                                         scanner, software_version, verbose=verbose)


        header = ('subject,task,censor1,censor2,' +
                  'nCorrectStop1,nIncorrectStop1,nStopTooEarly1,nCorrectGo1,nIncorrectGo1,' +
                  'nLateCorrectGo1,nLateIncorrectGo1,nNoGoResponse1,' +
                  'RTCorrectGo1,SSDCorrect1,SSDIncorrect1,' +
                  'nCorrectStop2,nIncorrectStop2,nStopTooEarly2,nCorrectGo2,nIncorrectGo2,' +
                  'nLateCorrectGo2,nLateIncorrectGo2,nNoGoResponse2,' +
                  'RTCorrectGo2,SSDCorrect2,SSDIncorrect2,WrongButton,')

        if os.path.exists('log-sst.csv')==False:
            with open('log-sst.csv', 'w') as out:
                out.write(header+'\n')

        with open('log-sst.csv', 'a') as out:
            out.write('{0},sst,{1:.3f},{2:.3f},{3}\n'.format(subject,propCensor1, propCensor2, behave))


        # Copy template model file, modify if necessary
        if scanner in ['Siemens', 'Philips'] or software_version == 'DV26':
            shutil.copy(FEATfolder+'/siemens/task-SST01_hp200_s4_level1.fsf', sst1Folder)
            shutil.copy(FEATfolder+'/siemens/task-SST02_hp200_s4_level1.fsf', sst2Folder)
        elif scanner == 'GE':
            shutil.copy(FEATfolder+'/GE/task-SST01_hp200_s4_level1.fsf', sst1Folder)
            shutil.copy(FEATfolder+'/GE/task-SST02_hp200_s4_level1.fsf', sst2Folder)
        else:
            print('Scanner not identified!')
            sys.exit(1)


        # Remove EVs with no events
        sstEV = {'IncorrectGo':3, 'LateCorrectGo':4, 'LateIncorrectGo':5, 'NoGoResponse':6, 'StopTooEarly':7}
        for run in {1,2}:
            for event in sstEV:
                EVfile = '{0}/{1}-{2}.txt'.format(EVfolder,event,run)
                fsf = studyFolder + '/MNINonLinear/Results/task-SST0{0}/task-SST0{0}_hp200_s4_level1.fsf'.format(run)
                checkEV(EVfile, fsf, sstEV[event], verbose=verbose)

        # Create folder for second level analysis and copy the template model file
        if os.path.exists(studyFolder + '/MNINonLinear/Results/task-SST')==False:
            os.makedirs(studyFolder + '/MNINonLinear/Results/task-SST')
        shutil.copy(FEATfolder+'/task-SST_hp200_s4_level2.fsf', studyFolder + '/MNINonLinear/Results/task-SST')
        nGoodSST += 1

    except IOError:
        print('********** IOError raised by SST on {0}'.format(subject))
        nBadSST += 1

    except KeyError:
        print('********** KeyError raised by SST on {0}'.format(subject))
        nBadSST += 1

    except ValueError:
        print('********** ValueError raised by SST on {0}'.format(subject))
        nBadSST +=1

    except AttributeError:
        print('********** AttributeError raised by SST on {0}'.format(subject))
        nBadSST +=1

else:
    nMissingSST += 1

# Process MID
mid1Folder = studyFolder + '/MNINonLinear/Results/task-MID01'
mid2Folder = studyFolder + '/MNINonLinear/Results/task-MID02'
mid1MR = mid1Folder + MR_path
mid2MR = mid2Folder + MR_path
#midEPrime = studyFolder + '/' + subject + '/unprocessed/EPRIME/' + subject + '_tfMRI_MID1.txt'
midEPrime = eprimeFolder + '/' + subject + '/' + session + '/func/' + subject + '_' + session + '_task-MID_run-01_bold_EventRelatedInformation.txt'

good = True
for file in {mid1MR, mid2MR, midEPrime}:
    if os.path.isfile(file)==False:
        print('No file '+file)
        good = False

if good:
    try:
        # Create censor file for each run
        propCensor1 = ABCD.createCensorFile(mid1MR, scanner, software_version)
        propCensor2 = ABCD.createCensorFile(mid2MR, scanner, software_version)

        shutil.copy(midEPrime, EVfolder)

        # Create EVs
        behave = ABCD.EPrimeCSVtoFSL_MID(EVfolder+'/' + subject + '_' + session + '_task-MID_run-01_bold_EventRelatedInformation.txt',  
                                         scanner, software_version, verbose=verbose)

        header = ('subject,task,censor1,censor2,' +
                  'WinBig-Success-1,WinBig-Failure-1,' +
                  'WinSmall-Success-1,WinSmall-Failure-1,' +
                  'Neutral-Success-1,Neutral-Failure-1,' +
                  'LoseSmall-Success-1,LoseSmall-Failure-1,' +
                  'LoseBig-Success-1,LoseBig-Failure-1,' +
                  'WinBig-Success-2,WinBig-Failure-2,' +
                  'WinSmall-Success-2,WinSmall-Failure-2,' +
                  'Neutral-Success-2,Neutral-Failure-2,' +
                  'LoseSmall-Success-2,LoseSmall-Failure-2,' +
                  'LoseBig-Success-2,LoseBig-Failure-2,')

        if os.path.exists('log-mid.csv')==False:
            with open("log-mid.csv", "w") as out:
                out.write(header+'\n')

        with open("log-mid.csv", "a") as out:
            out.write('{0},mid,{1:.3f},{2:.3f},{3}\n'.format(subject,propCensor1, propCensor2, behave))


        # Copy template model file
        if scanner in ['Siemens', 'Philips'] or software_version == 'DV26':
            shutil.copy(FEATfolder+'/siemens/task-MID01_hp200_s4_level1.fsf', mid1Folder)
            shutil.copy(FEATfolder+'/siemens/task-MID02_hp200_s4_level1.fsf', mid2Folder)
        elif scanner == 'GE':
            shutil.copy(FEATfolder+'/GE/task-MID01_hp200_s4_level1.fsf', mid1Folder)
            shutil.copy(FEATfolder+'/GE/task-MID02_hp200_s4_level1.fsf', mid2Folder)
        else:
            print('Scanner not identified!')
            sys.exit(1)

        # Create folder for second level analysis and copy the template model file
        if os.path.exists(studyFolder + '/MNINonLinear/Results/task-MID')==False:
            os.makedirs(studyFolder + '/MNINonLinear/Results/task-MID')
        shutil.copy(FEATfolder+'/task-MID_hp200_s4_level2.fsf', studyFolder + '/MNINonLinear/Results/task-MID')


    except IOError:
        print('********** IOError raised by MID on {0}'.format(subject))

    except KeyError:
        print('********** KeyError raised by MID on {0}'.format(subject))

    except ValueError:
        print('********** ValueError raised by MID on {0}'.format(subject))

    except AttributeError:
        print('********** AttributeError raised by MID on {0}'.format(subject))

# Process nBack
nBack1Folder = studyFolder + '/MNINonLinear/Results/task-nback01'
nBack2Folder = studyFolder + '/MNINonLinear/Results/task-nback02'
nBack1MR = nBack1Folder + MR_path
nBack2MR = nBack2Folder + MR_path
#nBackEPrime = studyFolder + '/' + subject + '/unprocessed/EPRIME/' + subject + '_tfMRI_nBack1.txt'
nBackEPrime = eprimeFolder + '/' + subject + '/' + session + '/func/' + subject + '_' + session + '_task-nback_run-01_bold_EventRelatedInformation.txt'

good = True
for file in {nBack1MR, nBack2MR, nBackEPrime}:
    if os.path.isfile(file)==False:
        print('No file '+file)
        good = False

if good:
    try:
        # Create censor file for each run
        propCensor1 = ABCD.createCensorFile(nBack1MR, scanner, software_version)
        propCensor2 = ABCD.createCensorFile(nBack2MR, scanner, software_version)

        shutil.copy(nBackEPrime, EVfolder)

        # Create EVs
        behave = ABCD.EPrimeCSVtoFSL_nBack(EVfolder+'/' + subject + '_' + session + '_task-nback_run-01_bold_EventRelatedInformation.txt',  
                                           scanner, software_version, verbose=verbose)

        header = ('subject,task,censor1,censor2,' +
                  '0-Back-Acc-1,0-Back-RT-1,2-Back-Acc-1,2-Back-RT-1,' +
                  '0-Back-Acc-2,0-Back-RT-2,2-Back-Acc-2,2-Back-RT-2,')

        if os.path.exists('log-nback.csv')==False:
            with open("log-nback.csv", "a") as out:
                out.write(header+'\n')
        with open("log-nback.csv", "a") as out:
            out.write('{0},nback,{1:.3f},{2:.3f},{3}\n'.format(subject,propCensor1, propCensor2, behave))


        # Copy template model file
        if scanner in ['Siemens', 'Philips'] or software_version == 'DV26':
            shutil.copy(FEATfolder+'/siemens/task-nback01_hp200_s4_level1.fsf', nBack1Folder)
            shutil.copy(FEATfolder+'/siemens/task-nback02_hp200_s4_level1.fsf', nBack2Folder)
        elif scanner == 'GE':
            shutil.copy(FEATfolder+'/GE/task-nback01_hp200_s4_level1.fsf', nBack1Folder)
            shutil.copy(FEATfolder+'/GE/task-nback02_hp200_s4_level1.fsf', nBack2Folder)
        else:
            print('Scanner version not identified!')
            sys.exit(1)



        # Create folder for second level analysis and copy the template model file
        if os.path.exists(studyFolder + '/MNINonLinear/Results/task-nback')==False:
            os.makedirs(studyFolder + '/MNINonLinear/Results/task-nback')
        shutil.copy(FEATfolder+'/task-nback_hp200_s4_level2.fsf', studyFolder + '/MNINonLinear/Results/task-nback')



    except IOError:
        print('********** IOError raised by nback on {0}'.format(subject))

    except KeyError:
        print('********** KeyError raised by nback on {0}'.format(subject))

    except ValueError:
        print('********** ValueError raised by nback on {0}'.format(subject))

    except AttributeError:
        print('********** AttributeError raised by nback on {0}'.format(subject))


print('SST Good {0}, Missing {1}, Bad {2}'.format(nGoodSST, nMissingSST, nBadSST))
