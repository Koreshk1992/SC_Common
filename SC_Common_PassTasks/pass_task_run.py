#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import traceback
    import subprocess
    from datetime import datetime
    from Bus.bus import Bus
    from Bus.metaData import *

    bus = Bus()
    bus.stop_if_already_running('main_pass_sc_task.py')
    bus.create_db_connection()
    result = bus.send_database_request(g_unprocessed)
    incs = [inc for inc in result]
    bus.connection.close()
    for inc in incs:
        exec_string = os.path.join(os.path.dirname(os.path.realpath(__file__)), "main_pass_sc_task.py '{0}' '{1}'")
        process = subprocess.Popen(exec_string.format(inc[0], inc[1]), shell=True)
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_PassTasks"))
