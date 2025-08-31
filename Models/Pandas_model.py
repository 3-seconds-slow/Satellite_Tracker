import pandas as pd
from PySide6.QtCore import QAbstractTableModel, Qt

class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame, parent=None):
        super().__init__(parent)
        self._df = df

    def rowCount(self, parent=None):
        return len(self._df)

    def columnCount(self, parent=None):
        return len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if index.isValid() and role == Qt.DisplayRole:
            return str(self._df.iloc[index.row(), index.column()])
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._df.columns[section])
            if orientation == Qt.Vertical:
                return str(section)
        return None
