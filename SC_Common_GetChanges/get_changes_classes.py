#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
import re
import os
from Bus.bus import Bus
from Bus.config import *
from Bus.metaData import *
from xml.dom.minidom import *
from Bus.functions import get_changes_error_handler, check_author, check_duplicates


class ChangeCollector(Bus):
    mode = "True"
    count = None
    team_id = None
    requests = None
    event_id = None
    comments = None
    condition = None
    package_id = None
    attachments = None
    current_method = None

    @staticmethod
    def parse_naumen_xml(raw_xml, attrs):  # Метод парсинга xml, возвращаемой нативного адаптера Naumen
        parsed_xml = parseString(raw_xml.replace('ns1:', ''))
        entries = parsed_xml.getElementsByTagName('entry')
        for entry in entries:
            tmp_entry = parseString(entry.toxml().encode('utf-8')).getElementsByTagName('key')
            node_value = tmp_entry[0].childNodes[0].nodeValue
            if node_value == "impact" and "priority" in attrs.keys():
                attrs['priority'] = skuf_priority[entry.getElementsByTagName('catalog-item')[0].attributes["uuid"].value]
            if node_value == "state" and 'state' in attrs.keys():
                attrs['state'] = Bus.node_val(entry.getElementsByTagName('string'))
                if attrs['state'] == "resolved":
                    entries2 = parsed_xml.getElementsByTagName('entry')
                    for entry2 in entries2:
                        tmp_entry2 = parseString(entry2.toxml().encode('utf-8')).getElementsByTagName('key')
                        node_value = tmp_entry2[0].childNodes[0].nodeValue
                        if node_value == "solution":
                            TAG_RE = re.compile(r'<[^>]+>')
                            attrs.pop('state')
                            attrs.update({"solution": ""})
                            attrs["solution"] = TAG_RE.sub('', Bus.node_val(entry2.getElementsByTagName('string')))
            if node_value == "RepairPriznak" and 'recovery' in attrs.keys():
                attrs['recovery'] = recovery_mapping_reversed[entry.getElementsByTagName('catalog-item')[0].attributes["uuid"].value]

    def pars_adapter_xml(self, raw_xml):
        attach_names = []
        valid_comments = []
        attach_file = 0
        attach_comment = 0
        files_dict = {}
        comment_dict = {}
        package_id = None
        TAG_RE = re.compile(r'<[^>]+>')
        parsed_xml = parseString(raw_xml)

        entries = parsed_xml.getElementsByTagName('CommonEvent')

        for entry in entries:
            tmp_entry = parseString(entry.toxml().encode('utf-8')).getElementsByTagName('Category')
            if self.node_val(tmp_entry) == "changeCase":
                if check_author(self, entry):
                    self.arguments.update({'metaClass': ''})
            if self.node_val(tmp_entry) == "edit":
                if u'Приоритет' in self.node_val(entry.getElementsByTagName('Message')):
                    if check_author(self, entry):
                        self.arguments.update({'priority': ''})
                if u'Восстановлен' in self.node_val(entry.getElementsByTagName('Message')):
                    if check_author(self, entry):
                        self.arguments.update({'recovery': ''})
                if u"'-'." in self.node_val(entry.getElementsByTagName('Message')):
                    if check_author(self, entry):
                        self.arguments.update({'recovery': ''})
            if self.node_val(tmp_entry) == "wfChangeStatus":
                if check_author(self, entry):
                    self.arguments.update({'state': ''})
            if self.node_val(tmp_entry) == "attach_file":
                if check_author(self, entry):
                    attach_file = 1
                    attach_names.append(self.node_val(entry.getElementsByTagName('Message'))[17:-1])
            if self.node_val(tmp_entry) == "commentAdd":
                if check_author(self, entry):
                    attach_comment = 1

            try:
                package_id = parsed_xml.getElementsByTagName('ns2:Task')[0].attributes["packageId"].value
            except KeyError:
                package_id = None

        if attach_file:
            file_events = parsed_xml.getElementsByTagName('AddFileEvent')
            for number, entry in enumerate(file_events):
                tmp_dict = {'File{0}': ""}
                key_tmp = tmp_dict.keys()[0].format(number)
                file_dict = {"Name": "", "b64": "", "Id": ""}
                tmp_entry = entry.toxml().encode("utf-8")
                file_dict["Id"] = self.node_val(parseString(tmp_entry).getElementsByTagName('Id'))
                file_dict["Name"] = self.node_val(parseString(tmp_entry).getElementsByTagName('Reference'))
                file_dict["b64"] = self.node_val(parseString(tmp_entry).getElementsByTagName('BinaryContent'))
                if check_duplicates(self, file_dict["Id"]):
                    self.process = self.write_process('Found existing attach: {0}'.format(file_dict["Id"]), 0, self.process)
                    continue
                if file_dict["Name"] not in attach_names:
                    self.process = self.write_process('Found own attach: {0}'.format(file_dict["Id"]), 0, self.process)
                    continue
                files_dict.update(tmp_dict)
                files_dict[key_tmp] = {"Name": file_dict["Name"], "b64": file_dict["b64"], "Id": file_dict["Id"]}
            if "File{0}" in files_dict.keys():
                files_dict.pop("File{0}")

        if attach_comment:
            change_events, skip = parsed_xml.getElementsByTagName('ChangeAttributeEvent'), 1
            for entry in change_events:
                tmp_entry = parseString(entry.toxml().encode('utf-8')).getElementsByTagName('Name')
                if self.node_val(tmp_entry) == u"!Комментарий к приостановке":
                    comment_txt = self.node_val(parseString(entry.toxml().encode("utf-8")).getElementsByTagName('Value'))
                    common_events = parsed_xml.getElementsByTagName('CommonEvent')
                    for event in common_events:
                        if self.node_val(parseString(event.toxml().encode("utf-8")).getElementsByTagName('Category')) == "edit":
                            edit_value = self.node_val(parseString(event.toxml().encode("utf-8")).getElementsByTagName('Message'))
                            if edit_value == comment_txt and check_author(self, event) and edit_value != u"''":
                                valid_comments.append(comment_txt[1:-1])

            comment_events = parseString(raw_xml).getElementsByTagName('AddCommentEvent')
            for number, entry in enumerate(comment_events):
                for comment in valid_comments:
                    if len(parseString(entry.toxml().encode("utf-8")).getElementsByTagName('Text')[0].childNodes) == 0:
                        continue
                    if self.node_val(parseString(entry.toxml().encode("utf-8")).getElementsByTagName('Text')) is None:
                        continue
                    if comment in self.node_val(parseString(entry.toxml().encode("utf-8")).getElementsByTagName('Text')):
                        skip = 0
                        break

                tmp_dict = {'Comment{0}': ""}
                key_tmp = tmp_dict.keys()[0].format(number)
                comment = {"Author": "", "Text": "", "OriginalDate": "", "Id": ""}
                tmp_entry = entry.toxml().encode("utf-8")
                if len(parseString(tmp_entry).getElementsByTagName('Text')[0].childNodes) == 0:
                    continue
                elif self.node_val(parseString(tmp_entry).getElementsByTagName('Text')) is None:
                    continue
                elif skip and self.node_val(parseString(tmp_entry).getElementsByTagName('Author')) in [u"СКУФ Служебный", u"суперпользователь"]:
                    continue
                comment["Id"] = self.node_val(parseString(tmp_entry).getElementsByTagName('Id'))
                comment["Author"] = self.node_val(parseString(tmp_entry).getElementsByTagName('Author'))
                comment["Text"] = self.node_val(parseString(tmp_entry).getElementsByTagName('Text'))
                comment["Text"] = Bus.replace_html_chars(TAG_RE.sub('', comment["Text"]))
                comment["OriginalDate"] = self.node_val(parseString(tmp_entry).getElementsByTagName('Date'))
                if check_duplicates(self, comment["Id"]):
                    self.process = self.write_process('Found existing comment: {0}'.format(comment["Id"]), 0, self.process)
                    continue
                comment_dict.update(tmp_dict)
                comment_dict[key_tmp] = {"Author": comment["Author"], "Text": comment["Text"],
                                         "OriginalDate": comment["OriginalDate"], "Id": comment["Id"]}
            if "Comment{0}" in comment_dict.keys():
                comment_dict.pop("Comment{0}")
        return package_id, files_dict, comment_dict  # Возвращает ид пакета изменений, словарь с вложениями и коммент-ми

    @get_changes_error_handler
    def get_changed_attributes(self):
        self.location = "SC_GetChanges_Logs"
        self.current_method = "GetEvents"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.create_db_connection()
        request_event = get_task_events.format(self.team_id, self.event_id)
        log = self.logger(request_event, "REQUEST", "GetEvents", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)
        req_event = self.create_req_instance(request_event, 'urn:GetTaskEventLists', sc_adapter_url)
        response = self.send_req(req_event, 60).read()
        self.package_id, self.attachments, self.comments = self.pars_adapter_xml(response)
        if self.arguments:
            self.process = self.write_process("Successefull gained names of changed attributes", 0, self.process)
            self.process = self.write_process("Names: " + ','.join(self.arguments.keys()), 0, self.process)
        else:
            self.process = self.write_process("No changes were found", 0, self.process)
        self.check_attachments()
        self.check_comments()
        log = self.logger(response, "RESPONSE", "GetEvents", self.count, self.event_id)
        self.process = self.write_process(log, 0, self.process)

    @get_changes_error_handler
    def get_current_attributes_values(self):
        self.location = "SC_GetChanges_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        if self.arguments:
            self.current_method = "GetStats"
            log = self.logger(get_task_statuses.format(self.event_id), "REQUEST", "GetStats", self.count, self.event_id)
            self.process = self.write_process(log, 0, self.process)
            req_stat = self.create_req_instance(get_task_statuses.format(self.event_id, self.team_id), '', sc_native_url)
            response = self.send_req(req_stat, 60).read()
            log = self.logger(response, "RESPONSE", "GetStats", self.count, self.event_id)
            self.process = self.write_process(log, 0, self.process)
            self.parse_naumen_xml(response, self.arguments)
            self.requests = self.prepare_attributes()

    def check_attachments(self):
        if self.attachments:
            att_length = len(self.attachments)
            self.process = self.write_process("Found {0} attachment(s)".format(att_length), 0, self.process)
            self.attachments = self.prepare_attachments()
        else:
            self.process = self.write_process("No attachments were found", 0, self.process)

    def check_comments(self):
        if self.comments:
            self.process = self.write_process("Found {0} comment(s)".format(len(self.comments)), 0, self.process)
            self.comments = self.prepare_comments()
        else:
            self.process = self.write_process("No comments were found", 0, self.process)

    def prepare_attachments(self):
        req_list = []
        attachments = [x for x in self.attachments.values()]
        for attach in attachments:
            req_list.append(add_attach_1.format(login=skuf_integr_login,
                                                passwd=skuf_integr_pass,
                                                sc_num=self.event_id,
                                                name1=attach["Name"],
                                                b64_1=attach["b64"],
                                                ID=attach["Id"]
                                                )
                            )
        if not(len(req_list)):
            req_list = None
        return req_list

    def prepare_comments(self):
        req_list = []
        comments = [x for x in self.comments.values()]
        for comment in comments:
            text = u"Автор: " + comment["Author"]+'\n'+u"Дата: "+comment["OriginalDate"]+'\n'+comment["Text"]
            req_list.append(send_comment.format(login=skuf_integr_login,
                                                passwd=skuf_integr_pass,
                                                sc_num=self.event_id,
                                                ID=comment["Id"],
                                                process=self.process,
                                                name='AddCommentEvent',
                                                value=text,
                                                mode=self.mode
                                                )
                            )
        if not(len(req_list)):
            req_list = None
        return req_list

    def prepare_attributes(self):
        req_list = []
        for attribute in self.arguments:
            req_list.append(send_change.format(login=skuf_integr_login,
                                               passwd=skuf_integr_pass,
                                               sc_num=self.event_id,
                                               ID='0',
                                               process=self.process,
                                               name=attribute,
                                               value=self.arguments[attribute],
                                               mode=self.mode
                                               )
                            )
        if not(len(req_list)):
            req_list = None
        return req_list

    @get_changes_error_handler
    def send_changes(self):
        self.location = "SC_GetChanges_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.current_method = "PassChanges"
        if self.comments:
            for i, request in enumerate(self.comments):
                comm = self.create_req_instance(request, 'urn:RTL:SC_Common:GetChangesFromSC/SendChanges',
                                                skuf_send_changes_url)
                self.send_req(comm, 60)
                self.process = self.write_process('Sent comment number {0}'.format(i), 0, self.process)
        if self.attachments:
            for i, request in enumerate(self.attachments):
                att = self.create_req_instance(request, 'urn:RTL:SC_Common:GetChangesFromSC/SendChanges',
                                               skuf_send_changes_url)
                self.send_req(att, 60)
                self.process = self.write_process('Sent file number {0}'.format(i), 0, self.process)
        if self.requests:
            for i, request in enumerate(self.requests):
                log = self.logger(request, "REQUEST", "PassChanges", i, self.event_id)
                self.process = self.write_process(log, 0, self.process)
                attr = self.create_req_instance(request, 'urn:RTL:SC_Common:GetChangesFromSC/SendChanges',
                                                skuf_send_changes_url)
                response = self.send_req(attr, 60).read()
                log = self.logger(response, "RESPONSE", "PassChanges", i, self.event_id)
                self.process = self.write_process(log, 0, self.process)
                self.process = self.write_process('Sent attribute number {0}'.format(i), 0, self.process)
        if not self.condition:
            self.ack_changes()

    def ack_changes(self):
        if self.package_id:
            ack_changes_req = ackChanges.format(self.package_id, self.team_id)
            self.current_method = "AckChanges"
            log = self.logger(ack_changes_req, "REQUEST", "AckChanges", self.count, self.event_id)
            self.process = self.write_process(log, 0, self.process)
            ack_changes = self.create_req_instance(ack_changes_req, 'urn:AckEventPackage', sc_adapter_url)
            response = self.send_req(ack_changes, 60).read()
            log = self.logger(response, "RESPONSE", "AckChanges", self.count, self.event_id)
            self.process = self.write_process(log + '\nChanges accepted', 0, self.process)
        else:
            self.process = self.write_process('Nothing to confirm', 0, self.process)
