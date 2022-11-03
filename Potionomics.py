import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QAction, QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QHBoxLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy, QTableWidgetItem,
        QSlider, QSpinBox, QDoubleSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFileDialog, QLineEdit, QStyledItemDelegate, QTableView, qApp)
import numpy as np
import pandas as pd
import itertools
from sklearn.metrics import mean_squared_error

class HeaderView(QtWidgets.QHeaderView):
    # Credit: https://stackoverflow.com/questions/61500139/what-is-the-best-widget-in-pyqt5-to-show-a-checked-list-with-columns
    checked = QtCore.pyqtSignal(bool)

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self._checkable_column = -1
        self._state = False
        self._column_down = -1

    @property
    def checkable_column(self):
        return self._checkable_column

    @checkable_column.setter
    def checkable_column(self, c):
        self._checkable_column = c

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, c):
        if self.checkable_column == -1:
            return
        self._state = c
        self.checked.emit(c)
        self.updateSection(self.checkable_column)

    def paintSection(self, painter, rect, logicalIndex):
        painter.save()
        super().paintSection(painter, rect, logicalIndex)
        painter.restore()
        if logicalIndex != self.checkable_column:
            return

        opt = QtWidgets.QStyleOptionButton()

        checkbox_rect = self.style().subElementRect(
            QtWidgets.QStyle.SE_CheckBoxIndicator, opt, None
        )
        checkbox_rect.moveCenter(rect.center())
        opt.rect = checkbox_rect
        opt.state = QtWidgets.QStyle.State_Enabled | QtWidgets.QStyle.State_Active
        if logicalIndex == self._column_down:
            opt.state |= QtWidgets.QStyle.State_Sunken
        opt.state |= (
            QtWidgets.QStyle.State_On if self.state else QtWidgets.QStyle.State_Off
        )
        self.style().drawPrimitive(QtWidgets.QStyle.PE_IndicatorCheckBox, opt, painter)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        li = self.logicalIndexAt(event.pos())
        self._column_down = li
        self.updateSection(li)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        li = self.logicalIndexAt(event.pos())
        self._column_down = -1
        if li == self.checkable_column:
            self.state = not self.state

class Controller:
    def __init__(self, model, view):
        self._model = model
        self._view = view
        self.buttonResponse()
        self.loadExistingData()

    def loadExistingData(self):
        self._view.ingredientTableData = self._model.getExistingData(self._view.ingredientTableData)
        self._view.ingredientTable.setModel(self._view.ingredientTableData)
        self._view.ingredientTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._view.ingredientTable.horizontalHeader().setStretchLastSection(True)
    
    def calculateMagimins(self):
        self._view.solutionTableData = QtGui.QStandardItemModel(0, 2, self._view)
        self._view.solutionTableData, totalMagimins = self._model.getBestCombination(self._view.ingredientTableData, self._view.solutionTableData, self._view.ingredientNumber.value(), self._view.magiminsNumber.value(), self._view.potionMaking.currentText(), self._view.dailyIngredientLimit.currentText())
        self._view.solutionTable.setModel(self._view.solutionTableData)
        self._view.solutionTable.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self._view.solutionTable.horizontalHeader().setStretchLastSection(True)
        self._view.totalMagimins.setText("Total Magimins: " + str(totalMagimins))

    def buttonResponse(self):
        self._view.calculateButton.pressed.connect(self.calculateMagimins)

