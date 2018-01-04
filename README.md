# Description

The majority of the processing is the HCP MPP scripts which themselves rely on FSL, FreeSurfer, and Connectome workbench.  Information on the installation of the HCP pipelines can be found at:

https://github.com/Washington-University/Pipelines/wiki/v3.4.0-Release-Notes,-Installation,-and-Usage

Note that the whole HCP MPP processing is slow, so make friends with those that have access to a processing cluster. The steps in the pipeline are described in:

http://www.sciencedirect.com/science/article/pii/S1053811913005053

Each subject takes roughly 2-3 days on a single core from start to finish.  The PreFreeSurfer, FreeSurfer, PostFreeSurfer, GenericfMRIVolume and GenericfMRISurface batch scripts are run with very minimal changes to match your environment and the data format.  To set up for the TaskfMRI script, you need to generate the regressors, which is where these python scripts come in.  The python scripts require the NumPy and Pandas libraries to be installed, but are otherwise standard python.

If you just want to explore ABCD preprocessed data – group-level analysis – then you just need FSL Palm and HCP Workbench. This is relatively easy.

# Usage



# Examples
