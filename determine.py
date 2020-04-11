#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
sys.path.append('./lib')

import os.path
import time
import datetime
import csv
import configparser
from client import ClickHouseClient
from errors import Error as ClickHouseError
from message import Message
from message import ComplexMessage
from template import Template
from counter import Counter
from csv_writer import CSVWriter
from analitics import Analitics

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

global limit_step
global complex_messages
global templates
def OnProgress(total, read, progress):
    global limit_step
    sys.stdout.write('\r' + bcolors.OKGREEN + '[ClickHouse]' + bcolors.ENDC +' Load and parse: {0}/{1} [{2}%] with limit: '.format(read, total, int(round(progress * 100))) + str(limit_step))
    sys.stdout.flush()

def DateRange(start_date_str, end_date_str):
    start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d") + datetime.timedelta(days=1)
    for n in range(int ((end_date - start_date).days)):
        yield start_date + datetime.timedelta(n)

def ColoredPrint(prefix, text, prefix_color=bcolors.OKGREEN, text_color=bcolors.HEADER):
    print(prefix_color + prefix + bcolors.ENDC + ' ' + text_color + text + bcolors.ENDC)

def PrintTabbed(array):
    result = ''
    for value in array:
        result += '{0:16}'.format(str(value))
    sys.stdout.write('\r' + bcolors.OKGREEN + '[From *.CSV] '  + bcolors.ENDC + result)
    sys.stdout.flush()

def GetTemplatesFromCSV(file_paths):
    ColoredPrint('[From *.CSV]', 'Loading templates data: ' + ', '.join(file_paths), bcolors.OKGREEN, bcolors.WARNING)
    global templates
    templates = {}
    #for pirint out load result
    operators_counter = {}
    originators = {}
    templates_counter = 0
    PrintTabbed(['OPERATORS', 'ORIGINATORS',  'TEMPLATES'])
    print()
    for file_path in file_paths:
        with open(file_path) as csvfile:
            templatereader = csv.reader(csvfile, delimiter=';')
            for row in templatereader:
                text = row[0]
                originator = row[1]
                type = row[2]
                operator_id = int(row[3])

                if not operator_id in templates:
                    templates[operator_id] = {}
                if not originator in templates[operator_id]:
                    templates[operator_id][originator] = []

                tempalte = Template(text, type, originator)
                templates[operator_id][originator].append(tempalte)
                #print out
                if not originator in originators:
                    originators[originator] = 1
                if not operator_id in operators_counter:
                    operators_counter[operator_id] = 1
                templates_counter +=1
                PrintTabbed([len(operators_counter), len(originators),  templates_counter])
            csvfile.close()
    ColoredPrint('\n[From *.CSV]', str(templates_counter) + ' templates loaded', bcolors.OKGREEN, bcolors.WARNING)

def ToComplexMessage(message):
    global complex_messages
    for id, complex_message in enumerate(complex_messages):
        if complex_message.addIfSuitable(message):
            return id, complex_message
    complex_message = ComplexMessage(message)
    complex_messages.append(complex_message)
    return len(complex_messages)-1, complex_message

def GetTemplates(operator_id, originator):
    global templates
    if operator_id in templates:
        if originator in templates[operator_id]:
            return templates[operator_id][originator]
    return None

def WriteDownAllRemainingData(csvwriter, analitics, metrics):
    global complex_messages
    for id, c_message in enumerate(complex_messages):
        c_message.writePartsToCsvFile(csvwriter)
        analitics.addData(c_message.getDate(), c_message.getParameters(metrics), c_message.getType(), c_message.getCount())
        complex_messages.pop(id)

def GenerateFileName(dir, date_start, date_end):
    filename = dir + '/data_' + date_start + '_' + date_end
    return filename

def GenerateQueryFormat(config, colums):
    colums_query = ', '.join([str(x) for x in colums])
    query_format = 'SELECT ' + colums_query + ' FROM easysms.detailed_statistics WHERE EventDate = \'{0}\''
    # SpecificValues affects on WHERE part of sql query
    if 'SpecificValues' in config:
        specific_values = config['SpecificValues']
        for name, values in specific_values.items():
            query_format += ' AND ('
            for i, value in enumerate(values.split(',')):
                if i != 0:
                    query_format += ' OR '
                query_format += name + ' = ' + value
                

            query_format += ')'
    query_format += ' GROUP BY Phase,' + colums_query + ' WITH TOTALS HAVING sum(Sign) > 0 ORDER BY SubmitSmTime LIMIT {1},{2}'
    return query_format

def LoadConfigs(path):
    ColoredPrint('[config.ini]', 'Start coniguration loading', bcolors.OKGREEN, bcolors.WARNING)
    config = configparser.ConfigParser()
    config.optionxform = str
    config.read(path)
    if len(config.sections())==0:
        GenerateDefaultConfig(config, path)
    ColoredPrint('[config.ini]', 'Coniguration loaded', bcolors.OKGREEN, bcolors.WARNING)
    return config

def GetConfigParameter(config, header, parameter):
    if not header in config:
        ColoredPrint('[config.ini]', ('Can\'t find such header({0}) in config file').format(header), bcolors.FAIL, bcolors.FAIL)
        exit()
    if not parameter in config[header]:
        ColoredPrint('[config.ini]', ('Can\'t find such parameter({0}) in header({1}) in config file').format(parameter, header), bcolors.FAIL, bcolors.FAIL)
        exit()
    return config[header][parameter]


