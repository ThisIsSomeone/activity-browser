# -*- coding: utf-8 -*-
from pathlib import Path
from typing import List, Tuple

import brightway2 as bw
from PySide2 import QtGui, QtWidgets
from PySide2.QtCore import QRegExp, QThread, Qt, Signal, Slot

from activity_browser.bwutils.superstructure import get_sheet_names
from activity_browser.settings import project_settings
from activity_browser.signals import signals
from ..style import style_group_box
from ...ui.icons import qicons


class ForceInputDialog(QtWidgets.QDialog):
    """ Due to QInputDialog not allowing 'ok' button to be disabled when
    nothing is entered, we have this.

    https://stackoverflow.com/questions/48095573/how-to-disable-ok-button-in-qinputdialog-if-nothing-is-typed
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QtWidgets.QLabel()
        self.input = QtWidgets.QLineEdit()
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        )
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)

        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.input.textChanged.connect(self.changed)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    @property
    def output(self):
        return self.input.text()

    @Slot(name="inputChanged")
    def changed(self):
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(bool(self.input.text()))

    @classmethod
    def get_text(cls, parent: QtWidgets.QWidget, title: str, label: str, text: str = "") -> 'ForceInputDialog':
        obj = cls(parent)
        obj.setWindowTitle(title)
        obj.label.setText(label)
        obj.input.setText(text)
        return obj


class TupleNameDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.name_label = QtWidgets.QLabel("New name")
        self.view_name = QtWidgets.QLabel()
        self.no_comma_validator = QtGui.QRegExpValidator(QRegExp("[^,]+"))
        self.input_fields = []
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.name_label)
        row.addWidget(self.view_name)
        layout.addLayout(row)
        self.input_box = QtWidgets.QGroupBox(self)
        self.input_box.setStyleSheet(style_group_box.border_title)
        input_field_layout = QtWidgets.QVBoxLayout()
        self.input_box.setLayout(input_field_layout)
        layout.addWidget(self.input_box)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    @property
    def combined_names(self) -> str:
        """Reads all of the input fields in order and returns a string."""
        return ", ".join(self.result_tuple)

    @property
    def result_tuple(self) -> tuple:
        result = [f.text() for f in self.input_fields if f.text()]
        if not self.input_fields[-1].text():
            result.append(self.input_fields[-1].placeholderText())
        return tuple(result)

    @Slot(name="inputChanged")
    def changed(self) -> None:
        """Rebuild the view_name with text from all of the input fields."""
        self.view_name.setText("'({})'".format(self.combined_names))

    def add_input_field(self, text: str, placeholder: str = None) -> None:
        edit = QtWidgets.QLineEdit(text, self)
        edit.setPlaceholderText(placeholder or "")
        edit.setValidator(self.no_comma_validator)
        edit.textChanged.connect(self.changed)
        self.input_fields.append(edit)
        self.input_box.layout().addWidget(edit)

    @classmethod
    def get_combined_name(cls, parent: QtWidgets.QWidget, title: str, label: str,
                          fields: tuple, extra: str = "Extra") -> 'TupleNameDialog':
        obj = cls(parent)
        obj.setWindowTitle(title)
        obj.name_label.setText(label)
        for field in fields:
            obj.add_input_field(str(field))
        obj.add_input_field("", extra)
        obj.input_box.updateGeometry()
        obj.changed()
        return obj


class ExcelReadDialog(QtWidgets.QDialog):
    SUFFIXES = {".xls", ".xlsx"}

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select excel file to read")

        self.path = None
        self.path_line = QtWidgets.QLineEdit()
        self.path_line.setReadOnly(True)
        self.path_line.textChanged.connect(self.changed)
        self.path_btn = QtWidgets.QPushButton("Browse")
        self.path_btn.clicked.connect(self.browse)
        self.import_sheet = QtWidgets.QComboBox()
        self.import_sheet.addItems(["-----"])
        self.import_sheet.setEnabled(False)
        self.complete = False

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        )
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.complete)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        grid = QtWidgets.QGridLayout()
        grid.addWidget(QtWidgets.QLabel("Path to file*"), 0, 0, 1, 1)
        grid.addWidget(self.path_line, 0, 1, 1, 2)
        grid.addWidget(self.path_btn, 0, 3, 1, 1)
        grid.addWidget(QtWidgets.QLabel("Excel sheet name"), 1, 0, 1, 1)
        grid.addWidget(self.import_sheet, 1, 1, 2, 1)

        input_box = QtWidgets.QGroupBox(self)
        input_box.setStyleSheet(style_group_box.border_title)
        input_box.setLayout(grid)
        layout.addWidget(input_box)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    @Slot(name="browseFile")
    def browse(self) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            parent=self, caption="Select scenario template file",
            filter="Excel (*.xlsx);; All Files (*.*)"
        )
        if path:
            self.path_line.setText(path)

    def update_combobox(self, file_path) -> None:
        self.import_sheet.blockSignals(True)
        self.import_sheet.clear()
        names = get_sheet_names(file_path)
        self.import_sheet.addItems(names)
        self.import_sheet.setEnabled(self.import_sheet.count() > 0)
        self.import_sheet.blockSignals(False)

    @Slot(name="pathChanged")
    def changed(self) -> None:
        """Determine if selected path is valid."""
        self.path = Path(self.path_line.text())
        self.complete = all([
            self.path.exists(), self.path.is_file(),
            self.path.suffix in self.SUFFIXES
        ])
        if self.complete:
            self.update_combobox(self.path)
        self.buttons.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.complete)


class DatabaseLinkingDialog(QtWidgets.QDialog):
    """Display all of the possible links in a single dialog for the user.

    Allow users to select alternate database links."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Database linking")

        self.db_label = QtWidgets.QLabel()
        self.label_choices = []
        self.grid_box = QtWidgets.QGroupBox("Database links:")
        self.grid = QtWidgets.QGridLayout()
        self.grid_box.setLayout(self.grid)

        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.db_label)
        layout.addWidget(self.grid_box)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

    @property
    def relink(self) -> dict:
        """Returns a dictionary of str -> str key/values, showing which keys
        should be linked to which values.

        Only returns key/value pairs if they differ.
        """
        return {
            label.text(): combo.currentText() for label, combo in self.label_choices
            if label.text() != combo.currentText()
        }

    @property
    def links(self) -> dict:
        """Returns a dictionary of str -> str key/values, showing which keys
        should be linked to which values.
        """
        return {
            label.text(): combo.currentText() for label, combo in self.label_choices
        }

    @classmethod
    def construct_dialog(cls, label: str, options: List[Tuple[str, List[str]]],
                         parent: QtWidgets.QWidget = None) -> 'DatabaseLinkingDialog':
        obj = cls(parent)
        obj.db_label.setText(label)
        # Start at 1 because row 0 is taken up by the db_label
        for i, item in enumerate(options):
            label = QtWidgets.QLabel(item[0])
            combo = QtWidgets.QComboBox()
            combo.addItems(item[1])
            combo.setCurrentText(item[0])
            obj.label_choices.append((label, combo))
            obj.grid.addWidget(label, i, 0, 1, 2)
            obj.grid.addWidget(combo, i, 2, 1, 2)
        obj.updateGeometry()
        return obj

    @classmethod
    def relink_sqlite(cls, db: str, options: List[Tuple[str, List[str]]],
                      parent=None) -> 'DatabaseLinkingDialog':
        label = "Relinking exchanges from database '{}'.".format(db)
        return cls.construct_dialog(label, options, parent)

    @classmethod
    def relink_bw2package(cls, options: List[Tuple[str, List[str]]],
                          parent=None) -> 'DatabaseLinkingDialog':
        label = ("Some database(s) could not be found in the current project,"
                 " attempt to relink the exchanges to a different database?")
        return cls.construct_dialog(label, options, parent)

    @classmethod
    def relink_excel(cls, options: List[Tuple[str, List[str]]],
                     parent=None) -> 'DatabaseLinkingDialog':
        label = "Customize database links for exchanges in the imported database."
        return cls.construct_dialog(label, options, parent)


