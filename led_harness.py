import os
import json
import logging
import scrollphathd
import numpy as np
#from PIL import Image
import time
from fadecandy.examples.python import opc
import atexit

def get_led_info():

    local_path = os.path.dirname(os.path.abspath(__file__))

    l_dat = json.load(open(local_path + "/mapping/led_info.json"))
    strip_hwid = json.load(open(local_path + "/mapping/led_hardware_index.json"))
    mat_hwid = json.load(open(local_path + "/mapping/led_hardware_index_eyes.json"))

    for led_id in l_dat:

        if led_id.startswith("eye"):
            l_dat[led_id]["type"] = "mat"
            x, y = np.where(np.array(mat_hwid) == led_id.replace("eye_empty.", ""))
            l_dat[led_id]["hardware_id"] = (x[0], y[0])
            l_dat[led_id]["position"] = list(l_dat[led_id]["position_actual"])
        if led_id.startswith("LED"):
            l_dat[led_id]["type"] = "strip"
            l_dat[led_id]["hardware_id"] = strip_hwid.index(led_id.replace("LED.", ""))


        if "position" not in l_dat[led_id]:
            l_dat[led_id]["position"] = l_dat[led_id]["position_actual"]

        l_dat[led_id]["colour"] = [0, 0, 0]
        #if l_dat[led_id]["type"] == "strip":
        l_dat[led_id]["position"][0] *= -1
        l_dat[led_id]["position"][1] *= -1
        l_dat[led_id]["position_actual"][0] *= -1
        l_dat[led_id]["position_actual"][1] *= -1

    return l_dat


class LedHarness:

    def __init__(self):
        self.leds = get_led_info()
        self.client = opc.Client('localhost:7890')
        self.uv_maps = ["side", "front"]  # order = bottom to top of layers
        self._brightness = .5

        self.WIDTH = 27.388
        self.HEIGHT = 25.5237
        self.DEPTH = 30.5849  # TODO add min and max values too.
        atexit.register(self.quit)

    def image_to_colours(self, image_filepath):

        img = Image.open(image_filepath)
        pixels = img.load()
        colours = {}

        for map_name in self.uv_maps:
            for led_id in self.leds:
                led = self.leds[led_id]
                if map_name in led["maps"]:
                    u, v = led["maps"][map_name]
                    x, y = int(u*img.width), int((1-v)*img.height)
                    r, g, b, a = pixels[x, y]
                    if a:  # TODO Support blending in the future.
                        colours[led_id] = [r, g, b]
                else:
                    logging.warning("can't find mapping for %s" % led_id)

        return colours

    def set_colours(self, d, render=True):  # TODO remove, Now unused
        for led_id in self.leds:
            if led_id in d:
                self.leds[led_id]["colour"] = d[led_id]
            else:
                self.leds[led_id]["colour"] = [0, 0, 0]

        if render:
            self.render()

    def render(self, instant=True):

        led_strip_buf = np.zeros((512, 3))
#        led_mat_buf = np.zeros((16, 16))
#        s1 = time.time()
        for led_id in self.leds:
            led = self.leds[led_id]
            if led["type"] == "strip":
                led_strip_buf[led["hardware_id"]] = led["colour"]
            elif led["type"] == "mat":
                y, x = led["hardware_id"]
                y = 8 - y
                #led_mat_buf[x, y] = int(np.max(led["colour"])/255.0)
                #print("here")
                v = max(led["colour"])/255.0
                scrollphathd.pixel(x, y, v)
#        s2 = time.time()
#        if np.min(led_strip_buf) < 0 or \
#                np.min(led_mat_buf) < 0 or \
#                np.min(led_strip_buf) > 255 or \
#                np.min(led_mat_buf) > 255:
#            logging.error("Warning, some pixels values are outside of expected parameters")
#            return
#       s3 = time.time()
        self.client.put_pixels(led_strip_buf)
 #       if instant:
#            self.client.put_pixels(led_strip_buf)
#        s4 = time.time()
#        scrollphathd.buf = led_mat_buf
        scrollphathd.show()
#        s5 = time.time()

#        print((s2-s1)/(s5-s1), (s3-s2)/(s5-s1), (s4-s3)/(s5-s1), (s5-s4)/(s5-s1))

    def quit(self):
        for led_id in self.leds:
            self.leds[led_id]["colour"] = np.zeros(3)
        self.render()
