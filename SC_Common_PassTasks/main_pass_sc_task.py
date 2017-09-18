#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import sys
    import traceback
    from datetime import datetime
    import pass_task_classes
    from Bus.bus import Bus
    from Bus.metaData import *

    skufReq = pass_task_classes.Request()
    skufReq.inc_num, skufReq.ext_id = sys.argv[1], sys.argv[2]
    skufReq.get_request_info()
    if skufReq.New:
        skufReq.form_request()
        skufReq.send_request()
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_PassTasks"))
