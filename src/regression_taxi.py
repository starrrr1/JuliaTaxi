# -*- coding: utf-8 -*-

import os
import time
import numpy as np
import pandas
from keras.models import Sequential
from keras.layers import Dense, Dropout, BatchNormalization, Activation, Input, MaxoutDense
from keras.optimizers import Adam, RMSprop
from keras.regularizers import l2
from keras.constraints import maxnorm
from keras.models import Model
from keras.wrappers.scikit_learn import KerasRegressor
from sklearn.model_selection import KFold
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler

data_path = '../data'
time_format = '%Y-%m-%d_%X'

# fix random seed for reproducibility
seed = 7
np.random.seed(seed)
adam = Adam(lr=0.0001)


def load_dataset():
    train_dataframe = pandas.read_csv(os.path.join(data_path, 'train.dat'), header=None)
    test_dataframe = pandas.read_csv(os.path.join(data_path, 'test.dat'), header=None)
    train_dataset = train_dataframe.values.astype('float32')
    test_dataset = test_dataframe.values.astype('float32')
    return train_dataset, test_dataset


def load_samples():
    samples_dataframe = pandas.read_csv(os.path.join(data_path, 'train_sample.dat'), header=None)
    samples_dataset = samples_dataframe.values
    return samples_dataset


def maxout_model():
    model = Sequential()
    model.add(MaxoutDense(128, nb_feature=10, input_dim=22))
    model.add(MaxoutDense(64, nb_feature=10))
    model.add(MaxoutDense(32, nb_feature=10))

    model.add(Dense(1, init='zero'))

    model.compile(loss='mape', optimizer='adam')
    return model


# def ae():
#     encoding_dim = 5
#     input_seq = Input(shape=(22,))
#     encoded = Dense(encoding_dim, activation='relu')(input_seq)
#     decoded = Dense(22, activation='sigmoid')(encoded)
#     autoencoder = Model(input=input_seq, output=decoded)
#
#     encoder = Model(input=input_seq, output=encoded)
#
#     autoencoder.compile(optimizer=adam, loss='mse')
#     return autoencoder, encoder


def ae():
    encoding_dim = 16
    model = Sequential()
    model.add(Dense(encoding_dim, input_dim=22, activation='relu'))
    model.add(Dense(22, activation='sigmoid'))
    model.compile(optimizer=adam, loss='mse')
    return model


def make_submit_maxout():
    train, test = load_dataset()
    x_train = train[:, 0:22]
    y_train = train[:, 22]

    x_test = test[:, 0:22]
    x_scaler = StandardScaler()
    y_scaler = StandardScaler()
    x_train = (x_scaler.fit_transform(x_train.reshape(-1, 22)))
    y_train = (y_scaler.fit_transform(y_train.reshape(-1, 1)))
    x_test = (x_scaler.fit_transform(x_test.reshape(-1, 22)))
    proposed_model = maxout_model()
    proposed_model.fit(x_train, y_train, nb_epoch=5, batch_size=128, verbose=1)
    y_predict = y_scaler.inverse_transform(proposed_model.predict(x_test).reshape(-1, 1))

    trip_id = np.array(range(1, len(y_predict)+1))
    results = np.column_stack((trip_id, y_predict))
    timestamp = time.strftime(time_format, time.gmtime(time.time()))
    np.savetxt('rst_' + timestamp + '.csv', results, header='pathid,time', comments='', fmt='%d,%f')


def make_submit_ae_mlp():
    train, test = load_dataset()
    x_train = train[:, 0:22]
    y_train = train[:, 22]

    x_test = test[:, 0:22]
    x_scaler = MinMaxScaler(feature_range=(0, 1))
    y_scaler = MinMaxScaler(feature_range=(0, 1))
    x_train = (x_scaler.fit_transform(x_train.reshape(-1, 22)))
    y_train = (y_scaler.fit_transform(y_train.reshape(-1, 1)))
    x_test = (x_scaler.fit_transform(x_test.reshape(-1, 22)))

    autoencoder = ae()
    autoencoder.fit(x_train, x_train, batch_size=256, nb_epoch=5)
    encoder = autoencoder.layers[0]
    encoder.build = lambda: None
    model = Sequential()
    model.add(encoder)
    model.add(Dense(512, init='glorot_normal', activation='relu'))
    model.add(Dense(256, init='glorot_normal', activation='relu'))
    model.add(Dense(128, init='glorot_normal', activation='relu'))
    model.add(Dense(64, init='glorot_normal', activation='relu'))
    model.add(Dense(32, init='glorot_normal', activation='relu'))
    model.add(Dense(1, init='zero', activation='linear'))

    model.compile(optimizer='adam', loss='mape')
    model.fit(x_train, y_train, nb_epoch=5, batch_size=128, verbose=1)
    y_predict = y_scaler.inverse_transform(model.predict(x_test).reshape(-1, 1))

    trip_id = np.array(range(1, len(y_predict)+1))
    results = np.column_stack((trip_id, y_predict))
    timestamp = time.strftime(time_format, time.gmtime(time.time()))
    np.savetxt('rst_' + timestamp + '.csv', results, header='pathid,time', comments='', fmt='%d,%f')


def model_evaluation():
    samples = load_samples()
    x_samples = samples[:, 0:22]
    y_samples = samples[:, 22]
    proposed_model = model_wrapper()
    x_train, x_test, y_train, y_test = train_test_split(x_samples, y_samples, test_size=0.1, random_state=seed)
    proposed_model.fit(x_train, y_train)
    score = proposed_model.score(x_test, y_test)
    print '\n'
    print ('Standardized: %.4f MAPE' % score)
    print '\n'


if __name__ == '__main__':
    # model_evaluation()
    make_submit_maxout()
    # make_submit_ae_mlp()
