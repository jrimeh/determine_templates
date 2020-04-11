#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

class Template:
    regex_vals = {}
    regex_vals['%d']      = r'\d+'
    regex_vals['%d+']     = r'(\d+ )*\d+'
    regex_vals['%w']      = r'[\da-zа-пр-юяё]+'
    regex_vals['%w+']     = r'([\da-zа-пр-юяё]+ )*[\da-zа-пр-юяё]+'
    regex_vals['%d{0,N}'] = r'(\d+ ){0,%d}(\d+){0,1}'
    regex_vals['%d{M,N}'] = r'(\d+ ){%d,%d}(\d+){1,1}'
    regex_vals['%w{0,N}'] = r'([\da-zа-пр-юяё]+ ){0,%d}([\da-zа-пр-юяё]+){0,1}'
    regex_vals['%w{M,N}'] = r'([\da-zа-пр-юяё]+ ){%d,%d}([\da-zа-пр-юяё]+){1,1}'

    def __init__(self, template, type, originator):
        self.template = template
        self.pattern = self.createPattern(template)
        self.type = type
        self.originator = originator

    def exchangeTemplateRegex(self, regex_value):
        if regex_value in Template.regex_vals:
            return Template.regex_vals[regex_value]
        else:
            ranges = re.match(r'^%[wd]{(\d+),(\d+)}$', regex_value)
            if ranges.group(1) == 0:
                return Template.regex_vals['%' + regex_value[1] + '{0,N}'] % (int(ranges.group(2))-1)
            else:
                return Template.regex_vals['%' + regex_value[1] + '{M,N}'] % (int(ranges.group(1))-1, int(ranges.group(2))-1)
            
        
        

    def createPattern(self, template):
        #print ('\nTEMPLATE: ' + template)
        killer = r'[^a-zA-ZА-ПР-ЮЯЁа-пр-юяё0-9 %w+{0-9}%d+{0-9,}\r\n]'
        kill_spec = re.sub(killer,'',template)
        splitted = kill_spec.split()
        try:
            for i, word in enumerate(splitted):
                if word.find('%') >= 0:
                    new_value = ''
                    temp_regex_value = ''
                    bracket = False
                    for c in word:
                        if len(temp_regex_value) == 1 and (c == 'w' or c == 'd'):
                            temp_regex_value += c
                        elif len(temp_regex_value) > 1:
                            if c == '+':
                                temp_regex_value += c
                                new_value += self.exchangeTemplateRegex(temp_regex_value)
                                temp_regex_value = ''
                            elif c == '{':
                                bracket = True
                                temp_regex_value += c
                            elif c == '}' and bracket:
                                bracket = False
                                temp_regex_value += c
                                new_value += self.exchangeTemplateRegex(temp_regex_value)
                                temp_regex_value = ''
                            elif bracket:
                                temp_regex_value += c
                            else:
                                new_value += self.exchangeTemplateRegex(temp_regex_value)
                                new_value += c
                                temp_regex_value = ''
                        else:
                            if c == '%':
                                temp_regex_value += c
                            else:
                                new_value += c
                    if len(temp_regex_value) > 1:
                        new_value += self.exchangeTemplateRegex(temp_regex_value)
                    splitted[i] = new_value
            pattern = ' '.join(splitted).lower()
            print ('\nPATTERN: ' + pattern)
            return re.compile('^' + pattern + '$', re.I)
        except BaseException:
            print('Шаблон всрат')
            pass

    def getType(self):
        return self.type

    def getPattern(self):
        return self.pattern

    def getTemplate(self):
        return self.template

    def getOriginatorId(self):
        return self.originator


#a = Template('%d{1,3} Изменён пароль на вход в QBIS.Online',1,1)
#a.createPattern
#
#
#c  = '02.12.19 08:53:09 Изменён пароль на вход в QBIS.Online'.lower()
#
#kill_spec = re.sub('[^\w\d \n\t\r]+','',c)
#print(kill_spec)