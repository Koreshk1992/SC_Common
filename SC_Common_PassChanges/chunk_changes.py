#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import traceback
    import subprocess
    from datetime import datetime
    from Bus.bus import Bus
    from Bus.metaData import *

    Bus.stop_if_already_running("pass_chunk.py")
    connection, cursor = Bus.return_db_connection()
    cursor.execute(g_chunks)
    mass = [i[0] for i in cursor]
    connection.close()
    for inc in mass:
        string = os.path.join(os.path.dirname(os.path.realpath(__file__)), "pass_chunk.py '{0}'")
        p = subprocess.Popen(string.format(inc), shell=True)
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_PassChanges"))
