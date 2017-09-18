#!/bin/bash
export PYTHONPATH="$PYTHONPATH:/usr/local/python2.7/lib/python2.7/site-packages:/usr/local/python2.7"
cd /opt/Scripts/SC_Common/Bus/SC_Common_PassTasks
/usr/local/bin/python2.7 pass_task_run.py
cd /opt/Scripts/SC_Common/Bus/SC_Common_PassChanges
/usr/local/bin/python2.7 chunk_changes.py
