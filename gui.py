import traceback, sys, os
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QRunnable, Signal, QObject
from analyze import do_analysis
from open_file import openFile

def gui_do_analysis(osmFileName, importFile_nodes, osmFileName_network, importFile_network, filterRegion, filterProvince, progress):
        return do_analysis(osmFileName, importFile_nodes, osmFileName_network, importFile_network, filterRegion, filterProvince, progress=progress)

class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    '''
    finished = Signal()  # QtCore.Signal
    progress = Signal(object)
    error = Signal(tuple)
    result = Signal(object)

class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(
                *self.args, **self.kwargs,
                progress=self.signals.progress
            )
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done


class RunWindow(QtWidgets.QWidget):
    def __init__(self, osmFileName, importFile_nodes, osmFileName_network, importFile_network, filterRegion, filterProvince):
        super().__init__()
        print("started run window")
        self.osmFileName = osmFileName
        self.importFile_nodes = importFile_nodes
        self.osmFileName_network = osmFileName_network
        self.importFile_network = importFile_network
        self.filterRegion = filterRegion
        self.filterProvince = filterProvince
        self.setWindowTitle("Running analysis...")
        self.vlayout = QtWidgets.QVBoxLayout(self)
        self.progressLabel = QtWidgets.QLabel("")
        self.progressLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.vlayout.addWidget(self.progressLabel)

        self.threadpool = QtCore.QThreadPool()

        worker = Worker(gui_do_analysis, osmFileName, importFile_nodes, osmFileName_network, importFile_network, filterRegion, filterProvince)
        worker.signals.result.connect(self.thread_results)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.thread_progress)
        self.threadpool.start(worker)

    def thread_results(self, results):
        self.results = results

    def thread_progress(self, progress):
        self.progressLabel.setText(progress)

    def buttonOpenFile(self):
        openFile(self.results[0].filepath)

    def showInFolder(self):
        openFile(os.path.dirname(self.results[0].filepath))
    
    def thread_complete(self):
        print("Thread complete")
        self.setWindowTitle("Done with analysis")
        self.progressLabel.setText("Results")
        model = QtCore.QStringListModel()
        self.table = QtWidgets.QTableWidget(len(self.results), 2, self)
        self.table.setHorizontalHeaderLabels(["Filename", "Node count"])
        for j in range(len(self.results)):
            filenameItem = QtWidgets.QTableWidgetItem(self.results[j].filename)
            filenameItem.setFlags(filenameItem.flags() & ~QtCore.Qt.ItemIsEditable)
            nodeCountItem = QtWidgets.QTableWidgetItem(str(self.results[j].n_nodes))
            nodeCountItem.setFlags(nodeCountItem.flags() & ~QtCore.Qt.ItemIsEditable)
            self.table.setItem(j, 0, filenameItem)
            self.table.setItem(j, 1, nodeCountItem)

        self.table.verticalHeader().hide()
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setSortingEnabled(True)
        self.table.setColumnWidth(0, 450)
        self.table.horizontalHeader().setStretchLastSection(True)

        self.vlayout.addWidget(self.table)

        self.openButton = QtWidgets.QPushButton("Show in folder")
        self.vlayout.addWidget(self.openButton)
        self.openButton.clicked.connect(self.showInFolder)


class MainWindow(QtWidgets.QWidget):
    def addFileSlot(self, fileSelectFunc, label, layout):
        label = QtWidgets.QLabel(label)
        button = QtWidgets.QPushButton("Select")
        text = QtWidgets.QLineEdit()

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(label)
        hlayout.addWidget(text)
        hlayout.addWidget(button)

        groupbox = QtWidgets.QGroupBox()
        groupbox.setLayout(hlayout)

        layout.addWidget(groupbox)

        button.clicked.connect(fileSelectFunc)

        return text, hlayout

    def addFilterWidget(self, label, layout):
        label = QtWidgets.QLabel(label)
        text = QtWidgets.QLineEdit()

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(label)
        hlayout.addWidget(text)

        groupbox = QtWidgets.QGroupBox()
        groupbox.setLayout(hlayout)

        layout.addWidget(groupbox)
        return text

    def __init__(self):
        super().__init__()
        self.osmFile = None
        self.importFile_nodes = None
        self.osmFile_network = None
        self.importFile_network = None

        vlayout = QtWidgets.QVBoxLayout(self)

        self.setWindowTitle("OSM Knooppunten import analyzer")

        vlayout1 = QtWidgets.QVBoxLayout()
        #self.text1, groupbox1 = self.addFileSlot(self.selectOSM, "OSM file:", vlayout)
        self.text1, groupbox1 = self.addFileSlot(self.selectDataset1, "Dataset 1: nodes or nodes+network", vlayout1)
        self.text3, groupbox1 = self.addFileSlot(self.selectDataset3, "Dataset 1: network (optional)", vlayout1)

        groupbox1 = QtWidgets.QGroupBox()
        groupbox1.setLayout(vlayout1)
        vlayout.addWidget(groupbox1)

        #self.text2, groupbox1 = self.addFileSlot(self.selectImportFile, "Import file:", vlayout)

        # Add import file and filter region in the same layout
        vlayout2 = QtWidgets.QVBoxLayout()
        self.text2, groupbox2 = self.addFileSlot(self.selectDataset2, "Dataset 2: nodes", vlayout2)
        self.text4, groupbox2 = self.addFileSlot(self.selectDataset4, "Dataset 2: network (optional)", vlayout2)
        #self.filterProvince = self.addFilterWidget("Filter province:", vlayout2)
        groupbox = QtWidgets.QGroupBox()
        groupbox.setLayout(vlayout2)
        vlayout.addWidget(groupbox)

        vlayout3 = QtWidgets.QVBoxLayout()
        self.filterProvince = self.addFilterWidget("Filter province:", vlayout3)
        groupbox3 = QtWidgets.QGroupBox()
        groupbox3.setLayout(vlayout3)
        vlayout.addWidget(groupbox3)

        startButton = QtWidgets.QPushButton("Run")
        vlayout.addWidget(startButton)
        startButton.clicked.connect(self.startAnalysis)

    @QtCore.Slot()
    def selectOSM(self):
        self.osmFile, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self,
                "Select OSM file",
                filter="All Files (*);;OSM Files (*.osm)",
                selectedFilter="OSM Files (*.osm)")

        self.text1.setText(self.osmFile)

    @QtCore.Slot()
    def selectImportFile(self):
        self.importFile, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self,
                "Select import file",
                filter="All Files (*);;GeoJSON Files (*.geojson *.json)",
                selectedFilter="GeoJSON Files (*.geojson *.json)")

        self.text2.setText(self.importFile)

    @QtCore.Slot()
    def selectDataset1(self):
        self.osmFile, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self,
                "Select dataset 1",
                filter="All Files (*);;GeoJSON or OSM Files (*.geojson *.json *.osm)",
                selectedFilter="GeoJSON or OSM Files (*.geojson *.json *.osm)")

        self.text1.setText(self.osmFile)

    @QtCore.Slot()
    def selectDataset2(self):
        self.importFile_nodes, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self,
                "Select dataset 2",
                filter="All Files (*);;GeoJSON or OSM Files (*.geojson *.json *.osm)",
                selectedFilter="GeoJSON or OSM Files (*.geojson *.json *.osm)")

        self.text2.setText(self.importFile_nodes)

    @QtCore.Slot()
    def selectDataset3(self):
        self.osmFile_network, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self,
                "Select dataset 1 (network)",
                filter="All Files (*);;GeoJSON Files (*.geojson *.json)",
                selectedFilter="GeoJSON Files (*.geojson *.json)")

        self.text3.setText(self.osmFile_network)

    @QtCore.Slot()
    def selectDataset4(self):
        self.importFile_network, selectedFilter = QtWidgets.QFileDialog.getOpenFileName(self,
                "Select dataset 2 (network)",
                filter="All Files (*);;GeoJSON Files (*.geojson *.json)",
                selectedFilter="GeoJSON Files (*.geojson *.json)")

        self.text4.setText(self.importFile_network)

    @QtCore.Slot()
    def startAnalysis(self):
        print(self.osmFile)
        print(self.importFile_nodes)
        filterProvince = self.filterProvince.text()
        if len(filterProvince) == 0:
            filterProvince = None

        if self.osmFile is None:
            return -1

        if self.importFile_nodes is None:
            return -1

        self.runWindow = RunWindow(self.osmFile, self.importFile_nodes, self.osmFile_network, self.importFile_network, None, filterProvince)
        self.runWindow.resize(600, 400)
        self.runWindow.show()

