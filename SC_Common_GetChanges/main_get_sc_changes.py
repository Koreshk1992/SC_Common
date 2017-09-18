#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import sys
    import traceback
    from datetime import datetime
    from Bus.bus import Bus
    from Bus.metaData import *
    from Bus.config import *
    from get_changes_classes import ChangeCollector

    team, user, mode = sys.argv[1], sys.argv[2], 'EXECUTOR'
    bus = Bus()
    bus.location = "SC_GetChanges_Logs"
    bus.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), bus.location)
    if team == 'employee$644104':
        mode = 'INITIATOR'
    req = bus.create_req_instance(get_tasks_sc.format(team, mode, 'true', 'false'), 'urn:GetTasksList', sc_adapter_url)
    log = bus.logger(get_tasks_sc.format(team, mode, 'true', 'false'), "REQUEST", "GetTickets", 0, team)
    bus.process = bus.write_process(log, 0, bus.process)
    response = bus.send_req(req, 60).read()
    log = bus.logger(response, "RESPONSE", "GetTickets", 0, team)
    bus.process = bus.write_process(log, 0, bus.process)
    bus.log_process(bus.process, "GetTicketsProcess for team - " + team)
    changed_incs = set(bus.get_values_by_tag_name(response, 'Tasks'))
    bus.create_db_connection()
    bus.send_database_request(g_skuf_tickets)
    skuf_incs = set([i[0] for i in bus.cursor])
    sc_incs = list((changed_incs & skuf_incs) - forbiden_tickets)
    for i, sc_inc in enumerate(sc_incs):
        cc = ChangeCollector()
        cc.event_id, cc.count, cc.team_id, cc.user = sc_inc, i, team, user
        cc.get_changed_attributes()
        cc.get_current_attributes_values()
        cc.send_changes()
        cc.log_process(cc.process, cc.event_id)
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_GetChanges"))
