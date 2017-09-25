import io, os, sys
import pandas as pd

def ReadEPrimeFile(filename):
    # Check file encoding
    good = False
    for testEncoding in sorted({'utf-8', 'utf-16'}):
        try:
            if 'Subject' in io.open(filename, encoding=testEncoding).read():
                encoding = testEncoding
                good = True
                break
        except UnicodeError, UnicodeDecodeError:
            pass

    if good==False:
        raise IOError('No valid encoding found')

    # Check the number of header lines
    headerLines = 0
    good = False
    for line in io.open(filename, encoding=encoding).readlines():
        if 'Subject' in line:
            for testDelimiter in {',', '\t'}:
                if line.count(testDelimiter)>0:
                    delimiter = testDelimiter
                    good = True
            break;
        else:
            headerLines += 1

    if good==False:
        raise IOError('No valid delimiter found')

    #print('{0} encoding, {1} header lines'.format(encoding, headerLines))

    dataFrame = pd.read_csv(filename, header=headerLines, sep=delimiter, encoding=encoding)

    #print(dataFrame)

    try:
        path, subject = os.path.split(filename)
        print('{0} {1}-{2} {3} {4} encoding, {5} header lines'.format(subject,
              dataFrame['SessionDate'][0],dataFrame['SessionTime'][0], dataFrame['NARGUID'][0],
              encoding, headerLines))
    except KeyError:
        print('Major problem with {0}'.format(filename))
        raise IOError('Major problem')

    return dataFrame