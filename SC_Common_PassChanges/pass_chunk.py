#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import sys
    import traceback
    from copy import deepcopy
    from datetime import datetime
    import pass_changes_classes
    from Bus.bus import Bus
    from Bus.metaData import *

    inc_num = sys.argv[1]
    connection, cursor = Bus.return_db_connection()
    cursor.execute(g_events_by_inc.format(inc_num))
    mass = [i[0] for i in cursor]
    connection.close()
    for inc in mass:
        skuf_change_handler = deepcopy(pass_changes_classes.ChangeSender())
        skuf_change_handler.event_id = inc
        skuf_change_handler.get_pending_event()
        skuf_change_handler.set_event_arguments()
        skuf_change_handler.determine_event_type()
        skuf_change_handler.send_event_to_sc()

except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_PassChanges"))