class DefaultBiosphereDialog(QtWidgets.QProgressDialog):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setWindowTitle("Biosphere and impact categories")
        self.setRange(0, 3)
        self.setModal(Qt.ApplicationModal)

        self.biosphere_thread = DefaultBiosphereThread(self)
        self.biosphere_thread.update.connect(self.update_progress)
        self.biosphere_thread.finished.connect(self.finished)
        self.biosphere_thread.start()

    @Slot(int, str, name="updateThread")
    def update_progress(self, current: int, text: str) -> None:
        self.setValue(current)
        self.setLabelText(text)

    def finished(self, result: int = None) -> None:
        self.biosphere_thread.exit(result or 0)
        self.setValue(3)
        signals.change_project.emit(bw.projects.current)
        signals.project_selected.emit()


class DefaultBiosphereThread(QThread):
    update = Signal(int, str)

    def run(self):
        project = "<b>{}</b>".format(bw.projects.current)
        if "biosphere3" not in bw.databases:
            self.update.emit(0, "Creating default biosphere for {}".format(project))
            bw.create_default_biosphere3()
            project_settings.add_db("biosphere3")
        if not len(bw.methods):
            self.update.emit(1, "Creating default LCIA methods for {}".format(project))
            bw.create_default_lcia_methods()
        if not len(bw.migrations):
            self.update.emit(2, "Creating core data migrations for {}".format(project))
            bw.create_core_migrations()


