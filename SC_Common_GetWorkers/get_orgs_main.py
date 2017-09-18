#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import traceback
    from datetime import datetime
    import get_orgs_classes
    from Bus.bus import Bus
    from Bus.metaData import *

    skuf_company = get_orgs_classes.Company()
    skuf_company.create_db_connection()
    skuf_company.company_name = "SKUF"
    skuf_company.get_company_orgs()
    sc_company = get_orgs_classes.Company()
    sc_company.create_db_connection()
    sc_company.company_name = "SC"
    sc_company.get_company_orgs()
    manager = get_orgs_classes.CompanyManager()
    manager.create_db_connection()
    manager.company_main = sc_company
    manager.company_secondary = skuf_company
    manager.compare_companies()
    manager.send_to_skuf()
    if skuf_company.state or sc_company.state or manager.state:
        process = skuf_company.process + sc_company.process + manager.process
        Bus_handler = Bus()
        Bus_handler.location = "SC_Workers_Logs"
        Bus_handler.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), Bus_handler.location)
        Bus_handler.log_process(process, '')
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_GetWorkers"))