class Model:
    def __init__(self):
        1

    def getExistingData(self, ingredientTableData):
        self.excelLoc = './Potionomics.xlsx'
        self.data = pd.read_excel(self.excelLoc, 'Ingredients', skiprows = 0)
        self.data = self.data.replace(np.nan, 0)

        ingredientTableData.setHorizontalHeaderLabels(["", "Name", "A", "B", "C", "D", "E", "F"])
        for n in range(self.data.shape[0]):
            it_state = QtGui.QStandardItem()
            it_state.setEditable(False)
            it_state.setCheckable(True)
            if self.data.iloc[n, 7] != 2:
                state = False
            else:
                state = True
            it_state.setCheckState(QtCore.Qt.Checked if state else 0)
            it_name = QtGui.QStandardItem(str(self.data.iloc[n, 0]))
            it_a = QtGui.QStandardItem(str(self.data.iloc[n, 1]))
            it_b = QtGui.QStandardItem(str(self.data.iloc[n, 2]))
            it_c = QtGui.QStandardItem(str(self.data.iloc[n, 3]))
            it_d = QtGui.QStandardItem(str(self.data.iloc[n, 4]))
            it_e = QtGui.QStandardItem(str(self.data.iloc[n, 5]))
            it_f = QtGui.QStandardItem(str(self.data.iloc[n, 6]))
            ingredientTableData.appendRow([it_state, it_name, it_a, it_b, it_c, it_d, it_e, it_f])
        return ingredientTableData       

    def getBestCombination(self, ingredientTableData, solutionTableData, ingredientNumber, magiminsNumber, potionMaking, dailyIngredientLimit):
        states = np.zeros((ingredientTableData.rowCount(), 1))
        for i in range(ingredientTableData.rowCount()):
            states[i] = ingredientTableData.item(i, 0).checkState()
        self.data['Unlocked'] = states
        unlockedIngredients = self.data.loc[self.data["Unlocked"] == 2,]
        if potionMaking == 'Health Potion':
            magiminUsed = [1, 2]
            magiminRatio = [1, 1]
        elif potionMaking == 'Mana Potion':
            magiminUsed = [2, 3]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Stamina Potion':
            magiminUsed = [1, 5]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Speed Potion':
            magiminUsed = [3, 4]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Tolerance Potion':
            magiminUsed = [4, 5]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Fire Tonic':
            magiminUsed = [1, 3]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Ice Tonic':
            magiminUsed = [1, 4]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Thunder Tonic':
            magiminUsed = [2, 4]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Shadow Tonic':
            magiminUsed = [2, 5]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Radiation Tonic':
            magiminUsed = [3, 5]
            magiminRatio = [1, 1]
        elif potionMaking ==  'Sight Enhancer':
            magiminUsed = [1, 2, 3]
            magiminRatio = [3, 4, 3]
        elif potionMaking ==  'Alertness Enhancer':
            magiminUsed = [2, 3, 4]
            magiminRatio = [3, 4, 3]
        elif potionMaking ==  'Insight Enhancer':
            magiminUsed = [1, 2, 5]
            magiminRatio = [4, 3, 4]
        elif potionMaking ==  'Dowsing Enhancer':
            magiminUsed = [1, 4, 5]
            magiminRatio = [3, 3, 4]
        elif potionMaking ==  'Seeking Enhancer':
            magiminUsed = [3, 4, 5]
            magiminRatio = [3, 4, 3]
        elif potionMaking ==  'Poison Cure':
            magiminUsed = [1, 3, 4]
            magiminRatio = [2, 1, 1]
        elif potionMaking ==  'Drowsiness Cure':
            magiminUsed = [1, 2, 4]
            magiminRatio = [1, 1, 2]
        elif potionMaking ==  'Petrification Cure':
            magiminUsed = [1, 3, 5]
            magiminRatio = [1, 2, 1]
        elif potionMaking ==  'Silence Cure':
            magiminUsed = [2, 3, 5]
            magiminRatio = [2, 1, 1]
        elif potionMaking ==  'Curse Cure':
            magiminUsed = [2, 3, 5]
            magiminRatio = [1, 1, 1]
        usefulIngredients = unlockedIngredients.loc[(unlockedIngredients.iloc[:, magiminUsed] > 0).any(axis=1), :]
        # Testing no other magimins
        fullList = [1, 2, 3, 4, 5, 6]
        magiminValues = {}
        for n in range(len(magiminUsed)):
            fullList.remove(magiminUsed[n])
        choosenIngredients = usefulIngredients.loc[(usefulIngredients.iloc[:, fullList] == 0).all(axis=1), :]
        for n in range(len(magiminUsed)):
            magiminValues[n] = choosenIngredients.iloc[:,magiminUsed[n]]
        ingredientsNumbers = [*range(len(choosenIngredients))]
        if dailyIngredientLimit == "Yes":
            combs = []
            for item in itertools.combinations_with_replacement(ingredientsNumbers, ingredientNumber):
                unique = list(set(item))
                dailyLimit = False
                for n in range(len(unique)):
                    if item.count(unique[n]) > choosenIngredients.iloc[unique[n], 8]:
                        dailyLimit = True
                if dailyLimit == False:
                    combs.append(list(item))
        else:
            combs = list(itertools.combinations_with_replacement(ingredientsNumbers, ingredientNumber))
        result = [0, 0, 100] # combs number, max magimins, mean square error from ideal ratio
        for n in range(len(combs)):
            lst = []
            for m in range(len(magiminUsed)):
                lst.append(sum(magiminValues[m].iloc[list(combs[n])]))
            if 0 not in lst:
                magiminRatioGet = np.array(lst)
                np.seterr(divide='ignore', invalid='ignore')
                magiminRatioGet = magiminRatioGet / min(magiminRatioGet)
                error = mean_squared_error(magiminRatio, magiminRatioGet)
                if (sum(lst) > result[1]) and (error <= result[2]) and (sum(lst) <= magiminsNumber):
                    result = [n, sum(lst), error]
        ans = choosenIngredients.iloc[list(combs[result[0]]), 0]

        solutionTableData.setHorizontalHeaderLabels(["", "Name"])
        for n in range(ans.shape[0]):
            it_state = QtGui.QStandardItem()
            it_state.setEditable(False)
            it_state.setCheckable(True)
            state = False
            it_state.setCheckState(QtCore.Qt.Checked if state else 0)
            it_name = QtGui.QStandardItem(str(ans.iloc[n]))
            solutionTableData.appendRow([it_state, it_name])
        return solutionTableData, result[1]