class TableFilterDialog(QtWidgets.QDialog):
    """Set filters for a table.

    Dialog has 1 tab per given column. Each tab has rows for filters,
    where type/query/other is defined. User can add/remove filters as desired.
    When multiple filters exist for 1 column, user can choose AND/OR combination of filters.
    AND/OR for combining columns can also be chosen.

    Required inputs:
    - column names: dict --> the column names and their indices in the table
        format: {'col_name': i}
    Optional inputs:
    - filters: dict --> pre-apply filters in the dialog (see format example below)
    - selected_column: int --> open the dialog with this column tab open
    - column_types: dict --> show other filters for this column
        format: {'col_name': 'num'}
        options: str/num, defaults to str if no type is given

    Interaction:
    - call 'start_filter_dialog' of 'ABFilterableDataFrameView' to launch dialog,
    filters are only applied when OK is selected. This calls self.get_filters,
    which returns filter data as dict.

    example of filters (see also ABMultiColumnSortProxyModel):
    filters = {
            0: {'filters': [('contains', 'heat', False), ('contains', 'electricity', False)],
                'mode': 'OR'},
            1: {'filters': [('contains', 'market', False)]}
        }
    """
    def __init__(self, column_names: dict,
                 filters: dict = None,
                 selected_column: int = 0,
                 column_types: dict = {},
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle('Set table filters')

        # set given filters, if any
        if isinstance(filters, dict):
            self.filters = filters
        else:
            self.filters = {}

        # create a tab for every column in the table
        self.tab_widget = QtWidgets.QTabWidget()
        self.tabs = []

        for col_name, i in column_names.items():
            tab = ColumnFilterTab(parent=self,
                                  state=self.filters.get(i, None),
                                  col_type=column_types.get(col_name, 'str')
                                  )
            self.tabs.append(tab)
            self.tab_widget.addTab(tab, col_name)

        # add AND/OR choice button.
        self.and_or_buttons = AndOrRadioButtons(label_text='Combine columns:')
        # in the extremely unlikely event there is only 1 column, hide the AND/OR option.
        if len(column_names) == 1:
            self.and_or_buttons.hide()

        # create OK/cancel buttons
        self.buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)

        # assemble layout
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tab_widget)
        layout.addWidget(self.and_or_buttons)
        layout.addWidget(self.buttons)
        self.setLayout(layout)

        # set the column that launched the dialog as the open tab
        self.tab_widget.setCurrentIndex(selected_column)
        self.tabs[selected_column].filter_rows[-1].filter_query_line.setFocus()

    @property
    def get_filters(self) -> dict:
        state = {}
        for i, tab in enumerate(self.tabs):
            tab_state = tab.get_state
            if isinstance(tab_state, dict):
                state[i] = tab_state
        state['mode'] = self.and_or_buttons.get_state
        return state


