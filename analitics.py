#!/usr/bin/env python
# -*- coding: utf-8 -*-

class Analitics:
    headers = ['Date','Transaction','Transaction %','Service','Service %','Reklama','Reklama %','All']
    def __init__(self, path, metrics):
        self.outputfile_path = path
        self.data = {}
        self.metrics = metrics
        for i, value in enumerate(metrics):
            Analitics.headers.insert(i+1, value)

    def getPath(self):
        return self.outputfile_path

    def addData(self, date, params, type, count):
        key = date + ';' + (';').join(params);
        if not key in self.data:
            self.data[key] = { 'service':0,
                                'transaction':0,
                                'reklama':0}
        self.data[key][type] += count

    def _getFullDict(self):
        full_dict = {}
        for coded_keys, item in self.data.items():
            keys = coded_keys.split(';')
            temp = full_dict
            key = None
            for i in range(len(self.metrics) + 1): # +1 because of date
                key = keys[i]
                if not key in temp:
                    temp[key] = {}
                temp = temp[key]
            for k, v in item.items():
                temp[k] = v
        return full_dict

    def getCounters(self, index, dictionary, row, rows):
        transaction = 0
        service = 0
        reklama = 0
        all = 0
        for key, value in dictionary.items():
            row[index+1] = key
            if index == len(self.metrics)-1:
                temp_transaction = value['transaction']
                temp_service = value['service']
                temp_reklama = value['reklama']
                temp_all = temp_transaction + temp_service + temp_reklama
                transaction += temp_transaction
                service += temp_service
                reklama += temp_reklama
                all += temp_all
                transaction_per = temp_transaction/(temp_all*1.00) * 100
                service_per = temp_service/(temp_all*1.00) * 100
                reklama_per = temp_reklama/(temp_all*1.00) * 100
                row[len(self.metrics)+1] = temp_transaction
                row[len(self.metrics)+2] =  transaction_per
                row[len(self.metrics)+3] = temp_service
                row[len(self.metrics)+4] =  service_per
                row[len(self.metrics)+5] = temp_reklama
                row[len(self.metrics)+6] =  reklama_per
                row[len(self.metrics)+7] = temp_all
            else:
                temp_transaction, temp_service, temp_reklama, temp_all = self.getCounters(index+1, value, row.copy(), rows)
                transaction += temp_transaction
                service += temp_service
                reklama += temp_reklama
                all += temp_all
                transaction_per = temp_transaction/(temp_all*1.00) * 100
                service_per = temp_service/(temp_all*1.00) * 100
                reklama_per = temp_reklama/(temp_all*1.00) * 100
                row[len(self.metrics)+1] = temp_transaction
                row[len(self.metrics)+2] =  transaction_per
                row[len(self.metrics)+3] = temp_service
                row[len(self.metrics)+4] =  service_per
                row[len(self.metrics)+5] = temp_reklama
                row[len(self.metrics)+6] =  reklama_per
                row[len(self.metrics)+7] = temp_all
            rows.append(row.copy())
        return transaction, service, reklama, all

    def compiledRows(self):
        csv_table = []
        csv_table.append(Analitics.headers)
        empty_row = ['']*len(Analitics.headers)
        csv_table.append(empty_row)

        full_dict = self._getFullDict()
        for date, temp_full_dict in full_dict.items():
            start_row = [date, '0', '0', '0',  '0', '0', '0', '0']
            for i in range(len(self.metrics)):
                start_row.insert(1, 'ALL')
            all_transaction, all_service, all_reklama, all_full = self.getCounters(0, temp_full_dict, start_row.copy(), csv_table)
            transaction_per = all_transaction/(all_full*1.00) * 100
            service_per = all_service/(all_full*1.00) * 100
            reklama_per = all_reklama/(all_full*1.00) * 100
            start_row[len(self.metrics)+1] = all_transaction
            start_row[len(self.metrics)+2] =  transaction_per
            start_row[len(self.metrics)+3] = all_service
            start_row[len(self.metrics)+4] =  service_per
            start_row[len(self.metrics)+5] = all_reklama
            start_row[len(self.metrics)+6] =  reklama_per
            start_row[len(self.metrics)+7] = all_full
            csv_table.append(start_row)
            csv_table.append(empty_row)

        return csv_table
