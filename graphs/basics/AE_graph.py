import tensorflow as tf

from graphs.builder import make_models, load_models
from stats.losses import reconstuction_loss

LOSS_NAME= 'bce'

def make_ae(model_name, variables_params, restore=None):
    variables_names = [variables['name'] for variables in variables_params]  # ['inference',  'generative']
    variables = make_variables(variables_params=variables_params, model_name=model_name, restore=restore)

    def get_variables():
        return dict(zip(variables_names, variables))

    def loss_functions():
        return dict(zip([LOSS_NAME], [training_loss]))

    return get_variables, loss_functions

@tf.function
def training_loss(inputs, predictions):
    x_logit = predictions['x_logit']
    reconstruction_loss = reconstuction_loss(true_x=inputs, pred_x=x_logit)
    Px_xreconst = tf.reduce_mean(-reconstruction_loss)
    return Px_xreconst

def make_variables(variables_params, model_name, restore=None):
    variables_names = [variables['name'] for variables in variables_params]
    if restore is None:
        variables = make_models(variables_params)
    else:
        variables = load_models(restore, [model_name + '_' + var for var in variables_names])
    return variables

def encode(model, inputs):
    z = model('inference', [inputs])
    return z

def decode(model, latent, inputs_shape, apply_sigmoid=False):
    logits = model('generative', [latent])
    if apply_sigmoid:
        probs = tf.sigmoid(logits)
        return tf.reshape(probs, shape=[-1] + [*inputs_shape])
    return tf.reshape(logits, shape=[-1] + [*inputs_shape])

@tf.function
def generate_sample(model, inputs_shape, latent_shape, eps=None):
    if eps is None:
        eps = tf.random.normal(shape=latent_shape)
    generated = decode(model=model, latent=eps, inputs_shape=inputs_shape, apply_sigmoid=True)
    return generated

