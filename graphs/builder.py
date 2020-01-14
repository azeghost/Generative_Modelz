import tensorflow as tf
from tensorflow.keras.models import load_model
import numpy as np
import os
import logging
from utils.reporting.logging import log_message
from utils.swe.codes import properties, Layer_CD, Activate_CD, Messages_CD, Sampling_CD
from collections.abc import Iterable

def create_layer(layer_cd, lay_dim, kernel_shape=None, addBatchNorm=True, addDropout=True, activate=None):
    assert layer_cd in properties(Layer_CD), Messages_CD.USV.format(layer_cd, 'Layers', properties(Layer_CD))
    assert activate in properties(Activate_CD), Messages_CD.USV.format(activate, 'Activatation', properties(Activate_CD))
    x = []
    if layer_cd in [Layer_CD.Conv, Layer_CD.Deconv]:
        x = [layer_cd(lay_dim, kernel_shape, padding='same')] + x
    else:
        x = [layer_cd(lay_dim)] + x

    if addBatchNorm:
        x = [tf.keras.layers.BatchNormalization()] + x

    if addDropout:
        x = [tf.keras.layers.Dropout(0.2)] + x

    if activate:
        x = [tf.keras.layers.Activation(activate)] + x

    return x

def create_sequence(lay_shapes, isConv=True, kernel_shape=3, sampling_rate=2, addBatchNorm=True, addDropout=True,
                    activate=Activate_CD.relu, last_lay=Sampling_CD.DownSampling):

    assert activate in properties(Activate_CD), Messages_CD.USV.format(activate, 'Activations', properties(Activate_CD))
    assert activate in properties(Activate_CD), Messages_CD.USV.format(activate, 'Activations', properties(Activate_CD))
    x = []
    if isConv:
        lay_cd = Layer_CD.Conv
    else:
        lay_cd = Layer_CD.Dense

    if len(lay_shapes) %2 != 0:
        lay_shapes = lay_shapes[0] + lay_shapes

    for i, lay in enumerate(lay_shapes):
        x = create_layer(lay_cd, lay, kernel_shape=kernel_shape, addBatchNorm=addBatchNorm, addDropout=addDropout, activate=activate) + x

        if isConv:
            if i%2 == 0:
                x = [Sampling_CD.DownSampling((sampling_rate, sampling_rate), padding='same')] + x
            else:
                x = [Sampling_CD.UpSampling((sampling_rate, sampling_rate))] + x

    x = create_layer(lay_cd, lay, kernel_shape=kernel_shape, addBatchNorm=addBatchNorm, addDropout=addDropout, activate=activate) + x
    if last_lay == Sampling_CD.DownSampling:
        x = [Sampling_CD.DownSampling((sampling_rate, sampling_rate), padding='same')] + x
    else:
        x = [Sampling_CD.UpSampling((1, 1), padding='same')] + x

    return x

def make_variable(inputs_shape, outputs_shape, layers=[], name=None):
    if isinstance(outputs_shape, Iterable):
        outputs_shape = np.prod(outputs_shape)
    variable = \
        tf.keras.Sequential(
        name = name,
        layers=
        [
            tf.keras.layers.Input(shape=inputs_shape),
        ]
        +
            layers
        +
        [
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(outputs_shape),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(rate=0.25),
            tf.keras.layers.ActivityRegularization(l1=1e-6, l2=1e-6),
            tf.keras.layers.Activation(None, dtype='float32')
        ]

    )
    return variable

def save_models(file_name, variables):
    for name, variable in variables.items():
        variable.save(file_name + '_' + name + '.h5', overwrite=True)

def load_models(file_name, variables_names):
    log_message('Restore old models ...', logging.DEBUG)
    vars = []
    for name in variables_names:
        var = os.path.join(file_name, name+'.h5')
        variable = load_model(var)
        vars += [variable]
        log_message(variable.summary(), logging.WARN)
    return vars

def make_models(variables_params):
    vars = []
    for params in variables_params:
        var = make_variable(**params)
        log_message(var.summary(), logging.WARN)
        vars += [var]
    return vars

def run_variable(variable, param):
    return variable(*param)