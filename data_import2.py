import os
import numpy as np
import data as hdf5_utils
import os.path as ospath
import scipy.interpolate as interp

def contrast(chA, time, AOM_freq = 80e6):
    '''
    comtrast data
    args:
    chA: channel A(data['A'])
    time: scanning time (= 1/fs)
    AOM_freq = 80e6
    out = np.abs(interp.interp1d(freqs,F,kind='nearest',axis=0)(AOM_freq))
    '''
    F = np.fft.fft(chA,axis=0)
    dt = np.mean(np.diff(time))
    freqs = np.fft.fftfreq(len(time),d=dt)
    C = np.abs(interp.interp1d(freqs,F,kind='nearest',axis=0)(AOM_freq))
    return C

def import_data(filename,channels,transform = None):
    '''
    imports the data from filename
    args:
    channels: a list of the channels to import (ex: ['A','C'])
    transform: the action to apply
    out = transform(data)
    '''
    x=[]
    y=[]
    allData = {'contrast':[]}
    for c in channels:
        allData[c]=[]
    batch = hdf5_utils.load_dict_from_hdf5(filename)
    time = batch['time (s)_1']
    for k,data in batch.items():
        if k[0] in channels: #data keys should read 'A (V)_1'
            if transform is None:
                out = data
            elif transform == 'mean':
                out = np.mean(data, axis=1)
                print(k[0], out.shape)
            allData[k[0]].append(out)
        elif k[0] == 'x':
            x.append(data)
        elif k[0] == 'y':
            y.append(data)
        if k[0]=='A':
            C = np.mean(contrast(data, time, AOM_freq = 80e6),axis=0)
            allData['contrast'].append(C)
    return x,y,time,allData

def import_folder(folder, channels, transform = None):
    '''
    imports folder
    args: folder path,channels
    out: array[x],array[y],time,allData
    '''
    x = []
    y = []
    allData = {'contrast': []}
    for c in channels:
        allData[c] = []

    all_files = os.listdir(folder)
    data_files = []
    for filename in all_files:
        if filename.startswith("data_"):
            data_files.append(ospath.join(folder,filename))
    data_files.sort()
    for data_file in data_files:
        print("current data file", data_file)
        xi, yi, time, datai = import_data(ospath.join(folder, data_file), channels, transform=transform)
        x.extend(xi)
        y.extend(yi)
        for k in allData.keys():
            allData[k] = allData[k] + datai[k]
            # allData['contrast'] = allData['contrast']+datai['contrast']
        print(data_file + ' was successfully imported')

    for k in allData.keys():
        allData[k] = np.array(allData[k])
    return np.array(x), np.array(y), time, allData


# def import_all(folder,channels,transform=None):
#     '''
#     imports folder
#     args: folder path,channels
#     out: array[x],array[y],time,allData
#     '''
#     i=0
#     x = []
#     y = []
#     allData = {'contrast':[]}
#     for c in channels:
#         allData[c]=[]
#     while True:
#         try:
#             filename = 'data_{0}'.format(i)
#             xi,yi,time,datai = import_data(ospath.join(folder,filename),channels,transform = transform)
#             x.extend(xi)
#             y.extend(yi)
#             for k in allData.keys():
#                 allData[k] = allData[k]+datai[k]
#                 #allData['contrast'] = allData['contrast']+datai['contrast']
#             print(filename+' was successfully imported')
#             i+=1
#         except OSError:
#             for k in allData.keys():
#                 allData[k] = np.array(allData[k])
#             return np.array(x),np.array(y),time,allData
#         except KeyError:
#             for k in allData.keys():
#                 allData[k] = np.array(allData[k])
#             return np.array(x),np.array(y),time,allData
#     for k in allData.keys():
#         allData[k] = np.array(allData[k])
#     return np.array(x),np.array(y),time,allData
