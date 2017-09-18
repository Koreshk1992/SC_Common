#!/usr/local/bin/python2.7
# -*- coding: utf8 -*-
import os
import urllib2
from Bus.bus import Bus
from Bus.config import *
from Bus.metaData import *
from xml.dom.minidom import *
from Bus.functions import get_workers_error_handler


class Organization:
    def __init__(self, title, team_id, uuid):
        self.title = title
        self.team_id = team_id
        self.uuid = uuid
        self.flag = {'changed': None, 'new': None, 'delete': None}


class Company(Bus):
    company_name = None
    org_list = {}
    update_list = {}
    create_list = {}
    delete_list = {}
    state = None
    location = "SC_Workers_Logs"
    logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), location)

    @staticmethod
    def ru(string):
        return unicode(string, 'utf-8').encode('utf-8')

    @staticmethod
    def parse_naumen_xml(raw_xml):  # Метод парсинга xml, возвращаемой от soap адаптера СЦ
        result = []
        parsed_xml = parseString(raw_xml.replace('ns1:', ''))
        entries = parsed_xml.getElementsByTagName('objects')
        for entry in entries:
            values = parseString(entry.toxml().encode('utf-8')).getElementsByTagName('string')
            tmp_dict = {'title': None, 'id': None}
            for value in values:
                if 'team$' in value.childNodes[0].nodeValue:
                    tmp_dict['id'] = value.childNodes[0].nodeValue
                else:
                    tmp_dict['title'] = value.childNodes[0].nodeValue
            result.append([tmp_dict['title'].encode("utf-8"), tmp_dict['id']])
        return result

    @get_workers_error_handler
    def get_company_orgs(self):
        self.location = "SC_Workers_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.create_db_connection()
        if self.company_name == "SKUF":
            self.cursor.execute(g_skuf_orgs)
            self.org_list = {x[1]: Organization(self.ru(x[0]), x[1], x[2]) for x in self.cursor}
        if self.company_name != "SKUF":
            req = self.create_req_instance(sc_req.encode('utf-8'), '', sc_native_url)
            response = urllib2.urlopen(req, timeout=60)
            tmp_list = self.parse_naumen_xml(response.read())
            self.org_list = {x[1]: Organization(x[0], x[1], None) for x in tmp_list}


class CompanyManager(Bus):
    state = None
    company_main = None
    company_secondary = None
    location = "SC_Workers_Logs"
    logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), location)

    def check_delete(self):
        self.location = "SC_Workers_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for key in self.company_secondary.org_list.keys():
            if key not in self.company_main.org_list.keys():
                self.company_secondary.org_list[key].flag['delete'] = 1

    def check_create(self):
        self.location = "SC_Workers_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for key, value in self.company_main.org_list.items():
            if key not in self.company_secondary.org_list.keys():
                self.company_secondary.org_list.update({key: Organization(value.title, value.team_id, None)})
                self.company_secondary.org_list[key].flag["new"] = 1

    def check_update(self):
        self.location = "SC_Workers_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for key in self.company_secondary.org_list.keys():
            if not self.company_secondary.org_list[key].flag["delete"]:
                if self.company_secondary.org_list[key].title != self.company_main.org_list[key].title:
                    self.company_secondary.org_list[key].title = self.company_main.org_list[key].title
                    self.company_secondary.org_list[key].flag["changed"] = 1

    @get_workers_error_handler
    def compare_companies(self):
        self.location = "SC_Workers_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        self.check_delete()
        self.check_create()
        self.check_update()

    @get_workers_error_handler
    def send_to_skuf(self):
        self.location = "SC_Workers_Logs"
        self.logs_directory = os.path.join(os.path.dirname(os.path.realpath(__file__)), self.location)
        for org_id, org in self.company_secondary.org_list.items():
            if org.flag["new"]:
                req = self.create_req_instance(create_worker.format(login=skuf_integr_login,
                                                                    pwd=skuf_integr_pass,
                                                                    name=unicode(org.title, 'utf-8'),
                                                                    id=org.team_id),
                                               'urn:RTL:SC_Common:Workers/Create',
                                               skuf_workers_url
                                               )
                self.send_req(req, 60)
            if org.flag["changed"]:
                req = self.create_req_instance(change_worker.format(login=skuf_integr_login,
                                                                    pwd=skuf_integr_pass,
                                                                    name=unicode(org.title, 'utf-8'),
                                                                    id=org.uuid,
                                                                    action="change"),
                                               'urn:RTL:SC_Common:Workers/SetOrDelete',
                                               skuf_workers_url
                                               )
                self.send_req(req, 60)
            if org.flag["delete"]:
                req = self.create_req_instance(change_worker.format(login=skuf_integr_login,
                                                                    pwd=skuf_integr_pass,
                                                                    name=unicode(org.title, 'utf-8'),
                                                                    id=org.uuid,
                                                                    action="delete"),
                                               'urn:RTL:SC_Common:Workers/SetOrDelete',
                                               skuf_workers_url
                                               )
                self.send_req(req, 60)