def GenerateDefaultConfig(config, path):
    columns = ["ShortMessageId", "OutgoingGateId" , "SubmitSmTime", "OutgoingPhone", "OutgoingOriginator", "Text", "OperatorGroupId", "OutgoingPartCount", "OutgoingPartSequence", "OutgoingPartReference", "State"]
    config['Templates'] = {'paths' : '------.csv,-----.csv'}
    config['ClickHouse'] = {'host':'http://----------------',
                            'colums': (',').join(columns),
                            'limit_step':'250000'}
    config['SpecificValues'] = {'OutgoingOriginator':'------,------',
                                'OperatorGroupId':'1,4'}
    config['OutputFile'] = {'outputdir':'output',
                            'filemaxlines':'1000000',
                            'delimiter':';',
                            'quotechar':'"'}
    config['Analitics'] = {'filename':'analitics.csv',
                            'metrics':'UserId,OutgoingGateId,OperatorGroupId,OutgoingOriginator'}
    with open(path, 'w') as configfile:
        config.write(configfile)
    ColoredPrint('[config.ini]', 'Config file generated. Change it and restart script', bcolors.FAIL, bcolors.FAIL)
    exit()

def SaveAnalitics(analitics, delimiter, quotechar):
    ColoredPrint('[Analise it]', 'Starting analising passed data', bcolors.OKGREEN, bcolors.OKBLUE)
    file = open(analitics.getPath(), 'w', newline='', encoding='utf-8-sig')
    file.write(u'\ufeff')
    csvwriter = csv.writer(file,delimiter=delimiter,quotechar=quotechar,quoting=csv.QUOTE_ALL)
    csvwriter.writerows(analitics.compiledRows())
    file.close()
    ColoredPrint('[Analise it]', 'Analising ended and saved to ' + analitics.getPath(), bcolors.OKGREEN, bcolors.OKBLUE)

def main():
    global limit_step
    global complex_messages

    # configs
    config = LoadConfigs('config.ini')
    template_paths = GetConfigParameter(config, 'Templates', 'paths').split(',')
    filemaxlines = int(GetConfigParameter(config, 'OutputFile', 'filemaxlines'))
    delimiter = GetConfigParameter(config, 'OutputFile', 'delimiter')
    quotechar = GetConfigParameter(config, 'OutputFile', 'quotechar')
    outputdir = GetConfigParameter(config, 'OutputFile', 'outputdir')
    analitics_path = outputdir + '/' + GetConfigParameter(config, 'Analitics', 'filename')
    metrics = GetConfigParameter(config, 'Analitics', 'metrics').split(',') # add check if it is in query
    limit_step = int(GetConfigParameter(config, 'ClickHouse', 'limit_step'))
    clickhouse_host = GetConfigParameter(config, 'ClickHouse', 'host')
    colums = GetConfigParameter(config, 'ClickHouse', 'colums').split(',')
    date_start = sys.argv[1]
    date_end = sys.argv[2]

    complex_messages = []
    total_count = limit_step*2

    GetTemplatesFromCSV(template_paths)

    client = ClickHouseClient(clickhouse_host, on_progress=OnProgress)
    query_format = GenerateQueryFormat(config, colums)

    filename = GenerateFileName(outputdir, date_start, date_end)
    csvwriter = CSVWriter(filemaxlines, filename, delimiter, quotechar, u'\ufeff', colums + ['FullText', 'MessageType', 'Template'])
    analitics = Analitics(analitics_path, metrics)
    for single_date in DateRange(date_start, date_end):
        date_str = single_date.strftime("%Y-%m-%d")
        ColoredPrint('\n[Determiner]', 'Working on date(' + date_str + ')', bcolors.OKGREEN, bcolors.WARNING)
        limit_count = 0
        msg_count = 0
        while limit_count < total_count:
            query = query_format.format(date_str, limit_count, limit_step)
            result = client.select(query, on_progress=OnProgress, send_progress_in_http_headers=1)
            print()
            data_len = len(result.data)
            total_count = limit_count + data_len + 1
            counter = Counter(data_len, 0.2)
            for v in result.data:
                message = Message(colums, v)
                id, c_message = ToComplexMessage(message)
                if c_message.isFullFiled():
                    operator_id = message.get('OperatorGroupId')
                    originator = message.get('OutgoingOriginator')
                    c_message.determineTemplate(GetTemplates(operator_id, originator))
                    c_message.writePartsToCsvFile(csvwriter)
                    analitics.addData(date_str[:-3], c_message.getParameters(metrics), c_message.getType(), c_message.getCount())
                    complex_messages.pop(id)
                msg_count+=1
                counter.step(bcolors.OKGREEN + '[' + date_str + '] ' + bcolors.ENDC + str(msg_count) + ' messages handled')
            counter.lastTell(bcolors.OKGREEN + '[' + date_str + '] ' + bcolors.ENDC + str(msg_count) + ' messages handled')
            del result
            limit_count += limit_step
    WriteDownAllRemainingData(csvwriter, analitics, metrics)
    csvwriter.close()
    SaveAnalitics(analitics, delimiter, quotechar)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        ColoredPrint('[ERR FORMAT]', 'python3.6 determine.py <date_start(YYYY-mm-dd)> <date_end(YYYY-mm-dd)>', bcolors.FAIL, bcolors.FAIL)
        exit()
    main()