class ColumnFilterTab(QtWidgets.QWidget):
    """Content of column tab.

    Required inputs:
    - None
    Optional inputs:
    - col_type: str --> the type of column, either 'str' or 'num'. defines the search type options.
    defaults to 'str'
    - state: dict --> dict of existing filter state that should be re-created in UI.

    Interaction:
    - def get_state: Provides the state of all relevant filter elements (filter rows, AND/OR menu)
    returns: dict
    - def set_state: Writes given state dict to UI elements (filter rows, AND/OR menu)
    """
    def __init__(self, col_type: str = 'str', state: dict = {}, parent=None):
        super().__init__(parent)
        self.col_type = col_type

        self.add = QtWidgets.QToolButton()
        self.add.setIcon(qicons.add)
        self.add.setToolTip('Add a new filter for this column')
        self.add.clicked.connect(self.add_row)

        self.and_or_buttons = AndOrRadioButtons(label_text='Combine filters within column:')
        if self.col_type == 'str':
            self.and_or_buttons.set_state('OR')

        self.filter_rows = []
        self.filter_widget_layout = QtWidgets.QVBoxLayout()
        self.filter_widget = QtWidgets.QWidget()
        self.filter_widget.setLayout(self.filter_widget_layout)

        # set the state, adds 1 empty row if state=={}
        self.set_state(state)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.filter_widget)
        layout.addWidget(self.add)
        layout.addStretch()
        layout.addWidget(self.and_or_buttons)
        self.setLayout(layout)

    def add_row(self, state: tuple = None) -> None:
        """Add a new row to the self.filter_rows."""
        idx = len(self.filter_rows)
        new_filter_row = FilterRow(column_type=self.col_type, state=state, idx=idx, parent=self)
        self.filter_rows.append(new_filter_row)
        self.filter_widget_layout.addWidget(new_filter_row)
        self.show_hide_and_or()

    def remove_row(self, idx: int) -> None:
        """Remove the row from the setup"""
        # remove the row from widget and self.filter_rows
        self.filter_widget_layout.itemAt(idx).widget().deleteLater()
        self.filter_rows.pop(idx)
        # re-index the list of rows
        for i, filter_row in enumerate(self.filter_rows):
            filter_row.idx = i
        # if there would be no remaining rows, add a new empty one
        if len(self.filter_rows) == 0:
            self.add_row()
        self.show_hide_and_or()

    @property
    def get_state(self) -> dict:
        # check if there are filters
        if len(self.filter_rows) == 0:
            return None
        # check if there are valid filters
        valid_filters = [row.get_state for row in self.filter_rows if row.get_state]
        if len(valid_filters) == 0:
            return None
        elif len(valid_filters) == 1:
            return {'filters': valid_filters}
        else:
            return {'filters': valid_filters,
                    'mode': self.and_or_buttons.get_state}

    def set_state(self, state: dict) -> None:
        if not state:
            self.add_row()
            self.and_or_buttons.hide()
            return

        # add one row per filter
        filters = state['filters']
        self.filter_rows = []
        for filter_state in filters:
            self.add_row(filter_state)

        # set state and show/hide the AND/OR widget
        self.show_hide_and_or()
        if state.get('mode', False):
            self.and_or_buttons.set_state(state['mode'])

    def show_hide_and_or(self) -> None:
        if len(self.filter_rows) > 1:
            self.and_or_buttons.show()
        else:
            self.and_or_buttons.hide()


