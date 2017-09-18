#!/usr/bin/python27
# -*- coding: utf8 -*-
import re
import os
from Bus.bus import Bus
from Bus.config import *
from Bus.metaData import *
from Bus.functions import main_error_handler
from base64 import b64encode
from xml.dom.minidom import *


class ScReq(Bus):
    mode = None
    user = None
    count = None
    team_id = None
    event_id = None
    comments = None
    package_id = None
    attachments = None
    current_method = None

    @main_error_handler
    def get_request_attributes(self):
        self.location = "SC_GetTickets_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.create_db_connection()
        self.current_method = "GetStats"
        self.arguments = {'descriptionInRTF': "",
                          'priority': "",
                          'origDescr': "",
                          'topic': "",
                          'metaClass': '',
                          'linkedINC': None,
                          'orgName': '',
                          'clientEmail': '',
                          'number': '',
                          'service': ''}

        log = self.logger(get_task_statuses.format(self.event_id), "REQUEST", "GetStats", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        req_stat = self.create_req_instance(get_task_statuses.format(self.event_id), '', sc_native_url)
        response = self.send_req(req_stat, 60).read()
        log = self.logger(response, "RESPONSE", "GetStats", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        self.parse_naumen_xml(response, self.arguments)
        self.process = self.write_process('Got request info', 0, self.process)

        self.current_method = "GetEvents"
        request_event = get_task_events.format(self.team_id, self.event_id)
        log = self.logger(request_event, "REQUEST", "GetEvents", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        req_event = self.create_req_instance(request_event, 'urn:GetTaskEventLists', sc_adapter_url)
        response = self.send_req(req_event, 60).read()
        log = self.logger(response, "RESPONSE", "GetEvents", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        self.package_id, self.attachments, attach_count, del_count, iteration, self.comments = self.pars_adapter_xml(response)

        dict_len = str(len(self.attachments))
        self.process = self.write_process('Got attachments info - {0},{1},{2},{3}'.format(str(attach_count),
                                          dict_len, str(del_count), str(iteration)), 0, self.process)
        if len(self.attachments) == 0:
            self.process = self.write_process("No attachments were found", 0, self.process)
        self.attachments = self.count_attachments()
        self.comments = self.prepare_comments()

    @main_error_handler
    def send_request_to_skuf(self):
        self.location = "SC_GetTickets_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.current_method = "SendToSKUF"
        self.arguments['topic'] = self.arguments['topic'][0:80] + ' SCR#' + self.arguments['number']
        assignee, self.mode, service, inc_type = self.form_variables_to_skuf_request()
        request = create_skuf_incident.format(user=skuf_integr_login,
                                              pwd=skuf_integr_pass,
                                              number=self.event_id,
                                              topic=self.arguments['topic'],
                                              descr=self.arguments['descriptionInRTF'],
                                              group=assignee,
                                              mode=self.mode,
                                              service=service,
                                              priority=skuf_priority[self.arguments['priority']],
                                              stdout=self.process,
                                              inc_type=inc_type,
                                              org=self.arguments['orgName'],
                                              email=self.arguments['clientEmail'])
        log = self.logger(request, "REQUEST", "SendToSKUF", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        skuf_req = self.create_req_instance(request, 'urn:RTL:SC_Common:GetTicketsFromSC/CreateRequest', skuf_create_inc_url)
        response = self.send_req(skuf_req, 60).read()
        log = self.logger(response, "RESPONSE", "SendToSKUF", self.count, self.event_id)
        self.process = self.write_process(log + '\nIncident created successefull', 0, self.process)
        if self.attachments:
            self.send_attachments()
        if self.comments:
            self.send_comments()
        else:
            self.process = self.write_process("No comments found", 0, self.process)
        if self.package_id:
            self.ack_changes()
        else:
            self.process = self.write_process("Nothing to Ack", 0, self.process)
        self.log_process(self.process, self.event_id)

    @staticmethod
    def parse_naumen_xml(raw_xml, attrs):
        regexp_pattern = re.compile(r'<[^>]+>')
        exp = re.compile('charset=(.*?)"')
        parsed_xml = parseString(raw_xml.replace('ns1:', ''))
        entries = parsed_xml.getElementsByTagName('entry')
        for entry in entries:
            tmp_entry = parseString(entry.toxml().encode('utf-8')).getElementsByTagName('key')
            if tmp_entry[0].childNodes[0].nodeValue == "impact":
                attrs['priority'] = entry.getElementsByTagName('catalog-item')[0].attributes["uuid"].value
            if tmp_entry[0].childNodes[0].nodeValue == "service":
                attrs['service'] = entry.getElementsByTagName('entity')[0].attributes["uuid"].value
            if tmp_entry[0].childNodes[0].nodeValue == "topic":
                attrs['topic'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue
                attrs['topic'] = regexp_pattern.sub('', attrs['topic'])
            if tmp_entry[0].childNodes[0].nodeValue == "descriptionInRTF":
                attrs['descriptionInRTF'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue
                search = exp.search(attrs['descriptionInRTF'])
                if search:
                    attrs['descriptionInRTF'] = attrs['descriptionInRTF'].replace(search.group(1), 'utf-8')
                attrs['origDescr'] = attrs['descriptionInRTF']
                attrs['descriptionInRTF'] = Bus.replace_html_chars(regexp_pattern.sub('', attrs['descriptionInRTF']))
            if tmp_entry[0].childNodes[0].nodeValue == "clientEmail":
                attrs['clientEmail'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue
            if tmp_entry[0].childNodes[0].nodeValue == "orgName":
                attrs['orgName'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue
            if tmp_entry[0].childNodes[0].nodeValue == "metaClass":
                attrs['metaClass'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue
            if tmp_entry[0].childNodes[0].nodeValue == "linkedINC":
                attrs['linkedINC'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue
            if tmp_entry[0].childNodes[0].nodeValue == "number":
                attrs['number'] = entry.getElementsByTagName('string')[0].childNodes[0].nodeValue

    @staticmethod
    def pars_adapter_xml(raw_xml):
        regexp_pattern = re.compile(r'<[^>]+>')
        files_dict, comment_dict = {}, {}
        try:
            package_id = parseString(raw_xml).getElementsByTagName('ns2:Task')[0].attributes["packageId"].value
        except KeyError:
            package_id = None
        file_events = parseString(raw_xml).getElementsByTagName('AddFileEvent')
        attach_count, del_count, iteration = len(file_events), 0, 0
        for number, entry in enumerate(file_events):
            files_dict_tmp = {'File{0}': ""}
            key_tmp = files_dict_tmp.keys()[0].format(number)
            files_dict.update({key_tmp: ""})
            file_dict = {"Name": "", "b64": "", "Id": ""}
            tmp_entry = entry.toxml().encode("utf-8")
            file_dict["Id"] = parseString(tmp_entry).getElementsByTagName('Id')[0].childNodes[0].nodeValue
            file_dict["Name"] = parseString(tmp_entry).getElementsByTagName('Reference')[0].childNodes[0].nodeValue
            file_dict["b64"] = parseString(tmp_entry).getElementsByTagName('BinaryContent')[0].childNodes[0].nodeValue
            files_dict[key_tmp] = {"Name": file_dict["Name"], "b64": file_dict["b64"], "Id": file_dict["Id"]}
            iteration += 1
        if "File{0}" in files_dict.keys():
            files_dict.pop("File{0}")
            del_count += 1

        comment_events = parseString(raw_xml).getElementsByTagName('AddCommentEvent')
        for number, entry in enumerate(comment_events):
            tmp = {'Comment{0}': ""}
            key_tmp = tmp.keys()[0].format(number)
            comment = {"Author": "", "Text": "", "OriginalDate": "", "Id": ""}
            tmp_entry = entry.toxml().encode("utf-8")
            if len(parseString(tmp_entry).getElementsByTagName('Text')[0].childNodes) == 0:
                continue
            elif parseString(tmp_entry).getElementsByTagName('Text')[0].childNodes[0].nodeValue is None:
                continue
            comment["Id"] = parseString(tmp_entry).getElementsByTagName('Id')[0].childNodes[0].nodeValue
            comment["Author"] = parseString(tmp_entry).getElementsByTagName('Author')[0].childNodes[0].nodeValue
            comment["Text"] = parseString(tmp_entry).getElementsByTagName('Text')[0].childNodes[0].nodeValue
            comment["Text"] = Bus.replace_html_chars(regexp_pattern.sub('', comment["Text"]))
            comment["OriginalDate"] = parseString(tmp_entry).getElementsByTagName('Date')[0].childNodes[0].nodeValue
            comment_dict.update(tmp)
            comment_dict[key_tmp] = {"Author": comment["Author"], "Text": comment["Text"],
                                     "OriginalDate": comment["OriginalDate"], "Id": comment["Id"]}
            if "Comment{0}" in comment_dict.keys():
                comment_dict.pop("Comment{0}")
        return package_id, files_dict, attach_count, del_count, iteration, comment_dict

    def count_attachments(self):
        att_length = len(self.attachments)
        if att_length % 3 == 0:
            amount_of_reqs = att_length / 3
            return self.prepare_attachments(amount_of_reqs)
        else:
            if att_length > 3:
                amount_of_reqs = att_length // 3
                return self.prepare_attachments(amount_of_reqs, att_length - amount_of_reqs*3)
            else:
                return self.prepare_attachments(0, att_length)

    def prepare_comments(self):
        req_list = []
        comments = [x for x in self.comments.values()]
        for comment in comments:
            text = u"Автор: " + comment["Author"]+'\n'+u"Дата: "+comment["OriginalDate"]+'\n'+comment["Text"]
            req_list.append(send_comment.format(login=skuf_integr_login,
                                                passwd=skuf_integr_pass,
                                                sc_num=self.event_id,
                                                name='AddCommentEvent',
                                                value=text,
                                                mode="True",
                                                ID=comment["Id"]))
        if not(len(req_list)): req_list = None
        return req_list

    def prepare_attachments(self, amount_of_reqs, remains=0):
        req_list = []
        attachments = [x for x in self.attachments.values()]
        orig_descr = b64encode(self.arguments['origDescr'].encode("utf-8"))
        req_list.append(add_attach_1.format(login=skuf_integr_login,
                                            passwd=skuf_integr_pass,
                                            name1=u"Описание.html",
                                            b64_1=orig_descr,
                                            sc_num=self.event_id,
                                            ID=""))
        if amount_of_reqs != 0:
            for attach in range(0, amount_of_reqs):
                req_list.append(add_attach_full.format(login=skuf_integr_login,
                                                       passwd=skuf_integr_pass,
                                                       name1=attachments[0]["Name"],
                                                       b64_1=attachments[0]["b64"],
                                                       name2=attachments[1]["Name"],
                                                       b64_2=attachments[1]["b64"],
                                                       name3=attachments[2]["Name"],
                                                       b64_3=attachments[2]["b64"],
                                                       sc_num=self.event_id,
                                                       ID=attachments[0]["Id"]+","+attachments[1]["Id"]+","+attachments[2]["Id"]))
                del attachments[0:3]
        if remains == 1:
            req_list.append(add_attach_1.format(login=skuf_integr_login,
                                                passwd=skuf_integr_pass,
                                                name1=attachments[0]["Name"],
                                                b64_1=attachments[0]["b64"],
                                                sc_num=self.event_id,
                                                ID=attachments[0]["Id"]))
        if remains == 2:
            req_list.append(add_attach_2.format(login=skuf_integr_login,
                                                passwd=skuf_integr_pass,
                                                name1=attachments[0]["Name"],
                                                b64_1=attachments[0]["b64"],
                                                name2=attachments[1]["Name"],
                                                b64_2=attachments[1]["b64"],
                                                sc_num=self.event_id,
                                                ID=attachments[0]["Id"]+","+attachments[1]["Id"]))
        return req_list

    def form_variables_to_skuf_request(self):
        mode = "False"
        assignee = unicode(assignment_mapping[str(self.user)], "utf-8")
        if self.arguments['priority'] == '':
            self.arguments['priority'] = u'priority$7002'
        if self.arguments['metaClass'] in allowed_meta_classes:
            mode = "True"
        if self.arguments['metaClass'] in ServiceMapping.keys():
            service = unicode(ServiceMapping[self.arguments['metaClass']].split(':')[0], "utf-8")
            inc_type = unicode(ServiceMapping[self.arguments['metaClass']].split(':')[1], "utf-8")
        else:
            service = u"Не определен"
            inc_type = "Information Request"
        return assignee, mode, service, inc_type

    def send_attachments(self):
        self.current_method = "SendAttach"
        self.location = "SC_GetTickets_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for i, request in enumerate(self.attachments):
            att = self.create_req_instance(request, 'urn:RTL:SC_Common:GetChangesFromSC/SendChanges', skuf_send_changes_url)
            self.send_req(att, 60).read()
            self.process = self.write_process('Sent attach №{0}'.format(i), 0, self.process)

    def send_comments(self):
        self.current_method = "SendComment"
        self.location = "SC_GetTickets_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for i, request in enumerate(self.comments):
            comment = self.create_req_instance(request, 'urn:RTL:SC_Common:GetChangesFromSC/SendChanges', skuf_send_changes_url)
            self.send_req(comment, 60).read()
            self.process = self.write_process('Sent comment №{0}'.format(i), 0, self.process)

    def ack_changes(self):
        ack_changes_req = ackChanges.format(self.package_id, self.team_id)
        self.current_method = "AckChanges"
        log = self.logger(ack_changes_req, "REQUEST", "AckChanges", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        ack_changes = self.create_req_instance(ack_changes_req, 'urn:AckEventPackage', sc_adapter_url)
        response = self.send_req(ack_changes, 60).read()
        log = self.logger(response, "RESPONSE", "AckChanges", self.count, self.event_id)
        self.process = self.write_process(log + '\nChanges accepted', 0, self.process)
