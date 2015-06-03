# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals
from eight import *

from ...signals import signals
from .activity import ActivityItem
from brightway2 import databases, Database
from bw2data.utils import natural_sort
from PyQt4 import QtCore, QtGui
import itertools


class FlowsTableWidget(QtGui.QTableWidget):
    COUNT = 100
    COLUMNS = {
        0: "name",
        2: "unit"
    }

    def __init__(self):
        super(FlowsTableWidget, self).__init__()
        self.setColumnCount(3)
        self.setDragEnabled(True)
        self.setHorizontalHeaderLabels(["Name", "Categories", "Unit"])

        signals.database_selected.connect(self.sync)

    def sync(self, name):
        self.clear()
        self.database = Database(name)
        self.database.order_by = 'name'
        self.database.filters = {'type': 'emission'}
        self.setRowCount(min(len(self.database), self.COUNT))
        self.setHorizontalHeaderLabels(["Name", "Categories", "Unit"])
        data = itertools.islice(self.database, 0, self.COUNT)
        for row, ds in enumerate(data):
            for col, value in self.COLUMNS.items():
                self.setItem(row, col, ActivityItem(ds.get(value, ''), key=ds.key))
            self.setItem(row, 1, ActivityItem(", ".join(ds.get('categories', [])), key=ds.key))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()

    def reset_search(self):
        self.sync(self.database.name)

    def search(self, search_term):
        search_result = self.database.search(search_term, limit=self.COUNT, **self.database.filters)
        self.clear()
        self.setRowCount(len(search_result))
        self.setHorizontalHeaderLabels(["Name", "Categories", "Unit"])
        for row, ds in enumerate(search_result):
            for col, value in self.COLUMNS.items():
                self.setItem(row, col, ActivityItem(ds.get(value, ''), key=ds.key))
            self.setItem(row, 1, ActivityItem(", ".join(ds.get('categories', [])), key=ds.key))

        self.resizeColumnsToContents()
        self.resizeRowsToContents()
