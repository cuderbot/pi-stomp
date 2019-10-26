#!/usr/bin/env python

import json
import os
import requests as req
import sys

import modalapi.controller as Controller
import modalapi.pedalboard as Pedalboard

sys.path.append('/usr/lib/python3.5/site-packages')  # TODO possibly /usr/local/modep/mod-ui
from mod.development import FakeHost as Host


class Mod:
    __single = None

    def __init__(self, lcd):
        print("Init mod")
        if Mod.__single:
            raise Mod.__single
        Mod.__single = self

        self.lcd = lcd
        self.root_uri = "http://localhost:80/"
        # TODO construct pblist, current at each call in case changes made via UI
        # unless performance sucks that way
        self.param_list = []  # TODO remove
        self.pedalboards = []
        self.controllers = {}  # Keyed by midi_channel:midi_CC
        self.current_pedalboard_index = 0
        self.current_preset_index = 0
        self.current_num_presets = 0

        self.plugin_dict = {}

        # TODO should this be here?
        #self.load_pedalboards()

        # Create dummy host for obtaining pedalboard info
        self.host = Host(None, None, self.msg_callback)


    def load_pedalboards(self):
        url = self.root_uri + "pedalboard/list"

        try:
            resp = req.get(url)
        except:  # TODO
            print("Cannot connect to mod-host.")
            sys.exit()

        if resp.status_code != 200:
            print("Cannot connect to mod-host.  Status: %s" % resp.status_code)
            sys.exit()

        self.pedalboards = json.loads(resp.text)
        for pb in self.pedalboards:
            print("Loading pedalboard info: %s" % pb['title'])
            bundle = pb['bundle']
            title = pb['title']
            pedalboard = Pedalboard.Pedalboard(bundle, title)
            pedalboard.load_bundle(bundle, self.plugin_dict)
            #print("dump: %s" % pedalboard.to_json())
        return self.pedalboards


    # TODO change these functions ripped from modep
    def get_current_pedalboard(self):
        url = self.root_uri + "pedalboard/current"
        try:
            resp = req.get(url)
            # TODO pass code define
            if resp.status_code == 200:
                return resp.text
        except:
            return None

    def get_current_pedalboard_name(self):
        pb = self.get_current_pedalboard()
        return os.path.splitext(os.path.basename(pb))[0]

    def get_current_pedalboard_index(self, pedalboards, current):
        try:
            return pedalboards.index(current)
        except:
            return None

    def get_bundlepath(self, index):
        pedalboard = self.pedalboards[index]
        if pedalboard == None:
            print("Pedalboard with index %d not found" % index)
            # TODO error handling
            return None
        return self.pedalboards[index]['bundle']

    def msg_callback(self, msg):
        print(msg)

    def pedalboard_init(self):
        # Get current pedalboard - TODO refresh when PB changes
        url = self.root_uri + "pedalboard/current"
        resp = req.get(url)
        pedalboard_name = os.path.splitext(os.path.basename(resp.text))[0]
        print("Getting Pedalboard: %s" % pedalboard_name)
        bundle = "/usr/local/modep/.pedalboards/%s.pedalboard" % pedalboard_name
        pedalboard = (next(item for item in self.pedalboards if item['bundle'] == bundle))
        self.current_pedalboard_index = self.pedalboards.index(pedalboard)
        print("  Index: %d" % self.current_pedalboard_index)


        # Preset info
        # TODO should this be here?
        plugins = []  # TODO
        bundlepath = self.get_bundlepath(self.current_pedalboard_index)
        print("bundle: %s" % bundlepath)

        self.host.load(bundlepath, False)
        #var = self.host.load_pb_presets(plugins, bundlepath)
        self.current_num_presets = len(self.host.pedalboard_presets)
        print("len: %d" % len(self.host.pedalboard_presets))
        print(self.host.plugins)

        # Plugin info



        # Pedalboard info
        # info = pb.get_pedalboard_info(resp.text)
        # param_list = list()
        # for key, param in info.items():
        #     if param != {}:
        #          p = param['instance'].capitalize() + ":" + param['parameter'].upper()
        #          print(p)
        #          param_list.append(p)
        # print(len(param_list))

        # lcd_draw_text_rows(pedalboard_name, param_list)

    def get_current_preset_name(self):
        return self.host.pedalpreset_name(self.current_preset_index)

    def preset_change(self, encoder, clk_pin):
        enc = encoder.get_data()
        index = ((self.current_preset_index - 1) if (enc == 1)
                 else (self.current_preset_index + 1)) % self.current_num_presets
        print("preset change: %d" % index)
        url = "http://localhost/pedalpreset/load?id=%d" % index
        print(url)
        # req.get("http://localhost/reset")
        resp = req.get(url)
        if resp.status_code != 200:
            print("Bad Rest request: %s status: %d" % (url, resp.status_code))
        self.current_preset_index = index

        # TODO move formatting to common place
        # TODO name varaibles so they don't have to be calculated
        text = "%s-%s" % (self.get_current_pedalboard_name(), self.get_current_preset_name())
        self.lcd.draw_text_rows(text)
