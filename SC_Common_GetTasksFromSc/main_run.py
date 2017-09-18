#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
import os
import subprocess
from Bus.bus import Bus
from Bus.metaData import *

Bus.stop_if_already_running('main_get_sc_tasks.py')
for i in [3, 6, 9, 10, 11, 12, 13]:
    string = os.path.join(os.path.dirname(os.path.realpath(__file__)), "main_get_sc_tasks.py '{0}' '{1}'")
    p = subprocess.Popen(string.format(User[i].split(":")[1], i), shell=True)
