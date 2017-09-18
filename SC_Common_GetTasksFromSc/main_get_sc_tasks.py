#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import sys
    import traceback
    from datetime import datetime
    from main_classes import *
    from Bus.bus import Bus
    from Bus.config import *
    from Bus.metaData import *

    team, user = sys.argv[1], sys.argv[2]
    bus = Bus()
    bus.location = "SC_GetTickets_Logs"
    bus.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), bus.location)
    req = bus.create_req_instance(get_tasks_sc.format(team, "EXECUTOR", "false", "false"), 'urn:GetTasksList', sc_adapter_url)
    log = bus.logger(get_tasks_sc.format(team, "EXECUTOR", "false", "false"), "REQUEST", "GetTickets", 0, team)
    bus.process = bus.write_process(log, 0, bus.process)
    response = bus.send_req(req, 60).read()
    log = bus.logger(response, "RESPONSE", "GetTickets", 0, team)
    bus.process = bus.write_process(log, 0, bus.process)
    bus.log_process(bus.process, "GetTicketsProcess for team - " + team)
    sc_incs = set(bus.get_values_by_tag_name(response, 'Tasks'))
    bus.create_db_connection()
    skuf_incs = set([i[0] for i in bus.send_database_request(g_exist_tickets)])
    sc_incs = list(sc_incs - skuf_incs)
    bus.connection.close()
    for i, sc_inc in enumerate(sc_incs):
        sc_req = ScReq()
        sc_req.event_id, sc_req.count, sc_req.team_id, sc_req.user = sc_inc, i, team, user
        sc_req.get_request_attributes()
        sc_req.send_request_to_skuf()
        sc_req.connection.close()
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_GetTasksFromSc"))
