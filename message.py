#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
import template
import csv_writer

class Message:
    check_list = ['OutgoingPhone', 'OutgoingOriginator', 'OutgoingPartCount', 'OutgoingPartReference']
    column_names = []
    time_margin = datetime.timedelta(minutes = 1)

    def __init__(self, column_names, data):
        self.parameters = {}
        for i, name in enumerate(column_names):
                self.parameters[name] = data[i]
        Message.column_names = column_names

    def parametersArray(self):
        params = []
        for name in Message.column_names:
            params.append(self.parameters[name])
            #params.append(str(self.parameters[name]))
        return params

    def serialiseToCsv(self, delimiter, quotes):
        csv_string = ''
        for i, name in enumerate(Message.column_names):
            if i != 0:
                csv_string += delimiter
            csv_string += quotes + str(self.parameters[name]) + quotes
        return csv_string

    def get(self, key):
        return self.parameters[key]

    def checkDataRange(self, other):
        first_date = datetime.datetime.strptime(self.get('SubmitSmTime'), "%Y-%m-%d %H:%M:%S")
        second_date = datetime.datetime.strptime(other.get('SubmitSmTime'), "%Y-%m-%d %H:%M:%S")
        return (first_date <= second_date <= first_date + Message.time_margin)

    def isSutableToPart(self, other):
        for key in Message.check_list:
            if self.get(key) != other.get(key):
                return False
        return self.checkDataRange(other)

class ComplexMessage:
    def __init__(self, init_message):
        self.is_full_filed = False
        self.full_text = ""
        self.template = "-"
        self.message_type = "reklama"
        self.part_count = 0
        part = int(init_message.get('OutgoingPartSequence'))
        self.init_message_part = part if (part==0) else part-1
        part_count = int(init_message.get('OutgoingPartCount'))
        self.full_part_count = 1 if (part_count == 0) else part_count
        self.parts = [None] * self.full_part_count
        self.addPart(self.init_message_part, init_message)

    def getDate(self):
        return self.parts[self.init_message_part].get('SubmitSmTime')[:-12]

    def getOriginator(self):
        return self.parts[self.init_message_part].get('OutgoingOriginator')

    def getOperatorId(self):
        return str(self.parts[self.init_message_part].get('OperatorGroupId'))

    def getType(self):
        return self.message_type

    def getParameters(self, metrics):
        params = []
        init_message = self.parts[self.init_message_part]
        for metric in metrics:
            params.append(str(init_message.get(metric)))
        return params

    def getCount(self):
        count = 0
        if self.is_full_filed:
            count = self.full_part_count
        else:
            for part in self.parts:
                if part:
                    count += 1
        return count

    def addPart(self, pos, msg):
        if self.parts[pos] == None:
            self.parts[pos] = msg
            self.part_count += 1
            self.checkFullFiled()
            return True
        else:
            return False

    def addIfSuitable(self, msg):
        init_msg = self.parts[self.init_message_part]
        part_number = int(msg.get('OutgoingPartSequence')) - 1
        if init_msg.isSutableToPart(msg):
            return self.addPart(part_number, msg)
        else:
            return False

    def checkFullFiled(self):
        if (self.part_count==self.full_part_count):
            self.full_text = ""
            for part in self.parts:
                self.full_text += part.get('Text')
            self.is_full_filed = True

    def isFullFiled(self):
        return self.is_full_filed

    def writePartsToCsvFile(self, csvwriter):
        for part in self.parts:
            if part:
                csvwriter.writeRow(part.parametersArray() + [self.full_text, self.message_type, self.template])

    def writePartsToFile(self, out_file, delimiter, quotes):
        for part in self.parts:
            line = part.serialiseToCsv(delimiter, quotes)
            line += delimiter + quotes + self.full_text + quotes
            line += delimiter + quotes + self.message_type + quotes
            line += delimiter + quotes + self.template + quotes
            out_file.write(line + '\n')

    def simplifyFullText(self):
        text = self.full_text
        #print(text)
        text = ' '.join(text.split()) # remove tabs, newlines and multi spaces
        text = re.sub('[^\w\d \n\t\r]+', '', text)
        text = re.sub('( {2,})+', ' ', text)
        return text.lower()

    def determineTemplate(self, templates):
        if templates:
            text = self.simplifyFullText()
            #print(text)
            for template in templates:
                try:
                    a = template.getPattern().match(text)
                    #print(a)
                    if template.getPattern().match(text):
                        self.template = template.getTemplate()
                        self.message_type = template.getType()
                        return True
                except BaseException:
                    pass
        return False
