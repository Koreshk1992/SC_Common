#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
import re
import os
import uuid
from xml.dom.minidom import *
from Bus.bus import Bus
from Bus.config import *
from Bus.metaData import *
from Bus.functions import pass_task_error_handler


class Request(Bus):
    ext_id = None
    inc_num = None
    sc_num = None
    request_params = {}
    soap_request = None
    New = True

    @pass_task_error_handler
    def get_request_info(self):
        self.location = "SC_PassTasks_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.create_db_connection()
        sc_num = self.send_database_request(g_inc_created.format(self.inc_num)).fetchall()

        if u'INC' in self.inc_num:
            self.request_params = {}
            self.send_database_request(g_inc_details.format(self.inc_num))
            params_list = self.fetch_response_from_db_v2(self.cursor)[0]
            self.request_params = {'topic': re.sub(r'[0-9]', '#', params_list[0]).replace('<![CDATA[', '').replace(']]>', ''),
                                   'descriptionInRTF': re.sub(r'[0-9]', '#',params_list[1]).replace('<![CDATA[', '').replace(']]>', ''),
                                   'metaClass': "serviceCall$NewInc", 'impact': impactCode[params_list[4]],
                                   'linkedINC': params_list[5], 'agreement': 'agreement$106028301',
                                   'service': 'slmService$106028501'}
        if u'TAS' in self.inc_num:
            self.request_params = {}
            self.send_database_request(g_inc_details_oiv.format(self.inc_num))
            params_list = self.fetch_response_from_db_v2(self.cursor)[0]
            self.request_params = {'topic': re.sub(r'[0-9]', '#', params_list[0]).replace('<![CDATA[', '').replace(']]>', ''),
                                   'descriptionInRTF': re.sub(r'[0-9]', '#',params_list[1]).replace('<![CDATA[', '').replace(']]>', ''),
                                   'metaClass': "serviceCall$Consultation", 'impact': impactCode[params_list[4]],
                                   'RespIsp0': params_list[6],
                                   'parentCall': params_list[7],
                                   'linkedINC': params_list[5],
                                   'agreement': 'agreement$106028301', 'service': 'slmService$106028501', 'PriznakAutoSta': 'true',
                                   'SubIS': service_mapping[params_list[8]]}

        self.process = self.write_process("Got unprocessed ticket details", 0, self.process)
        if len(sc_num) > 0:
            sc_num = sc_num[0][0]
            self.pass_number(sc_num, self.ext_id)
            self.process = self.write_process("Got created tickets", 0, self.process)
            self.New = None

    @pass_task_error_handler
    def form_request(self):
        self.location = "SC_PassTasks_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        request_part = u""
        for key in self.request_params:
            request_part += req_part.format(Name=key, Value=self.request_params[key]) + '\n'
        self.soap_request = create_sc_inc.format(uuid=uuid.uuid1(), part=request_part)

    def pass_number(self, sc_num, ext_id):
        req_num = self.create_req_instance(set_sc_number_request.format(login=skuf_integr_login,
                                                                        pwd=skuf_integr_pass,
                                                                        number=sc_num,
                                                                        id=ext_id),
                                           "urn:RTL:SC_Common:SendTicketsToSC:SetNumber/SetNumberSC",
                                           skuf_set_number
                                           )
        self.send_req(req_num, 60)
        self.process = self.write_process("Success sending data to skuf", 0, self.process)
        self.log_process(self.process, self.inc_num)

    @pass_task_error_handler
    def send_request(self):
        self.location = "SC_PassTasks_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        req_sc = self.create_req_instance(self.soap_request, 'urn:CreateTasks', sc_adapter_url)
        self.process = self.write_process(self.logger(self.soap_request, "REQUEST", "Create", 0, self.ext_id), 0, self.process)
        self.process = self.write_process("Successful created request to SC", 0, self.process)
        response = self.send_req(req_sc, 60)
        response = response.read()
        self.process = self.write_process(self.logger(response, "RESPONSE", "Create", 0, self.ext_id), 0, self.process)
        self.sc_num = parseString(response).getElementsByTagName('id')[0].childNodes[0].nodeValue
        self.send_database_request(i_created_ticket.format(self.inc_num, self.sc_num))
        self.process = self.write_process("Successful sent request to SC", 0, self.process)
        self.pass_number(self.sc_num, self.ext_id)
        self.connection.close()