class MagiminsCalculator(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Magimins Calculator")
        self.setWindowFlag(Qt.WindowMinimizeButtonHint, True)
        self.setWindowFlag(Qt.WindowMaximizeButtonHint, True)

        self.ingredientTableData = QtGui.QStandardItemModel(0, 4, self)
        self.ingredientTable = QTableView(showGrid=False, selectionBehavior=QtWidgets.QAbstractItemView.SelectRows)
        headerview = HeaderView(QtCore.Qt.Horizontal, self.ingredientTable)
        headerview.checkable_column = 0
        headerview.checked.connect(self.change_state_of_model)
        self.ingredientTable.setHorizontalHeader(headerview)
        self.ingredientTable.verticalHeader().hide()
        self.ingredientTable.horizontalHeader().setMinimumSectionSize(0)

        self.solutionTableData = QtGui.QStandardItemModel(0, 2, self)
        self.solutionTable = QTableView(showGrid=False, selectionBehavior=QtWidgets.QAbstractItemView.SelectRows)
        solutionheaderview = HeaderView(QtCore.Qt.Horizontal, self.solutionTable)
        solutionheaderview.checkable_column = 0
        # solutionheaderview.checked.connect(self.change_state_of_model)
        self.solutionTable.setHorizontalHeader(solutionheaderview)
        self.solutionTable.verticalHeader().hide()
        self.solutionTable.horizontalHeader().setMinimumSectionSize(0)

        ingredientNumberLabel = QLabel()
        ingredientNumberLabel.setText("Number of Ingredients:")
        self.ingredientNumber = QSpinBox()
        self.ingredientNumber.setValue(4)
        magiminsNumberLabel = QLabel()
        magiminsNumberLabel.setText("Number of Magimins:")
        self.magiminsNumber = QSpinBox()
        self.magiminsNumber.setMaximum(2000)
        self.magiminsNumber.setValue(120)
        potionMakingLabel = QLabel()
        potionMakingLabel.setText("Potion to Craft:")
        self.potionMaking = QComboBox()
        self.potionMaking.addItem('Health Potion')
        self.potionMaking.addItem('Mana Potion')
        self.potionMaking.addItem('Stamina Potion')
        self.potionMaking.addItem('Speed Potion')
        self.potionMaking.addItem('Fire Tonic')
        self.potionMaking.addItem('Ice Tonic')
        self.potionMaking.addItem('Thunder Tonic')
        self.potionMaking.addItem('Shadow Tonic')
        self.potionMaking.addItem('Radiation Tonic')
        self.potionMaking.addItem('Sight Enhancer')
        self.potionMaking.addItem('Alertness Enhancer')
        self.potionMaking.addItem('Insight Enhancer')
        self.potionMaking.addItem('Dowsing Enhancer')
        self.potionMaking.addItem('Seeking Enhancer')
        self.potionMaking.addItem('Poison Cure')
        self.potionMaking.addItem('Drowsiness Cure')
        self.potionMaking.addItem('Petrification Cure')
        self.potionMaking.addItem('Silence Cure')
        self.potionMaking.addItem('Curse Cure')
        dailyLabel = QLabel()
        dailyLabel.setText("Limit Ingredients To Daily Limit:")
        self.dailyIngredientLimit = QComboBox()
        self.dailyIngredientLimit.addItem('Yes')
        self.dailyIngredientLimit.addItem('No')
        self.calculateButton = QPushButton("Calculate")
        self.calculateButton.setDefault(True)
        self.totalMagimins = QLabel()
        self.totalMagimins.setText("Total Magimins: 0")

        hlay = QGridLayout(self)
        hlay.addWidget(self.ingredientTable, 0, 0, 9, 1)
        hlay.addWidget(ingredientNumberLabel, 0, 1)
        hlay.addWidget(self.ingredientNumber, 1, 1)
        hlay.addWidget(magiminsNumberLabel, 2, 1)
        hlay.addWidget(self.magiminsNumber, 3, 1)
        hlay.addWidget(potionMakingLabel, 4, 1)
        hlay.addWidget(self.potionMaking, 5, 1)
        hlay.addWidget(dailyLabel, 6, 1)
        hlay.addWidget(self.dailyIngredientLimit, 7, 1)
        hlay.addWidget(self.calculateButton, 8, 1)
        hlay.addWidget(self.totalMagimins, 0, 2)
        hlay.addWidget(self.solutionTable, 1, 2, 8, 1)

    def closeEvent(self, event):
        excelLoc = './Potionomics.xlsx'
        data = pd.read_excel(excelLoc, 'Ingredients', skiprows = 0)
        data = data.replace(np.nan, 0)
        states = np.zeros((self.ingredientTableData.rowCount(), 1))
        for i in range(self.ingredientTableData.rowCount()):
            states[i] = self.ingredientTableData.item(i, 0).checkState()
        data['Unlocked'] = states
        data.to_excel(excelLoc, sheet_name = "Ingredients", index = False)


    @QtCore.pyqtSlot(bool)
    def change_state_of_model(self, state):
        for i in range(self.ingredientTableData.rowCount()):
            it = self.ingredientTableData.item(i)
            if it is not None:
                it.setCheckState(QtCore.Qt.Checked if state else QtCore.Qt.Unchecked)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    w = MagiminsCalculator()
    w.show()
    controller = Controller(model=Model(), view=w)
    sys.exit(app.exec_())