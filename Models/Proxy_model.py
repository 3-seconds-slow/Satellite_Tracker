from Models.Pandas_model import PandasModel
from PySide6.QtCore import QSortFilterProxyModel, Qt


class ProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._visible_columns = ["OBJECT_ID", "OBJECT_NAME", "updated"]

    def setVisibleColumns(self, columns):
        self._visible_columns = columns
        self.invalidateFilter()  # Re-apply filter

    def filterAcceptsColumn(self, source_column, source_parent):
        source_model = self.sourceModel()
        if isinstance(source_model, PandasModel):
            column_name = source_model.headerData(source_column, Qt.Horizontal)
            return column_name in self._visible_columns
        return True