#!/bin/bash
export PYTHONPATH="$PYTHONPATH:/usr/local/python2.7/lib/python2.7/site-packages:/usr/local/python2.7"
cd /opt/Scripts/SC_Common/Bus/SC_Common_PassChanges
/usr/local/bin/python2.7 chunk_changes.py
sleep 15
cd /opt/Scripts/SC_Common/Bus/SC_Common_GetChanges
/usr/local/bin/python2.7 get_changes_run.py

