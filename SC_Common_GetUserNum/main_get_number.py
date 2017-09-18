#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
try:
    import os
    import traceback
    from xml.dom.minidom import *
    from datetime import datetime
    from Bus.bus import Bus
    from Bus.metaData import *
    from Bus.config import *

    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(g_nums)
    nums = [x for x in bus.cursor]
    for num, form in nums:
        print num, form
        request = get_req_stats.format(num)
        req = bus.create_req_instance(request, 'urn:GetCurrentTaskStatuses', sc_adapter_url)
        sc_num = ''
        response = bus.send_req(req, 60)
        xml_resp = parseString(response.read())
        blocks = xml_resp.getElementsByTagName('Attribute')
        for elem in blocks:
            if elem.childNodes[0].childNodes[0].nodeValue == 'title':
                sc_num = elem.childNodes[1].childNodes[0].nodeValue.replace(u'№', '')
                if form == 'HPD:Help Desk':
                    bus.send_database_request(u_nums_hpd.format(sc_number=num, number=sc_num))
                else:
                    bus.send_database_request(u_nums_tms.format(sc_number=num, number=sc_num))
except Exception as error:
    file_error = open(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'GlobalError.txt'), 'a')
    file_error.write("\n\--------------------START--------------------/" + '\n' + traceback.format_exc() +
                     datetime.now().strftime('%Y.%m.%d %H:%M') + '\n' +
                     "\---------------------END--------------------/")
    file_error.close()
    bus = Bus()
    bus.create_db_connection()
    bus.send_database_request(insert_error.format(bus.remove_quotes(traceback.format_exc()), "Global", "Global_GetUserNum"))
