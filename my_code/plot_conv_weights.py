import sys
from os import path
import math
import cPickle

import numpy
from PIL import Image
import scipy.misc

from my_code.predict import model_runid

import pdb

def conv_weight_image(W,b, filter_enlargement=2, filter_padding=1, filter_shape='c01b'):
    """
    Creates an image from a CONV layer's weights
    """
    # http://lasagne.readthedocs.org/en/latest/modules/layers.html?highlight=conv2dcclayer#lasagne.layers.cuda_convnet.Conv2DCCLayer
    if filter_shape == 'c01b':
        num_input_channels, filter_rows, filter_columns, num_filters = W.shape
    else:
        num_filters, num_input_channels, filter_rows, filter_columns = W.shape # bc01
    filt = [w+b_ for w, b_ in zip(W, b)]
    dim_in_filters = int(math.ceil(math.sqrt(num_filters*(num_input_channels)))) # num filters plotted per dimension
    filter_px_size = (filter_rows*filter_enlargement+filter_padding)
    dim_in_px = dim_in_filters * filter_px_size
    out_img = numpy.zeros((dim_in_px,dim_in_px))
    for n in xrange(num_filters):
        for m in xrange(num_input_channels):
            i,j = divmod((n*num_input_channels)+m, dim_in_filters)
            i_px_start = i * filter_px_size
            i_px_end = i_px_start + filter_rows*filter_enlargement
            j_px_start = j * filter_px_size
            j_px_end = j_px_start + filter_rows*filter_enlargement
            if filter_shape == 'c01b':
                img = scipy.misc.toimage(filt[m][:,:,n])
            else:
                img = scipy.misc.toimage(filt[n][m,:,:])
            nd = int(filter_rows*filter_enlargement)
            new_size = nd, nd
            img_3x = img.resize(new_size, Image.NEAREST)
            out_img[i_px_start:i_px_end, j_px_start:j_px_end] = img_3x
    return out_img

if __name__ == '__main__':
    model_file = sys.argv[1]
    if len(sys.argv) == 3:
        filter_shape = sys.argv[2]
    else:
        filter_shape = 'c01b'
    runid = model_runid(model_file)
    f = open(model_file)
    # discard first slot
    all_saves = []
    while True:
        try:
            all_saves.append(cPickle.load(f))
        except EOFError:
            break
    all_layers_flat = all_saves[-1]
    all_layers = zip(all_layers_flat[0::2], all_layers_flat[1::2])
    conv_layers = [(W,b) for W,b in all_layers if len(W.shape) == 4]

    outpaths = []
    for i,Wb in enumerate(conv_layers):
        W,b = Wb
        imgname = "%s-layer-%i-%s" % (runid, i,'x'.join(numpy.array(W.shape, dtype=str)))
        outpath = 'plots/' + imgname + '.png'
        layer_img = conv_weight_image(W,b, filter_shape=filter_shape)
        scipy.misc.toimage(layer_img).save(outpath, "PNG")
        outpaths.append(outpath)
    for outpath in outpaths:
        print("Saved image in: %s" % outpath)
