#!/home/exacloud/lustre1/fnl_lab/code/external/utilities/anaconda2/bin/python

import os, sys
import ABCD_tfMRI as ABCD
import shutil

#FEATfolder = '/users/r/w/rwatts1/bin/FEAT'
FEATfolder = os.environ("FEATfolder")
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
    print("Usage: {0} studyFolder subject1 <subject2> <subject3>".format(sys.argv[0]))
    sys.exit(1)


nGoodSST = 0
nBadSST = 0
nMissingSST = 0

studyFolder = sys.argv[1]


for subject in sys.argv[2:]:

    # Make an EVs folder and copy the Prime files into it
    EVfolder = studyFolder + '/' + subject+'/MNINonLinear/Results/EVs'
    if not os.path.exists(EVfolder):
        os.makedirs(EVfolder)


    # Process SST
    sst1Folder = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_SST1'
    sst2Folder = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_SST2'
    sst1MR = sst1Folder+'/Movement_Regressors_FNL_preproc_v2.txt'
    sst2MR = sst2Folder+'/Movement_Regressors_FNL_preproc_v2.txt'
    sstEPrime = studyFolder + '/' + subject+'/unprocessed/EPRIME/'+subject+'_tfMRI_SST1.txt'


    good = True
    for file in {sst1MR, sst2MR, sstEPrime}:
        if os.path.isfile(file)==False:
            print('No file '+file)
            good = False

    if good:
        try:
            # Create censor file for each run
            propCensor1 = ABCD.createCensorFile(sst1MR)
            propCensor2 = ABCD.createCensorFile(sst2MR)

            # Create EVs
            shutil.copy(sstEPrime, EVfolder+'/')

            behave = ABCD.EPrimeCSVtoFSL_SST(EVfolder+'/'+subject+'_tfMRI_SST1.txt', verbose=verbose)

    
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
            shutil.copy(FEATfolder+'/tfMRI_SST1_hp200_s4_level1.fsf', sst1Folder)
            shutil.copy(FEATfolder+'/tfMRI_SST2_hp200_s4_level1.fsf', sst2Folder)


            # Remove EVs with no events
            sstEV = {'IncorrectGo':3, 'LateCorrectGo':4, 'LateIncorrectGo':5, 'NoGoResponse':6, 'StopTooEarly':7}
            for run in {1,2}:
                for event in sstEV:
                    EVfile = '{0}/{1}-{2}.txt'.format(EVfolder,event,run)
                    fsf = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_SST{0}/tfMRI_SST{0}_hp200_s4_level1.fsf'.format(run)
                    checkEV(EVfile, fsf, sstEV[event], verbose=verbose)

            # Create folder for second level analysis and copy the template model file
            if os.path.exists(studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_SST')==False:
                os.makedirs(studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_SST')
            shutil.copy(FEATfolder+'/tfMRI_SST_hp200_s4_level2.fsf', studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_SST')
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
    mid1Folder = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_MID1'
    mid2Folder = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_MID2'
    mid1MR = mid1Folder+'/Movement_Regressors_FNL_preproc_v2.txt'
    mid2MR = mid2Folder+'/Movement_Regressors_FNL_preproc_v2.txt'
    midEPrime = studyFolder + '/' + subject+'/unprocessed/EPRIME/'+subject+'_tfMRI_MID1.txt'


    good = True
    for file in {mid1MR, mid2MR, midEPrime}:
        if os.path.isfile(file)==False:
            print('No file '+file)
            good = False

    if good:
        try:
            # Create censor file for each run
            propCensor1 = ABCD.createCensorFile(mid1MR)
            propCensor2 = ABCD.createCensorFile(mid2MR)

            shutil.copy(midEPrime, EVfolder)

            # Create EVs
            behave = ABCD.EPrimeCSVtoFSL_MID(EVfolder+'/'+subject+'_tfMRI_MID1.txt', verbose=verbose)

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
            shutil.copy(FEATfolder+'/tfMRI_MID1_hp200_s4_level1.fsf', mid1Folder)
            shutil.copy(FEATfolder+'/tfMRI_MID2_hp200_s4_level1.fsf', mid2Folder)


            # Create folder for second level analysis and copy the template model file
            if os.path.exists(studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_MID')==False:
                os.makedirs(studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_MID')
            shutil.copy(FEATfolder+'/tfMRI_MID_hp200_s4_level2.fsf', studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_MID')


        except IOError:
            print('********** IOError raised by MID on {0}'.format(subject))

        except KeyError:
            print('********** KeyError raised by MID on {0}'.format(subject))

	except ValueError:
            print('********** ValueError raised by MID on {0}'.format(subject))

	except AttributeError:
            print('********** AttributeError raised by MID on {0}'.format(subject))

    # Process nBack
    nBack1Folder = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_nBack1'
    nBack2Folder = studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_nBack2'
    nBack1MR = nBack1Folder+'/Movement_Regressors_FNL_preproc_v2.txt'
    nBack2MR = nBack2Folder+'/Movement_Regressors_FNL_preproc_v2.txt'
    nBackEPrime = studyFolder + '/' + subject+'/unprocessed/EPRIME/'+subject+'_tfMRI_nBack1.txt'


    good = True
    for file in {nBack1MR, nBack2MR, nBackEPrime}:
        if os.path.isfile(file)==False:
            print('No file '+file)
            good = False

    if good:
        try:
            # Create censor file for each run
            propCensor1 = ABCD.createCensorFile(nBack1MR)
            propCensor2 = ABCD.createCensorFile(nBack2MR)

            shutil.copy(nBackEPrime, EVfolder)

            # Create EVs
            behave = ABCD.EPrimeCSVtoFSL_nBack(EVfolder+'/'+subject+'_tfMRI_nBack1.txt', verbose=verbose)

            header = ('subject,task,censor1,censor2,' +
                      '0-Back-Acc-1,0-Back-RT-1,2-Back-Acc-1,2-Back-RT-1,' +
                      '0-Back-Acc-2,0-Back-RT-2,2-Back-Acc-2,2-Back-RT-2,')

            if os.path.exists('log-nback.csv')==False:
                with open("log-nback.csv", "a") as out:
                    out.write(header+'\n')
            with open("log-nback.csv", "a") as out:
                out.write('{0},nback,{1:.3f},{2:.3f},{3}\n'.format(subject,propCensor1, propCensor2, behave))


            # Copy template model file
            shutil.copy(FEATfolder+'/tfMRI_nBack1_hp200_s4_level1.fsf', nBack1Folder)
            shutil.copy(FEATfolder+'/tfMRI_nBack2_hp200_s4_level1.fsf', nBack2Folder)


            # Create folder for second level analysis and copy the template model file
            if os.path.exists(studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_nBack')==False:
                os.makedirs(studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_nBack')
            shutil.copy(FEATfolder+'/tfMRI_nBack_hp200_s4_level2.fsf', studyFolder + '/' + subject+'/MNINonLinear/Results/tfMRI_nBack')



        except IOError:
            print('********** IOError raised by nBack on {0}'.format(subject))

        except KeyError:
            print('********** KeyError raised by nBack on {0}'.format(subject))

	except ValueError:
            print('********** ValueError raised by nBack on {0}'.format(subject))

	except AttributeError:
            print('********** AttributeError raised by nBack on {0}'.format(subject))


print('SST Good {0}, Missing {1}, Bad {2}'.format(nGoodSST, nMissingSST, nBadSST))
