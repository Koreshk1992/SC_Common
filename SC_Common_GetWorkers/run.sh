#!/bin/bash
export PYTHONPATH="$PYTHONPATH:/usr/local/python2.7/lib/python2.7/site-packages:/usr/local/python2.7"
cd /opt/Scripts/SC_Common/Bus/SC_Common_GetWorkers
/usr/local/bin/python2.7 get_orgs_main.py
