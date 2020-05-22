#!/usr/bin/env python
# coding: utf-8
#this file is used for load and save data
# In[1]:
''' USE FOR DISPLACEMENT '''

import os
import numpy as np
import pickle
import joblib
import h5py
from scipy import signal, interpolate
import pylab
# from mpl_toolkits.mplot3d import Axes3D


# ??
def save_dict_to_hdf5(dic, filename):
    '''
    save a dictionary into an hdf5 file
    args:
    oefghlf
    '''
    with h5py.File(filename, 'w') as h5file:  # fixed grammer, write to 'h5file'
        recursively_save_dict_contents_to_group(h5file, '/', dic)  # defined below


def load_dict_from_hdf5(filename):
    '''
    loads an hdf5 file and creates a dictionary with it
    '''
    with h5py.File(filename, 'r') as h5file:  # read h5py file as h5file
        return recursively_load_dict_contents_from_group(h5file, '/')  # defined below


def recursively_save_dict_contents_to_group(h5file, path, dic):  # how to define the format

    # argument type checking
    if not isinstance(dic, dict):
        raise ValueError("must provide a dictionary")

    if not isinstance(path, str):
        raise ValueError("path must be a string")
    if not isinstance(h5file, h5py._hl.files.File):
        raise ValueError("must be an open h5py file")
    # isinstance(file name, format)

    # save items to the hdf5 file
    for key, item in dic.items():
        # print(key,item)
        key = str(key)
        if isinstance(item, list):
            item = np.array(item)
            # print(item)
        if not isinstance(key, str):
            raise ValueError("dict keys must be strings to save to hdf5")
        # save strings, numpy.int64, and numpy.float64 types
        if isinstance(item, (np.int64, np.float64, str, np.float, float, np.float32, int)):
            # print( 'here' )
            h5file[path + key] = item
            if not h5file[path + key][()] == item:
                raise ValueError('The data representation in the HDF5 file does not match the original dict.')
        # save numpy arrays
        elif isinstance(item, np.ndarray):
            try:
                h5file[path + key] = item
            except:
                item = np.array(item).astype('|S9')
                h5file[path + key] = item
            if not np.array_equal(h5file[path + key][()], item):
                raise ValueError('The data representation in the HDF5 file does not match the original dict.')
        # save dictionaries
        elif isinstance(item, dict):
            recursively_save_dict_contents_to_group(h5file, path + key + '/', item)
        # other types cannot be saved and will result in an error
        else:
            # print(item)
            raise ValueError('Cannot save %s type.' % type(item))


def recursively_load_dict_contents_from_group(h5file, path):
    ans = {}
    for key, item in h5file[path].items():
        if isinstance(item, h5py._hl.dataset.Dataset):
            ans[key] = item.value
        elif isinstance(item, h5py._hl.group.Group):
            ans[key] = recursively_load_dict_contents_from_group(h5file, path + key + '/')
    return ans


# In[2]:

'''
Returns max number of A(V) default= 101
s.find() To find STR in STRINGS  
set() TO delete the same element
example: 'A (V)_124'-> 124, 

'''


def n_elems(mykeys):
    indices = [s[(s.find('_') + 1):] for s in mykeys]
    return len(set(indices))


# In[3]:


def importfile(filename):
    '''10X, return  keys,x, y, z(B.MEAN IN DISPLACEMENT), C(A IN VOLTAGE), a_all( A.MEAN IN VOLTAGE)'''
    my_data = load_dict_from_hdf5(filename)
    keys = my_data.keys()  # A =voltage B =H(voltage)
    n = n_elems(keys) + 1  # index start from 0, and here it starts from 1
    # print(A(V)_1.shape)

    """
    if n_test==1:
        n=n_elems(keys)+1   #index start from 0, and here it starts from 1
    else:
        n=2
    print('n')
    """
    # ?? [:,0] ['A (V)_'+str(s)] str(s)
    # ??AV, BV
    ''' With for in sentence n=75
    A: first dimension =part of 6000 points, SECOND DIMENSION =NUMBER OF SEGMENTS, DEFAULT 32
    ?
    C: USE A(V)[:,0] TO FIND THE MAX P-P VALUE ?:WHY NOT USE MEAN OF A[,:]
    x,y:0.4 USED TO COMPENSATION THE LENS, UNIT IS um;
    '''
    C = [(np.max(my_data['A (V)_' + str(s)][:, 0]) - np.min(my_data['A (V)_' + str(s)][:, 0])) / np.mean(
        my_data['A (V)_' + str(s)][:, 0]) for s in range(1, n)]

    print('C = ', np.argmax(C))  # index of point with max value
    y = np.array([my_data['y_' + str(s)] * 1e6 for s in range(1, n)])
    x = np.array([my_data['x_' + str(s)] * 1e6 for s in range(1, n)])
    # B_at_max_contrast = [np.mean(my_data['B (V)_'+str(np.argmax(C)+1)],axis =1)]
    # t_max = np.argmax(B_at_max_contrast)
    # test=my_data['A(V)_0']
    z_all = []
    a_all = []

    # test_BV =np.array(my_data['B (V)_'+str(50)])
    # test_AV =np.array(my_data['A (V)_'+str(50)])
    # print('BV',test_BV.shape,'AV',test_AV.shape)

    for s in range(1, n):
        # z_all.append(0.5*633e-9*np.mean(my_data['B (V)_'+str(s)],axis=1)) #speed in m/s #mean:multi metering #mean in 32 times
        z_all.append(np.mean(my_data['B (V)_' + str(s)], axis=1))
        a_all.append(np.mean(my_data['A (V)_' + str(s)], axis=1))
    z_all = np.array(z_all)
    a_all = np.array(a_all)
    # print('Z_ALL',n,z_all.shape,'A',a_all.shape)
    # z = z_all[:,t_max]
    # print(z.shape)
    z = z_all

    # print('type')#make sure the right type is loaded
    return keys, x, y, z, C, a_all


def load_data_from_files(filenames):
    ''''
    imports the data from a series of filenames
    args:
        filenames: a list of files (str)
    returns:
        x: spatial position of the points (which units?)
        y:
        z: average of channel B over all the segments
        a: average of channel A over all the segments
    '''
    x, y, z, C, a = [], [], [], [], []
    for filename in filenames:
        keys, xi, yi, zi, Ci, ai = importfile(filename)  # str paste
        x.append(xi)
        y.append(yi)
        z.append(zi)
        C.append(Ci)
        a.append(ai)

        print('len keys', len(keys))
        print('len xi', len(xi))
        print('len yi', len(yi))
        print('len zi', len(zi), np.array(zi).shape)

    return x, y, z, C, a


def import_compressed_data(filename):
    '''
    imports compressed file
    args: compressed file path
    return : compressed data(average value of each segment)
    '''

    # filenames = os.listdir(folder_name)
    # filenames = [ filename for filename in filenames if filename.endswith('.pkl') ]

    print("reading file...", filename)
    # with open(filename, 'rb+') as f:
    #     data = joblib.load(f)
    #     return data
    data = load_dict_from_hdf5(filename)
    return data
