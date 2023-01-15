import time
import threading
import platform
# okay...
debug = (platform.platform()[0:7]=="Windows")
if debug:
    from cv2_debugscreen import TestScreen
else:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions

from PIL import Image
import flask
from flask import Flask, render_template, Response, request, redirect, url_for

import createqrcode
import numpy as np

import sys

global position

position = [32, 16]
curdir='left'
bits = np.array([position]*10)

global matrix

global mostrecent

if not debug:
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.gpio_slowdown = 2
    options.brightness=60
    options.hardware_mapping = 'adafruit-hat'
    options.daemon = False
    options.drop_privileges = False
    matrix = RGBMatrix(options = options)
else:
    resizefac=12
    matrix = TestScreen((64*resizefac, 32*resizefac))
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

app = flask.Flask(__name__,
                static_url_path='',
                static_folder='../Web Interface/static',
                template_folder='../Web Interface/templates')

validmoves = ['left','right','up','down']

global started
started = False

@app.route("/")
def root():
    global started
    if not started:
        pass
    started = True
    return flask.render_template("index.html")

@app.route('/<cmd>')
def command(cmd=None):
    global curdir
    response = cmd.lower()
    if (response in ['left', 'right', 'up', 'down']):
        curdir = cmd.lower()

    return response

def update():
    global bits
    while True:
        time.sleep(0.1)
        bits[:-1,:] = bits[1:,:]
        if curdir=='left': tform = np.array([-1,0])
        elif curdir=='right': tform = np.array([1,0])
        elif curdir=='up': tform = np.array([0,-1])
        elif curdir=='down': tform = np.array([0,1])

        bits[-1,:] = bits[-2,:]+tform

        bits[:,0] = np.mod(bits[:,0],64*np.ones(len(bits)))
        bits[:,1] = np.mod(bits[:,1],32*np.ones(len(bits)))

        frame = np.zeros((64, 32))
        frame[bits[:,0],bits[:,1]]+=150
        matrix.SetImage(Image.fromarray(frame.T).convert('RGB'))
    return

gameloop = threading.Thread(target=update)
gameloop.start()

matrix.SetImage(createqrcode.make())

if __name__ == "__main__":

    t = threading.Thread(target=app.run, kwargs={"host":"0.0.0.0", 'port':80, 'debug':True, 'threaded':True, 'use_reloader':False})
    t.start()


    # t.terminate()
    # t.join()

matrix.check()
