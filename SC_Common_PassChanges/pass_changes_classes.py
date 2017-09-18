#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
import os
import uuid
from datetime import datetime
from Bus.bus import Bus
from Bus.config import *
from Bus.metaData import *
from Bus.functions import pass_changes_error_handler


class ChangeSender(Bus):
    requests = None
    event_id = None
    current_method = "SendEvent"

    @pass_changes_error_handler
    def get_pending_event(self):
        self.location = "SC_PassChanges_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.create_db_connection()
        self.arguments = self.send_database_request(g_events.format(self.event_id)).fetchall()[0]
        self.process = self.write_process("Got event info", 0, self.process)

    @pass_changes_error_handler
    def set_event_arguments(self):
        self.location = "SC_PassChanges_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        tmp = self.arguments
        self.arguments = {'event': tmp[0],
                          'value': tmp[1],
                          'date': tmp[5],
                          'skuf_num': tmp[2],
                          'sc_num': tmp[3],
                          'notes': tmp[4],
                          'reason': tmp[6]}
        if self.arguments['notes']:
            self.arguments['notes'] = unicode(tmp[4].read(), 'utf-8')
        if self.arguments['value']:
            self.arguments['value'] = unicode(tmp[1].read(), 'utf-8')
        else:
            self.arguments['value'] = "None"
        self.process = self.write_process("successful parsed arguments", 0, self.process)

    @pass_changes_error_handler
    def determine_event_type(self):
        self.requests = []
        self.location = "SC_PassChanges_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        date1 = datetime.fromtimestamp(self.arguments['date']).strftime('%Y-%m-%dT%H:%M:%S+03:00')
        date2 = datetime.fromtimestamp(self.arguments['date']).strftime('%Y.%m.%d %H:%M')
        if self.arguments['event'] == "IS" and self.arguments['value']:
            req_as = single_event.format(sc_num=self.arguments['sc_num'],
                                         uuid=uuid.uuid1(),
                                         date=date1,
                                         event="SubIS",
                                         value=service_mapping[self.arguments['value']],
                                         )
            self.requests.append(req_as)

        if self.arguments['event'] == "Status" and self.arguments['value'] in ["Closed", "In Progress", "Assigned", "Work In Progress"]:
            req_as = single_event.format(sc_num=self.arguments['sc_num'],
                                         uuid=uuid.uuid1(),
                                         date=date1,
                                         event="state",
                                         value=simple_status[self.arguments['value']],
                                         )
            self.requests.append(req_as)

        if self.arguments['event'] == "Status" and self.arguments['value'] == "Pending":
            req_pend = tripple_event.format(sc_num=self.arguments['sc_num'],
                                            uuid=uuid.uuid1(),
                                            date=date1,
                                            event="state",
                                            value=simple_status[self.arguments['value']],
                                            uuid2=uuid.uuid1(),
                                            event2="resolution",
                                            value2=reason_mapping[self.arguments['reason']],
                                            uuid3=uuid.uuid1(),
                                            event3="DopInfo",
                                            value3=self.arguments["notes"],
                                            )
            self.requests.append(req_pend)

        if self.arguments['event'] == "Status" and self.arguments['value'] == "Resolved":
            req_resolv = tripple_event.format(sc_num=self.arguments['sc_num'],
                                              uuid=uuid.uuid1(),
                                              date=date1,
                                              event="state",
                                              value=simple_status[self.arguments['value']],
                                              uuid2=uuid.uuid1(),
                                              event2="codeOfClosing",
                                              value2=reason_mapping[self.arguments['reason']],
                                              uuid3=uuid.uuid1(),
                                              event3="solution",
                                              value3=self.arguments["notes"]
                                              )
            self.requests.append(req_resolv)

        if self.arguments['event'] == "linkedInc":
            req_inc = single_event.format(sc_num=self.arguments['sc_num'],
                                          uuid=uuid.uuid1(),
                                          date=date1,
                                          event="linkedINC",
                                          value=self.arguments['value']
                                          )
            self.requests.append(req_inc)

        if self.arguments['event'] == "priorityDown":
            req_priority = single_event.format(sc_num=self.arguments['sc_num'],
                                               uuid=uuid.uuid1(),
                                               date=date1,
                                               event="impact",
                                               value=impactCode[self.arguments['value']]
                                               )
            self.requests.append(req_priority)

        if self.arguments['event'] == "priority":
            req_priority = single_event.format(sc_num=self.arguments['sc_num'],
                                               uuid=uuid.uuid1(),
                                               date=date1,
                                               event="impact",
                                               value=impactCode[self.arguments['value']]
                                               )
            self.requests.append(req_priority)

        if self.arguments['event'] == "Recovery" and ((self.arguments['value'] == u"Оповещен о восстановлении") or (self.arguments['value'] == u"Оповестить о восстановлении")):
            req_recovery = double_event.format(sc_num=self.arguments['sc_num'],
                                               uuid=uuid.uuid1(),
                                               date=date1,
                                               event="RepairPriznak",
                                               value=recovery_mapping[self.arguments['value']],
                                               uuid2=uuid.uuid1(),
                                               event2="RepairSolution",
                                               value2=self.arguments["notes"]
                                               )
            self.requests.append(req_recovery)

        if self.arguments['event'] == "Recovery" and (self.arguments['value'] != u"Оповещен о восстановлении") and (self.arguments['value'] != u"Оповестить о восстановлении"):
            req_recovery = double_event.format(sc_num=self.arguments['sc_num'],
                                               uuid=uuid.uuid1(),
                                               date=date1,
                                               event="RepairPriznak",
                                               value=recovery_mapping[self.arguments['value']],
                                               uuid2=uuid.uuid1(),
                                               event2="RepairSolution",
                                               value2=""
                                               )
            self.requests.append(req_recovery)

        if self.arguments['event'] == "AddCommentEvent":
            self.current_method = "GetComment"
            get_comment_r = get_attach_hpd.format(user=skuf_integr_login,
                                                  pwd=skuf_integr_pass,
                                                  id=self.event_id
                                                  )
            self.process = self.write_process(self.logger(get_comment_r, "REQUEST", "GetComment", 0, self.event_id), 0,
                                              self.process)
            req = self.create_req_instance(get_comment_r,
                                           'urn:RTL:SC_Common:SendChanges_ToSC_GetComments/GetComment',
                                           skuf_get_comment
                                           )
            response = self.send_req(req, 60).read()
            text = self.get_values_by_tag_name(response.replace('ns0:', ''), 'Text')[0]
            req_comment = add_comment_sc.format(sc_num=self.arguments["sc_num"],
                                                uuid=uuid.uuid1(),
                                                date=date1,
                                                comment=text
                                                )
            self.requests.append(req_comment)

        if self.arguments['event'] == "AddAttachEvent":
            self.current_method = "GetComment"
            get_comment_r = get_attach_hpd.format(user=skuf_integr_login,
                                                  pwd=skuf_integr_pass,
                                                  id=self.event_id
                                                  )
            self.process = self.write_process(self.logger(get_comment_r, "REQUEST", "GetComment", 0, self.event_id), 0,
                                              self.process)
            req = self.create_req_instance(get_comment_r,
                                           'urn:RTL:SC_Common:SendChanges_ToSC_GetComments/GetComment',
                                           skuf_get_comment
                                           )
            response = self.send_req(req, 60).read()
            name = self.get_values_by_tag_name(response.replace('ns0:', ''), 'Name1')[0]
            data = self.get_values_by_tag_name(response.replace('ns0:', ''), 'Data1')[0]
            extension = name.split('.')[0]
            req_attach = add_attach_sc.format(sc_num=self.arguments["sc_num"],
                                              uuid=uuid.uuid1(),
                                              date=date1,
                                              base64=data,
                                              name=name,
                                              extension=extension
                                              )
            self.requests.append(req_attach)

    @pass_changes_error_handler
    def send_event_to_sc(self):
        self.current_method = "SendEvent"
        self.location = "SC_PassChanges_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for i, request in enumerate(self.requests):
            self.process = self.write_process(self.logger(self.requests[i], "REQUEST", "SendEvent", i, self.event_id), 0,
                                              self.process)
            req = self.create_req_instance(self.requests[i], 'urn:SendEvents', sc_adapter_url)
            response = self.send_req(req, 60)
            self.process = self.write_process(self.logger(response.read(), "RESPONSE", "SendEvent", i, self.event_id), 0,
                                              self.process)
            self.process = self.write_process("successful sent request №{0} to SC".format(i), 0, self.process)
        self.process = self.write_process("Done with event №{0}".format(self.event_id), 0, self.process)
        if len(self.requests) != 0:
            self.send_database_request(u_status.format(self.process, self.event_id))
        else:
            self.process = self.write_process("Cant determine event type", 0, self.process)
        self.connection.close()
        self.log_process(self.process, self.event_id)
