#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
import os
import time
import subprocess
from Bus.bus import Bus
from Bus.metaData import *
Bus.stop_if_already_running("main_get_sc_changes.py")
while True:
    if Bus.continue_if_running("pass_chunk.py"):
        time.sleep(5)
        continue
    else:
        break
for i in [15]:  # , 6, 9, 10, 11, 12, 13, 15]:
    string = os.path.join(os.path.dirname(os.path.realpath(__file__)), "main_get_sc_changes.py '{0}' '{1}'")
    p = subprocess.Popen(string.format(User[i].split(":")[1], i), shell=True)