class FilterRow(QtWidgets.QWidget):
    """Convenience class for managing a filter input row.

    This class is purely intended for TableFilterDialog and children and should not be used elsewhere.

    Required inputs:
    - idx: int --> integer index in self.filter_rows of parent. Used as ID in parent
    idx is the index position of this FilterRow in the list of rows in parent.
    Optional inputs:
    - col_type: str --> the type of column, either 'str' or 'num'. defines the search type options.
    defaults to 'str'
    - state: tuple --> tuple of existing filter state that should be re-created in UI.

    Interaction:
    - def get_state: Provides the state of all relevant filter fields (filter type, query, case sensitive)
    returns: tuple
    - def set_state: Writes given state tuple to UI elements (filter type, query, case sensitive)
    """

    STR_FILTER_TYPES = ['contains', 'does not contain',
                        'equals', 'does not equal',
                        'starts with', 'does not start with',
                        'ends with', 'does not end with']
    NUM_FILTER_TYPES = ['=', '!=', '>=', '<=']

    def __init__(self, idx: int, column_type='str', state: tuple = None, parent=None):
        super().__init__(parent)

        self.idx = idx
        self.parent = parent

        self.column_type = column_type

        if self.column_type == 'str':
            self.filter_type = self.STR_FILTER_TYPES
        elif self.column_type == 'num':
            self.filter_type = self.NUM_FILTER_TYPES
        else:
            print('WARNING: unknown column type {}, assuming string formatting'.format(self.column_type))
            self.filter_type = self.STR_FILTER_TYPES

        layout = QtWidgets.QHBoxLayout()

        # create a 'filter type' combobox
        self.filter_type_box = QtWidgets.QComboBox()
        self.filter_type_box.addItems(self.filter_type)
        layout.addWidget(self.filter_type_box)

        # create the filter input line
        self.filter_query_line = QtWidgets.QLineEdit()
        self.filter_query_line.setFocusPolicy(Qt.StrongFocus)
        layout.addWidget(self.filter_query_line)

        # if there's case-sensitive, add that
        if column_type != 'num':
            self.case_sensitive_text = QtWidgets.QLabel('Case Sensitive:')
            self.filter_case_sensitive_check = QtWidgets.QCheckBox()
            layout.addWidget(self.case_sensitive_text)
            layout.addWidget(self.filter_case_sensitive_check)

        # add buttons to remove the row
        self.remove = QtWidgets.QToolButton()
        self.remove.setIcon(qicons.delete)
        self.remove.setToolTip('Remove this filter')
        self.remove.clicked.connect(self.self_destruct)
        layout.addWidget(self.remove)

        self.setLayout(layout)

        # set the state if one was given
        if isinstance(state, tuple):
            self.set_state(state)

    @property
    def get_state(self) -> tuple:
        # check if input is valid
        query_line = self.filter_query_line.text().translate(str.maketrans('', '', ' \n\t\r'))
        # if valid, return a tuple with the state, otherwise, return None
        if query_line == '':
            return None

        selected_type = self.filter_type_box.currentText()
        selected_query = self.filter_query_line.text()
        if self.column_type == 'num':
            state = selected_type, selected_query
        else:
            case_sensitive = self.filter_case_sensitive_check.isChecked()
            state = selected_type, selected_query, case_sensitive
        return state

    def set_state(self, state: tuple) -> None:
        if self.column_type == 'str':
            selected_type, selected_query, case_sensitive = state
        else:
            selected_type, selected_query = state
        self.filter_type_box.setCurrentIndex(self.filter_type.index(selected_type))
        self.filter_query_line.setText(selected_query)
        if self.column_type == 'str':
            self.filter_case_sensitive_check.setChecked(case_sensitive)

    def self_destruct(self) -> None:
        """Remove this FilterRow object from parent."""
        self.parent.remove_row(self.idx)


class AndOrRadioButtons(QtWidgets.QWidget):
    """Convenience class for managing AND/OR buttons.

    This class is purely intended for TableFilterDialog and children and should not be used elsewhere.

    Required inputs:
    - None
    Optional inputs:
    - label_text: str -->
    - state: str --> str of existing AND/OR state that should be re-created in UI.

    Interaction:
    - def get_state: Provides the state of AND/OR radio buttons (string of 'AND' or 'OR')
    returns: str
    - def set_state: Writes given AND/OR state UI element (string of 'AND' or 'OR')
    """
    def __init__(self, label_text: str = '', state: str = None, parent=None):
        super().__init__(parent)
        # create an AND/OR widget
        layout = QtWidgets.QHBoxLayout()
        self.btn_group = QtWidgets.QButtonGroup()
        self.AND = QtWidgets.QRadioButton('AND')
        self.OR = QtWidgets.QRadioButton('OR')
        self.btn_group.addButton(self.AND)
        self.btn_group.addButton(self.OR)
        layout.addStretch()
        layout.addWidget(QtWidgets.QLabel(label_text))
        layout.addWidget(self.AND)
        layout.addWidget(self.OR)
        self.setLayout(layout)

        # set the state if one was given, otherwise, assume AND
        if isinstance(state, str):
            self.set_state(state)
        else:
            self.set_state('AND')

    @property
    def get_state(self) -> str:
        return self.btn_group.checkedButton().text()

    def set_state(self, state: str) -> None:
        x = True
        if state == 'OR':
            x = False
        self.AND.setChecked(x)
        self.OR.setChecked(not x)
