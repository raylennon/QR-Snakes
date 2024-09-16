import time
import threading
import platform
# okay...
debug = (platform.platform()[0:7]=="Windows")
if debug:
    from RGBMatrixEmulator import RGBMatrix, RGBMatrixOptions
else:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions

from PIL import Image, ImageDraw
import flask
from flask import Flask, render_template, Response, request, redirect, url_for

import createqrcode
import numpy as np

curdir='left'
bits = np.array([[32, 16], [33, 16]])
grow = False
global matrix

global mostrecent

if not debug:
    options = RGBMatrixOptions()
    options.rows = 64
    options.cols = 64
    options.chain_length = 1
    options.parallel = 1
    options.gpio_slowdown = 2
    options.brightness=10
    options.hardware_mapping = 'adafruit-hat'
    options.daemon = False
    options.drop_privileges = False
    matrix = RGBMatrix(options = options)
else:
    resizefac=12
    options = RGBMatrixOptions()
    options.rows = 32
    options.cols = 64
    options.chain_length = 1
    options.brightness = 100
    matrix = RGBMatrix(options = options)

    double_buffer = matrix.CreateFrameCanvas()
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

app = flask.Flask(__name__,
                static_url_path='',
                static_folder='../Web Interface/static',
                template_folder='../Web Interface/templates')

validmoves = ['left','right','up','down']

global apple
apple = np.random.randint([0, 0],[63, 31], (2))

splash = True

@app.route("/")
def root():
    global splash
    splash = False
    return flask.render_template("index.html")

@app.route('/<cmd>')
def command(cmd=None):
    global mostrecent
    global curdir
    global bits
    r = cmd.lower()
    if (r in ['left', 'right', 'up', 'down']):
        if (r in ['left', 'right'] and (not bits[-1,1]==bits[-2,1])) or  \
           (r in ['up', 'down'] and (not bits[-1,0]==bits[-2,0])):
            curdir = cmd.lower()
    mostrecent.cancel()
    mostrecent = threading.Timer(30, command, ['esc'])
    mostrecent.start()
    if r == 'esc':
        global splash
        splash = True
        curdir='left'
        bits = np.array([[32, 16], [33, 16]])
        grow = False
        matrix.SetImage(createqrcode.make())
    return r

def getspl():
    global splash
    return splash


def update():
    global curdir
    global apple
    global bits
    global grow
    while True:
        spl = getspl()
        time.sleep(0.1)
        if not splash:

            if curdir=='left': tform = np.array([-1,0])
            elif curdir=='right': tform = np.array([1,0])
            elif curdir=='up': tform = np.array([0,-1])
            elif curdir=='down': tform = np.array([0,1])
            if not grow:
                bits[:-1,:] = bits[1:,:]
                bits[-1,:] = bits[-2,:]+tform
            else:
                newbits = np.empty((bits.shape[0]+1, bits.shape[1]))
                newbits[:-1,:] = bits
                newbits[-1,:] = bits[-1,:]+tform
                print(newbits)
                bits = newbits.astype(int)
                grow = False

            if not len(np.unique(bits, axis=0)) == len(bits):
                curdir='left'
                bits = np.array([[32, 16], [33, 16]])            

            bits[:,0] = np.mod(bits[:,0],64*np.ones(len(bits))) # periodic boundary
            bits[:,1] = np.mod(bits[:,1],32*np.ones(len(bits)))

            if np.array_equal(bits[-1,:],apple):
                apple = np.random.randint([0, 0],[63, 31], (2))
                grow = True

            frame = np.zeros((64, 32,3)).astype(np.uint8)
            frame[bits[:,0],bits[:,1], 1:-1]+=150 # draws the snake
            frame[apple[0],apple[1], 0]+=200

            matrix.SetImage(Image.fromarray(np.transpose(frame, axes=[1,0,2])).convert('RGB'))
    return

gameloop = threading.Thread(target=update)
gameloop.start()

mostrecent = threading.Timer(30, command, ['esc'])

matrix.SetImage(createqrcode.make())

if __name__ == "__main__":

    t = threading.Thread(target=app.run, kwargs={"host":"0.0.0.0", 'port':80, 'debug':True, 'threaded':True, 'use_reloader':False})
    t.start()