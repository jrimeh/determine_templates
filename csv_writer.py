#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import os

class CSVWriter:
    postpix = '_{0}'
    def __init__(self, maxlines, filename, delimiter=',',quotechar='"', codec_bom = None, headers = None):
        self.maxlines = maxlines
        self.filename = filename + CSVWriter.postpix + '.csv'
        self.delimiter = delimiter
        self.quotechar = quotechar
        self.quoting = csv.QUOTE_ALL
        self.codec_bom = codec_bom
        self.headers = headers
        self.cur_csvfile = None
        self.cur_csvwriter = None
        self.part_counter = 1
        self.line_counter = 0

    def _fileOpen(self):
        try:
            filename = self.filename.format(self.part_counter)
            if not os.path.exists(os.path.dirname(filename)):
                os.makedirs(os.path.dirname(filename))
            self.cur_csvfile = open(filename, 'w', newline='', encoding='utf-8-sig')
        except IOError:
            self.cur_csvfile = None
            return
        if self.codec_bom:
            self.cur_csvfile.write(self.codec_bom)

    def _fileClose(self):
        if self.cur_csvfile:
            self.cur_csvfile.close()
            self.cur_csvfile = None

    def _initCsvWriter(self):
        if not self.cur_csvfile:
            self._fileOpen()
            self.cur_csvwriter = csv.writer(self.cur_csvfile,
                                            delimiter=self.delimiter,
                                            quotechar=self.quotechar,
                                            quoting=self.quoting)
            if self.headers:
                self._writeRow(self.headers)

    def _clearCsvWriter(self):
        if self.cur_csvwriter:
            self._fileClose()
            self.cur_csvwriter = None

    def _writeRow(self, array):
        self.cur_csvwriter.writerow(array)
        self.line_counter += 1

    def setHeaders(self, headers):
        self.headers = headers

    def writeRow(self, array):
        if not self.cur_csvwriter:
            self._initCsvWriter()
        if self.cur_csvwriter:
            self._writeRow(array)
        if self.line_counter==self.maxlines:
            self._clearCsvWriter()
            self.line_counter = 0
            self.part_counter += 1


    def close(self):
        self._clearCsvWriter()
