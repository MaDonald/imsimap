# Imports for GUI widgets 
from PyQt5.QtWidgets import (QFileDialog,
                              QApplication, 
                              QMainWindow, 
                              QAction,  
                              QTextEdit, 
                              QPushButton,
                              QLineEdit, 
                              QDialog,
                              QHBoxLayout, 
                              QVBoxLayout, 
                              QLabel, 
                              QWidget, 
                              QDoubleSpinBox, 
                              QTabWidget, 
                              QGroupBox, 
                              QMessageBox,
                              QTableWidget, 
                              QTableWidgetItem, 
                              QHeaderView, 
                              QListView,
                              QMenu, 
                              QAction, 
                              QSlider,
                              QComboBox
                              )  
# Imports for GUI items 
from PyQt5.QtGui import (QIcon, 
                         QTextCursor, 
                         QStandardItem, 
                         QStandardItemModel) 
# QtCore imports 
from PyQt5.QtCore import (QSize,
                          pyqtSignal, 
                          QObject, 
                          QThread,
                          Qt,pyqtSlot) 

# Other imports 
import subprocess 
import sys
from datetime import datetime
import csv 
import pytz
from PyQt5 import sip
import traceback 
from time import sleep
import json
import os
import re 
from grgsm_livemon import grgsm_livemon


class CustomStream(QObject):
    """
    This class is a custom output stream from the PyQt5 QObject. 
    It captures standard output or other text streams and redirect them.
    It emits a PyQt signal 'textWritten' whenever the write() method is called. This signal can be
    connected to any PyQt slot to perform real-time text updates in a PyQt application, such as
    updating a QTextEdit widget.
    Attributes:
        textWritten (pyqtSignal): A PyQt signal that is emitted when write() is called. The signal
                                  sends a string containing the text that was written.
                                  
    Methods:
        write(text: str): Emits the 'textWritten' signal, effectively broadcasting the 'text' to
                          any connected PyQt slot. 
    """
    textWritten = pyqtSignal(str)  

    def write(self, text):
        self.textWritten.emit(str(text))


class SavedLogsDialog(QDialog):
    """
    This is a modal for the display of saved logs. The input is the raw saved logs of previous runs of the program.
    Attributes:
        text_edit (QTextEdit): A QTextEdit widget that displays the logs. It is set to read-only mode.
        
    Methods:
        __init__(logs: str, parent=None): Initializes the dialog, sets its title, dimensions, and layout.
                                          Takes the logs as a string to be displayed in the QTextEdit widget.
    """
    def __init__(self, logs, parent=None):
        super(SavedLogsDialog, self).__init__(parent)
        self.setWindowTitle("Saved Logs")
        # Set the initial dimensions
        self.resize(500, 400)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setPlainText(logs)
        
        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        
        self.setLayout(layout) 

class OutputReader(QThread):
    """
    A PyQt5 QThread subclass that reads the output of a command and emits signals.
    
    Attributes:
        output_signal: Signal emitted when a new line of output is read.
        error_signal: Signal emitted when an exception occurs.
        
    Methods:
        run(): The main loop that reads the command's output and emits signals.
    """
    output_signal = pyqtSignal(str)
    error_signal = pyqtSignal(str)

    def __init__(self, command):
        super(OutputReader, self).__init__()
        self.command = command

    def run(self):
        while True:
            try:
                for line in runProcess(self.command):
                    try:
                        decoded_line = line.decode('utf-8').strip()
                    except UnicodeDecodeError:
                        decoded_line = line.decode('utf-8', errors='ignore').strip()  # Ignore decoding errors

                    if decoded_line and 'CellId' not in decoded_line:
                        self.output_signal.emit(decoded_line)
                        try: 
                            sys.stdout.flush()
                        except:
                            pass
            except Exception as e: 
                #self.error_signal.emit(str(e))
                pass 

def runProcess(exe):    
    """
    Generator function that runs a subprocess and yields its output line by line.
    
    Args:
        exe (str): The command to execute.
        
    Yields:
        str: A line of output or an error message.
    """
    try:
        p = subprocess.Popen(exe, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            retcode = p.poll()
            line = p.stdout.readline()
            yield line
            if retcode is not None:
                if retcode != 0:
                    err = p.stderr.read().decode('utf-8', 'ignore').strip()
                    if err:
                        yield f"Error: {err}"
                break
            sleep(0.1)  # Reduce CPU usage
    except Exception as e:
        yield f"Exception: {e}"
        
class CustomListView(QListView):
    """
    Custom QListView class that handles right-click events to select items.
    """
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            index = self.indexAt(event.pos())
            if index.isValid():
                self.setCurrentIndex(index)


class IMSITableDialog(QDialog):
    """
    A QDialog subclass for displaying captured IMSIs in a table format.
    
    Attributes:
        table (QTableWidget): The table widget where IMSIs are displayed.
        
    Methods:
        __init__(self, logs, headers, parent=None): Constructor that initializes the dialog, table, and headers.
        populate_table(self, logs): Fills the table with IMSI data from the logs.
        add_row(self, fields): Inserts a new row into the table with the given fields.
    """ 
    def __init__(self, logs, headers, parent=None):
        super(IMSITableDialog, self).__init__(parent)
        self.setWindowTitle("Captured IMSIs")
        # Set the initial dimensions
        self.resize(700, 500)
        self.table = QTableWidget(self)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        
        self.setLayout(layout)
        
        self.populate_table(logs)
    def populate_table(self, logs):
        lines = logs.split('\n')
        for line in lines:
            if line.count(';') >= 6 and 'CellId' not in line:
                fields = line.split(';')
                self.add_row(fields)
                
    def add_row(self, fields):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        for i, field in enumerate(fields[1:]):  # Skip the first field [1:]
            item = QTableWidgetItem(str(field).strip())
            self.table.setItem(row_position, i, item) 

# Functions for edit menu 
def cut_text():
    """
    Cuts the selected text from the currently focused QTextEdit widget.
    """
    focused_widget = QApplication.focusWidget()
    
    if focused_widget is None:
        print("No widget is currently focused.")
        return
    
    if isinstance(focused_widget, QTextEdit):
        focused_widget.cut()
    else:
        print(f"The focused widget is not a QTextEdit but a {type(focused_widget)}.")


def copy_text():
    """
    Copies the selected text from the currently focused QTextEdit widget.
    """
    focused_widget = QApplication.focusWidget()
    
    if focused_widget is None:
        print("No widget is currently focused.")
        return
    
    if isinstance(focused_widget, QTextEdit):
        focused_widget.copy()
    else:
        print(f"The focused widget is not a QTextEdit but a {type(focused_widget)}.")


def paste_text():
    """
    Pastes the clipboard content into the currently focused QTextEdit widget.
    """
    focused_widget = QApplication.focusWidget()
    
    if focused_widget is None:
        print("No widget is currently focused.")
        return
    
    if isinstance(focused_widget, QTextEdit):
        focused_widget.paste()
    else:
        print(f"The focused widget is not a QTextEdit but a {type(focused_widget)}.")


class IMSIMAP(QMainWindow):
    """
    The main application window for IMSI mapping. Contains all the widgets of the GUI. 
    """
    def __init__(self):
        super().__init__()
        try:
            # Instantiate grgsm_livemon 
            self.grgsm_instance = grgsm_livemon(args="", collector="localhost", collectorport='4729', fc=943.203831e6, gain=50, osr=4, ppm=0, samp_rate=2000000.052982, serverport='4730', shiftoff=400e3)

            # SCANS TAB INITIALIZATIONS 
            # Initialize the QStandard Item Model
            self.scan_model = QStandardItemModel()

            #Initialize the custom list view 
            self.scan_list_view = CustomListView()
            
            # Set the model for the scan_list_view
            self.scan_list_view.setModel(self.scan_model)

            # Populate the "Scans" tab
            self.populate_scans_tab() 


            # COMMAND TEXT BOX INITIALIZATIONS 
            # Create the text box and set placeholder text
            self.command_textbox = QTextEdit()
            self.update_command_textbox()  # Initialize with the current command

            # Create a list to hold the new windows <-- If you want to open multiple windows, in case of multiple hardware #Not working yet coz only 1 dongle 
            self.new_windows = [] 


            # SET THE MAIN APP WINDOW 
            # Set window title, icon, and window size 
            self.setWindowTitle("IMSIMAP")
            self.setWindowIcon(QIcon("images/icon_imsi_bin.jpg"))
            self.setGeometry(200, 200, 1200, 800) 

            # Create a central widget and set the layout
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            self.top_layout = QVBoxLayout(central_widget)


            # Create menu bar
            menu_bar = self.menuBar()
            # Create 'File' menu and its actions
            file_menu = menu_bar.addMenu("File")
            open_another_window = QAction("Open another window", self)
            open_another_window.triggered.connect(self.open_another_window)

            close_current_window = QAction("Close current window", self)
            close_current_window.triggered.connect(self.close_current_window)

            quit_application = QAction("Quit Application", self)
            quit_application.triggered.connect(self.quit_application)

            file_menu.addActions([open_another_window, close_current_window, quit_application])

            # Create 'Scan' menu and its actions
            scan_menu = menu_bar.addMenu("Scan")
            start_capture = QAction("Start capture", self)
            start_capture.triggered.connect(self.start_capture)

            stop_capture = QAction("Stop capture", self)
            stop_capture.triggered.connect(self.stop_capture)

            save_capture = QAction("Save capture", self)
            save_capture.triggered.connect(self.save_capture)

            scan_menu.addActions([start_capture, stop_capture, save_capture])


            # Create 'Edit' menu and its actions
            edit_menu = menu_bar.addMenu("Edit")
            cut_action = QAction("Cut", self)
            copy_action = QAction("Copy", self)
            paste_action = QAction("Paste", self)

            # Connect the actions to the functions
            cut_action.triggered.connect(cut_text)
            copy_action.triggered.connect(copy_text)
            paste_action.triggered.connect(paste_text)
            edit_menu.addActions([cut_action, copy_action, paste_action])


            # Create 'Help' menu and its actions
            help_menu = menu_bar.addMenu("Help")

            # Help 
            help_action = QAction("Help", self)
            help_action.triggered.connect(self.show_help)  

            # Tutorial 
            tutorial_action = QAction("Tutorial", self)
            tutorial_action.triggered.connect(self.show_tutorial)  

            # Report Bug 
            report_bug = QAction("Report a Bug", self)
            report_bug.triggered.connect(self.report_bug)  


            # About 
            about_action = QAction("About", self)
            about_action.triggered.connect(self.show_about)

            # Add actions to the Help menu
            help_menu.addActions([help_action, tutorial_action, report_bug,  about_action])


            # NOW THE MAIN WINDOW CONTENT - THE REAL STUFF 
            # Create a horizontal layout for the first row
            row_layout = QHBoxLayout()

            # Create a label for the target frequency
            freq_label = QLabel("Target Frequency (Hz)") 
            row_layout.addWidget(freq_label)


            # Create a QSlider for frequency
            self.freq_slider = QSlider(Qt.Horizontal)
            self.freq_slider.setMinimum(800000000)  # 800 MHz scaled by 1e6
            self.freq_slider.setMaximum(1990000000)  # 1990 MHz scaled by 1e6
            self.freq_slider.setSingleStep(200000)  # 0.2 MHz scaled by 1e6
            self.freq_slider.setValue(int(self.grgsm_instance.fc))  # Initial value already in Hz
            self.freq_slider.valueChanged.connect(self.set_frequency_in_grgsm_slider)
            # Synchronize with the command text box 

            self.freq_slider.valueChanged.connect(self.update_command_textbox)

            row_layout.addWidget(self.freq_slider, 10)

            # Create a QLineEdit for manual frequency input
            self.freq_input = QLineEdit()
            self.freq_input.setPlaceholderText("943203831")  
            self.freq_input.textChanged.connect(self.set_frequency_in_grgsm_text)
            row_layout.addWidget(self.freq_input)


            # Create buttons with icons
            button_height = 40  
            icon_size = QSize(button_height, button_height)  # Make the icon size the same as the button height

            # Start button - of course :) 
            start_button = QPushButton()
            start_button.setIcon(QIcon('icons/green.png')) #images/start_capture
            start_button.setIconSize(icon_size)
            start_button.setMinimumHeight(button_height)
            start_button.setToolTip('Start scan')

            # Stop cature button 
            stop_button = QPushButton()
            stop_button.setIcon(QIcon('icons/red.png')) #images/stop_capture
            stop_button.setIconSize(icon_size)
            stop_button.setMinimumHeight(button_height)
            stop_button.setToolTip('Stop scan')

            # Save capture, it saves the logs though. There is so much to save, the final output is much easier and smaller. 
            save_button = QPushButton()
            save_button.setIcon(QIcon('icons/save.png'))  #images/save_capture
            save_button.setIconSize(icon_size)
            save_button.setMinimumHeight(button_height)
            save_button.setToolTip('Save scan')

            # Connect the buttons to corresponding functions
            start_button.clicked.connect(self.save_all)
            stop_button.clicked.connect(self.stop_capture) 
            save_button.clicked.connect(self.save_capture)

            # Add the buttons to the layout, they should have the same size and stretch 
            row_layout.addWidget(start_button, 1)
            row_layout.addWidget(stop_button, 1)
            row_layout.addWidget(save_button, 1)

            # Add the row layout to the top layout
            self.top_layout.addLayout(row_layout)


            # Create a horizontal layout for the second row
            second_row_layout = QHBoxLayout()

            # Create QGroupBox for each section
            config_group = QGroupBox("Config")   # Config -> Configuration 
            scope_group = QGroupBox("Scope")

            # Create vertical layouts for each column
            config_layout = QVBoxLayout()
            scope_layout = QVBoxLayout()

            # Create a QDoubleSpinBox for Gain
            self.gain_spinbox = QDoubleSpinBox()
            self.gain_spinbox.setMinimum(0.0)
            self.gain_spinbox.setMaximum(100.0)
            self.gain_spinbox.setSingleStep(0.5)  
            self.gain_spinbox.setDecimals(1) 
            self.gain_spinbox.setValue(self.grgsm_instance.gain)  
            self.gain_spinbox.valueChanged.connect(self.set_gain_in_grgsm)  # Handle value changes 

            # Create a QDoubleSpinBox for PPM
            self.ppm_spinbox = QDoubleSpinBox()
            self.ppm_spinbox.setMinimum(-150.0)
            self.ppm_spinbox.setMaximum(150.0)
            self.ppm_spinbox.setSingleStep(0.1)  
            self.ppm_spinbox.setDecimals(1) 
            self.ppm_spinbox.setValue(self.grgsm_instance.ppm) 
            self.ppm_spinbox.valueChanged.connect(self.set_ppm_in_grgsm)  # Handle value changes
            row_layout.addWidget(self.ppm_spinbox)

            # Also update the command text box with those value changes so we know the current command the program is executing 
            self.gain_spinbox.valueChanged.connect(self.update_command_textbox)
            self.ppm_spinbox.valueChanged.connect(self.update_command_textbox) 

            # Add labels and spinboxes to Config layout
            config_layout.addWidget(QLabel("Gain:"))
            config_layout.addWidget(self.gain_spinbox)
            config_layout.addWidget(QLabel("PPM:"))
            config_layout.addWidget(self.ppm_spinbox) 


            # Create a horizontal layout for the third row inside Config
            third_row_layout = QHBoxLayout()

            # Create a label for the text box
            command_label = QLabel("Command:")
            third_row_layout.addWidget(command_label)


            self.command_textbox.setPlaceholderText("imsimap -f 943203831")
            self.command_textbox.setReadOnly(True)
            self.command_textbox.setFixedHeight(80)  
            # Add the text box to the layout
            third_row_layout.addWidget(self.command_textbox)

            # Add the third row layout to the Config layout
            config_layout.addLayout(third_row_layout)

            # Create a QWidget for the scope
            scope_widget = sip.wrapinstance(self.grgsm_instance.qtgui_freq_sink_x_0.qwidget(), QWidget)

            # Add the QWidget to the scope_layout
            scope_layout.addWidget(scope_widget)

            # Set the layout for scope_group
            scope_group.setLayout(scope_layout)

            # Set the layouts for each QGroupBox
            config_group.setLayout(config_layout)
            scope_group.setLayout(scope_layout)

            # Add the QGroupBoxes to the horizontal layout
            second_row_layout.addWidget(config_group,1)
            second_row_layout.addWidget(scope_group,1)

            # Add the second row layout to the main layout
            self.top_layout.addLayout(second_row_layout)

            # Create a QTabWidget for the last row
            self.tabs = QTabWidget()

            # Create QTextEdits for the logs tab/output <- to see what is going on with the program 
            self.output_text_edit = QTextEdit()

            # Create a QWidget as a container for the "Captured IMSIs" tab
            imsi_tab_container = QWidget()
            
            # Create a QTableWidget for the "Captured IMSIs" tab
            self.imsi_table = QTableWidget()
            self.imsi_table.setRowCount(0)  # Initially, no rows
            self.imsi_table.setColumnCount(11)  # Number of columns 

            # Set the header labels
            #header_labels = ["Nb IMSI", "TMSI-1", "TMSI-2", "IMSI", "Country", "Brand", "Operator", "MCC", "MNC", "LAC", "CellId", "Timestamp"]
            header_labels = ["TMSI-1", "TMSI-2", "IMSI", "Country", "Brand", "Operator", "MCC", "MNC", "LAC", "CellId", "Timestamp"]
            self.imsi_table.setHorizontalHeaderLabels(header_labels)

            # Freeze the header (make it unscrollable)
            self.imsi_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            # Create the button for exporting the table data 
            self.export_button = QPushButton('Export Table')
            self.export_button.clicked.connect(self.export_table)

            # Create a vertical layout for the tab's 2 widgets -> table, export button 
            self.layout_table = QVBoxLayout()

            # Add the table and button to the layout
            self.layout_table.addWidget(self.imsi_table)
            self.layout_table.addWidget(self.export_button)

            # Set the layout for the container
            imsi_tab_container.setLayout(self.layout_table)

            # Create a QWidget as a container for the "Scans" tab
            scans_tab_container = QWidget()

            # Create a QVBoxLayout for the container
            scans_layout = QVBoxLayout()

            # Add the QListView to the layout
            scans_layout.addWidget(self.scan_list_view)

            # Set the layout for the container
            scans_tab_container.setLayout(scans_layout)

            
            #try:
            # Create an instance of OutputReader
            output_reader = OutputReader(["python3", "-u", "simple_IMSI-catcher.py"])  # Run a parallel process for decoding received data 

            # Connect the output_signal to append text to the QTextEdit in the "Logs" tab
            output_reader.output_signal.connect(self.output_text_edit.append)
            output_reader.error_signal.connect(self.output_text_edit.append)  
            output_reader.output_signal.connect(self.update_table) 
            output_reader.start()
            
            # Add tabs of the last row 
            self.tabs.addTab(self.output_text_edit, "Logs")
            self.tabs.addTab(imsi_tab_container, "Captured IMSIs")  
            self.tabs.addTab(scans_tab_container, "Scans") 


            # Redirect stdout and stderr
            sys.stdout = CustomStream(textWritten=self.onUpdateText)
            sys.stderr = CustomStream(textWritten=self.onUpdateText)

            # Add the QTabWidget to the main layout
            self.top_layout.addWidget(self.tabs)

            # Set the stretch factor to make the tabs occupy nearly half of the available space
            self.top_layout.setStretchFactor(self.tabs, 1)
            QApplication.instance().aboutToQuit.connect(self.save_final_logs) 

            # Show the window
            self.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred during App initialization: {e}")
            raise  

    # MEMBER FUNCTIONS

    def set_frequency_in_grgsm_slider(self, value):
        new_frequency = value
        #new_frequency = value / 1e6  # Convert to MHz (since we scaled by 1e6)
        if self.set_frequency_in_grgsm(new_frequency):
            self.freq_input.setText(str(new_frequency))  # Update the text box with 6 decimal places


    def set_frequency_in_grgsm_text(self):
        try:
            new_frequency = float(self.freq_input.text())  # Convert to Hz
            #new_frequency = float(self.freq_input.text()) * 1e6  # Convert to Hz
            if self.set_frequency_in_grgsm(new_frequency):
                self.freq_slider.setValue(int(new_frequency))  # Update the slider, scaled by 1e6
        except ValueError:
            QMessageBox.critical(self, "Error", "Please enter a valid numerical frequency.")

    # CONFIGURATION OF THE SCAN 
    def set_frequency_in_grgsm(self, new_frequency):
        try:
            # Validate the frequency range
            if new_frequency < 800e6 or new_frequency > 1990e6:
                raise ValueError("Frequency out of valid range (800 MHz to 1990 MHz)")

            self.grgsm_instance.rtlsdr_source_0.set_center_freq((new_frequency-self.grgsm_instance.shiftoff), 0)
            self.grgsm_instance.qtgui_freq_sink_x_0.set_frequency_range(new_frequency, self.grgsm_instance.samp_rate)

        except ValueError as ve:
            QMessageBox.critical(self, "Error", f"ValueError: {ve}")
            return False

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")
            return False

        return True



    def set_gain_in_grgsm(self, value):
        self.grgsm_instance.set_gain(value)  # Update the gain
        self.grgsm_instance.set_gain_slider(value)  # Update the actual gain in the application


    def set_ppm_in_grgsm(self, value):
        self.grgsm_instance.set_ppm(value)  # Update the ppm
        self.grgsm_instance.set_ppm_slider(value)  # Update the actual ppm in the application

        
    def update_command_textbox(self):
        command_str = f"imsimap -f {self.grgsm_instance.fc} -g {self.grgsm_instance.gain} -p {self.grgsm_instance.ppm} --collector {self.grgsm_instance.collector} --collectorport {self.grgsm_instance.collectorport} --osr {self.grgsm_instance.osr} --samp_rate {self.grgsm_instance.samp_rate} --serverport {self.grgsm_instance.serverport} --shiftoff {self.grgsm_instance.shiftoff}"
        self.command_textbox.setPlainText(command_str)


    # MENU - File management/Window management 
    def open_another_window(self):
        try:
            new_window = IMSIMAP()
            new_window.show()
            # Store the new window so it won't be garbage-collected
            self.new_windows.append(new_window)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while opening a new window: {e}")
            traceback.print_exc()   


    def close_current_window(self):
        self.save_final_logs()
        self.close()

    def quit_application(self):
        self.save_final_logs() 
        QApplication.quit()


    # SCANS - START, STOP, SAVE 
    def save_capture(self):
        try:
            # Check if 'Captures' folder exists, if not, create one
            if not os.path.exists('Captures'):
                os.makedirs('Captures')

            # Get the window ID
            win_id = self.winId()

            # Get QScreen object
            screen = QApplication.primaryScreen()

            # Capture the screen
            screenshot = screen.grabWindow(win_id)

            # Generate file name
            fname = QFileDialog.getSaveFileName(self, 'Save file', 'Captures/screenshot.png')

            if fname[0]:
                screenshot.save(fname[0], 'png')
                print("\nCapture saved")
        except Exception as e:
            print("\nCouldn't save capture:", e)


    def save_all(self):
        self.add_new_scan()  
        self.start_capture()


    def start_capture(self):
        try:
            # Get the current date and time in W. Europe Daylight Time
            tz = pytz.timezone('Europe/Berlin')  
            current_time = datetime.now(tz)
            formatted_time = current_time.strftime('%Y-%m-%d %H:%M %Z')

            # Append the timestamp to the log tab
            self.output_text_edit.append(f"Starting IMSI MAP version 1.0 scan at {formatted_time}")

            self.grgsm_instance.start() 

            print('\nCapture started')  

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while starting the capture: {e}")
            traceback.print_exc()

    def stop_capture(self):
        try:
            self.grgsm_instance.stop()  # Stop the GNU Radio flowgraph
            self.grgsm_instance.wait() 
            print("\nCapture stopped") 
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while stopping the capture: {e}")
            traceback.print_exc()




    def onUpdateText(self, text):
        cursor = self.output_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(text)
        self.output_text_edit.setTextCursor(cursor)
        self.output_text_edit.ensureCursorVisible()


    # SCANS TAB 
    def populate_scans_tab(self):
        # Load the scan data
        scan_data = self.load_scan_data()
        
        # Clear existing items from the model
        self.scan_model.clear()
        
        for timestamp, data in scan_data.items():
            # Create a QStandardItem with the timestamp and frequency
            frequency = data.get('frequency', 'Unknown')
            item = QStandardItem(f"Scan at {timestamp} on {frequency} Hz")
            
            # Add the item to the model
            self.scan_model.appendRow(item)
            
            # Add a context menu to the item for additional actions
            self.scan_list_view.setContextMenuPolicy(Qt.CustomContextMenu)
            self.scan_list_view.customContextMenuRequested.connect(self.show_scan_context_menu)


    def load_scan_data(self):
        # Check if the 'logs' folder exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Define the path to the scan data file
        scan_data_file = 'logs/scan_data.json'
        
        # Check if the scan data file exists
        if not os.path.exists(scan_data_file):
            return {}  # Return an empty dictionary if the file doesn't exist
        
        # Load the scan data from the file
        with open(scan_data_file, 'r') as f:
            scan_data = json.load(f)
            
        return scan_data

    def add_new_scan(self):
        # Get the current timestamp and frequency
        tz = pytz.timezone('Europe/Berlin')
        current_time = datetime.now(tz)
        formatted_time = current_time.strftime('%Y-%m-%d %H:%M %Z')
        frequency = self.grgsm_instance.fc
        ppm = self.grgsm_instance.ppm
        gain = self.grgsm_instance.gain
        # Get the logs
        logs = self.output_text_edit.toPlainText()
        # Create a new scan item
        scan_item = QStandardItem(f"Scan at {formatted_time} on {frequency} Hz")
        
        # Add the item to the model
        self.scan_model.appendRow(scan_item)
        
        # Load existing scan data
        scan_data = self.load_scan_data()
        
        scan_data[formatted_time] = {
            'frequency': frequency,
            'ppm': ppm,
            'gain': gain,
            'logs': logs
        } 
        # Save updated scan data
        self.save_scan_data(scan_data)

    def save_scan_data(self, scan_data):
        with open('logs/scan_data.json', 'w') as f:
            json.dump(scan_data, f)


    def show_scan_context_menu(self, position):
        # Create a QMenu
        context_menu = QMenu()
        
        # Create actions
        view_log_action = QAction("View Log", self)
        view_table_action = QAction("View Table", self)
        repeat_scan_action = QAction("Repeat Scan", self)
        export_data_action = QAction("Export Data", self)
        
        # Connect actions to functions
        view_log_action.triggered.connect(self.view_log)
        view_table_action.triggered.connect(self.view_table)
        repeat_scan_action.triggered.connect(self.repeat_scan)
        export_data_action.triggered.connect(self.export_data)
        
        # Add actions to the menu
        context_menu.addAction(view_log_action)
        context_menu.addAction(view_table_action)
        context_menu.addAction(repeat_scan_action)
        context_menu.addAction(export_data_action)
        
        # Show the menu
        context_menu.exec_(self.scan_list_view.viewport().mapToGlobal(position))
        


    def view_log(self):
        # Get the selected scan timestamp from the QListView
        selected_index = self.scan_list_view.currentIndex()
        selected_text = selected_index.data()
        
        # Extract the timestamp from the selected_text
        timestamp_pattern = r"Scan at (.+?) on"
        timestamp = re.search(timestamp_pattern, selected_text).group(1)
        
        # Load existing scan data
        scan_data = self.load_scan_data()
        
        # Get the logs for the selected timestamp
        logs = scan_data.get(timestamp, {}).get('logs', "No logs available.")
        
        # Create and show the dialog
        dialog = SavedLogsDialog(logs, self)
        dialog.exec_()

    def view_table(self):
        # Get the selected scan timestamp from the QListView
        selected_index = self.scan_list_view.currentIndex()
        selected_text = selected_index.data()
        
        # Extract the timestamp from the selected_text
        timestamp_pattern = r"Scan at (.+?) on"
        timestamp = re.search(timestamp_pattern, selected_text).group(1)
        
        # Load existing scan data
        scan_data = self.load_scan_data()
        
        # Get the logs for the selected timestamp
        logs = scan_data.get(timestamp, {}).get('logs', "No logs available.")
        
        # Define headers
        headers = [ "TMSI-1", "TMSI-2", "IMSI", "Country", "Brand", "Operator", "MCC", "MNC", "LAC", "CellId", "Timestamp"]
        
        # Create and show the dialog
        dialog = IMSITableDialog(logs, headers, self)
        dialog.exec_()


    def extract_params_from_logs(self, logs):
        try:
            frequency_str = logs['frequency']
            gain_str = logs['gain']
            ppm_str = logs['ppm']

            # Convert to float
            frequency = int(frequency_str) if frequency_str is not None else None
            gain = float(gain_str) if gain_str is not None else None
            ppm = float(ppm_str) if ppm_str is not None else None

            return frequency, gain, ppm
        except (ValueError, TypeError) as e:
            QMessageBox.critical(self, "Error", f"An error occurred while converting parameters to float: {e}")
            traceback.print_exc()
            return None, None, None
    

    def update_spinboxes(self, frequency, gain, ppm):
        self.freq_slider.setValue(frequency)  
        self.gain_spinbox.setValue(gain) 
        self.ppm_spinbox.setValue(ppm) 
    
    def set_params_in_context(self, frequency, gain, ppm):
        self.grgsm_instance.fc = frequency
        self.grgsm_instance.gain = gain
        self.grgsm_instance.ppm = ppm


    def repeat_scan(self):

        try:
            # Get the selected scan timestamp from the QListView
            selected_index = self.scan_list_view.currentIndex()
            selected_text = selected_index.data()
            
            # Extract the timestamp from the selected_text
            timestamp_pattern = r"Scan at (.+?) on"
            timestamp = re.search(timestamp_pattern, selected_text).group(1)

            # Load existing scan data
            scan_data = self.load_scan_data()
            # Get the logs for the selected timestamp
            logs = scan_data.get(timestamp, {})

            # Extract the parameters
            frequency, gain, ppm = self.extract_params_from_logs(logs)
            
            if frequency is None or gain is None or ppm is None:
                raise ValueError("One or more scan parameters could not be extracted or converted to float.")
            
            self.set_params_in_context(frequency, gain, ppm)
            self.update_spinboxes(frequency, gain, ppm)
            self.start_capture()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while repeating the scan: {e}")
            traceback.print_exc()


    def export_data(self):
        # Get the selected scan timestamp from the QListView
        selected_index = self.scan_list_view.currentIndex()
        selected_text = selected_index.data()
        
        # Extract the timestamp from the selected_text
        timestamp_pattern = r"Scan at (.+?) on"
        timestamp = re.search(timestamp_pattern, selected_text).group(1)
        
        # Load existing scan data
        scan_data = self.load_scan_data()
        
        # Get the parameters and logs for the selected timestamp
        params = scan_data.get(timestamp, {})
        logs = params.get('logs', "No logs available.")
        
        # Open a text file for writing
        with open(f"exported_scan_data_{timestamp}.txt", "w") as f:
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Frequency: {params.get('frequency')}\n")
            f.write(f"PPM: {params.get('ppm')}\n")
            f.write(f"Gain: {params.get('gain')}\n")
            f.write("Logs:\n")
            f.write(logs)
            f.write("\nCaptured IMSIs:\n")
            
            # Write table data
            for row in range(self.imsi_table.rowCount()):
                f.write('\t'.join([self.imsi_table.item(row, col).text() if self.imsi_table.item(row, col) else '' for col in range(self.imsi_table.columnCount())]) + '\n')

        QMessageBox.information(self, 'Success', 'Data exported successfully to working directory.')


    def show_help(self):
        QMessageBox.information(self, "Help", "For help, contact the author at macdonald.phiri@studenti.unitn.it.")

    def show_tutorial(self):
        QMessageBox.information(self, "Tutorial", "Developed in python, you need python installed in a Linux environment to use this software. To capture IMSIs, you specify a target frequency and other\
                                parameters and hit the start scan button. This will capture the traffic in the area and decode it. Giving as output the IMSI numbers and other information. \
                                This information or logs of the scan can be exported for further analysis. Please note that tests were conducted using the Rafael RTL-SDR USB stick and receiver. Other similar hardware\
                                should work seamlessly. Remember to load your hardware in Linux before running the program. You may use the lsusb command to list available devices at the USB interfaces.  ")

    def report_bug(self):
        QMessageBox.information(self, "Report a Bug", "Report any bugs at macdonald.phiri@studenti.unitn.it.")

    def show_about(self):
        QMessageBox.information(self, "About", "This software is a user-friendly graphical interface for detecting IMSI numbers of mobile devices in a GSM network. This can be useful in events such as \
                                disaster response, forensics, urban planning etc") 


    # Function to add a new row of data
    def add_row(self, data):
        row_position = self.imsi_table.rowCount()
        self.imsi_table.insertRow(row_position)
        for i, field in enumerate(data[1:]):  # Skip the first field
            item = QTableWidgetItem(str(field))
            self.imsi_table.setItem(row_position, i, item)
        self.imsi_table.scrollToBottom()  # Auto-scroll to the new row


    # Slot function to update the QTableWidget
    def update_table(self, output_line):
        # Check if the line contains data (at least 6 semicolons)
        if output_line.count(';') >= 6 and 'CellId' not in output_line:
            # Split the line into fields
            fields = output_line.split(';')
            
            # Add a new row to the table
            row_position = self.imsi_table.rowCount()
            self.imsi_table.insertRow(row_position)
            
            # Populate the new row with data, skipping the first field
            for i, field in enumerate(fields[1:]):  # Skip the first field
                item = QTableWidgetItem(field)
                self.imsi_table.setItem(row_position, i, item)


    @pyqtSlot()
    def save_final_logs(self):
        logs = self.output_text_edit.toPlainText() 

    def export_table(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Save File", "", "CSV Files (*.csv);;TXT Files (*.txt);;SQLITE Files (*.sqlite)", options=options)
        
        if file_name:
            if file_name.endswith('.csv'):
                with open(file_name, 'w', newline='') as csv_file:
                    writer = csv.writer(csv_file)
                    # Write header
                    writer.writerow([self.imsi_table.horizontalHeaderItem(i).text() for i in range(self.imsi_table.columnCount())])
                    # Write data
                    for row in range(self.imsi_table.rowCount()):
                        writer.writerow([self.imsi_table.item(row, col).text() if self.imsi_table.item(row, col) else '' for col in range(self.imsi_table.columnCount())])
            
            elif file_name.endswith('.txt'):
                with open(file_name, 'w') as txt_file:
                    # Write header
                    txt_file.write('\t'.join([self.imsi_table.horizontalHeaderItem(i).text() for i in range(self.imsi_table.columnCount())]) + '\n')
                    # Write data
                    for row in range(self.imsi_table.rowCount()):
                        txt_file.write('\t'.join([self.imsi_table.item(row, col).text() if self.imsi_table.item(row, col) else '' for col in range(self.imsi_table.columnCount())]) + '\n')
            
            elif file_name.endswith('.sqlite'):
                import sqlite3  # Import SQLite
                
                # Connect to SQLite database
                sqlite_con = sqlite3.connect(file_name)
                sqlite_con.text_factory = str
                sqlite_cur = sqlite_con.cursor()
                
                # Create table
                sqlite_cur.execute("CREATE TABLE IF NOT EXISTS observations(stamp datetime, tmsi1 text, tmsi2 text, imsi text, imsicountry text, imsibrand text, imsioperator text, mcc integer, mnc integer, lac integer, cell integer);")
                
                # Insert data
                for row in range(self.imsi_table.rowCount()):
                    data = [self.imsi_table.item(row, col).text() if self.imsi_table.item(row, col) else None for col in range(self.imsi_table.columnCount())]
                    sqlite_cur.execute("INSERT INTO observations (stamp, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);", data)
                
                # Commit changes and close connection
                sqlite_con.commit()
                sqlite_con.close()

            QMessageBox.information(self, 'Success', 'Table exported successfully.')

    # FUNCTIONS FOR USING FIXED STATIC FREQUENCIES IN SCANS 
    def handle_freq_options(self):
        option = self.freq_options_combo.currentText()
        if option == "Choose":
            self.load_frequencies_from_file()
            self.freq_input.hide()
            self.freq_save_button.hide()
        elif option == "Add":
            self.freq_input.show()
            self.freq_save_button.show()
        # You could add known frequencies to a file and simply chose frequencies to scan any time. Still being developed. #TBD 
        '''
        # Create a QComboBox for Frequency Options
        self.freq_options_combo = QComboBox()
        self.freq_options_combo.addItem("Choose")
        self.freq_options_combo.addItem("Add")
        self.freq_options_combo.currentIndexChanged.connect(self.handle_freq_options)

        # Create another QComboBox for displaying available frequencies
        self.freq_combo = QComboBox()
        self.freq_combo.currentIndexChanged.connect(self.set_frequency_in_grgsm)
        self.freq_combo.show() 

        # Create a QLineEdit for adding new frequencies
        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText("Enter new frequency")
        self.freq_input.hide() 

        # Create a QPushButton to save the new frequency
        self.freq_save_button = QPushButton("Save")
        self.freq_save_button.clicked.connect(self.save_new_frequency)
        self.freq_save_button.hide() 

        config_layout.addWidget(QLabel("Saved Frequencies:")) 
        config_layout.addWidget(self.freq_options_combo)
        config_layout.addWidget(self.freq_combo)
        config_layout.addWidget(self.freq_input)
        config_layout.addWidget(self.freq_save_button)
        ''' 

            
    def load_frequencies_from_file(self):
        try:
            with open("frequencies.txt", "r") as f:
                frequencies = f.readlines()
            self.freq_combo.clear()
            self.freq_combo.addItems(frequencies)
        except FileNotFoundError:
            QMessageBox.critical(self, "Error", "Frequencies file not found.")

    def save_new_frequency(self):
        new_freq = self.freq_input.text()
        try:
            float_new_freq = float(new_freq)  
            with open("frequencies.txt", "a") as f:
                f.write(f"{float_new_freq}\n") 
            self.freq_combo.addItem(new_freq)  
            self.freq_input.clear()
        except ValueError: 
            QMessageBox.critical(self, "Error", "Please enter a valid numerical frequency.")

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        #app.setStyle('Fusion')  # Using built-in style 
        # Apply the custom style sheet
        stylesheet = '''
            QWidget {
                background-color: #FFFFFF;
                color: #000000;
            }
        ''' 
        app.setStyleSheet(stylesheet)
        window = IMSIMAP()
        sys.exit(app.exec_())
    except Exception as e:
        error_dialog = QMessageBox()
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("Runtime Error")
        error_dialog.setText(f"An error occurred during execution: {e}")
        error_dialog.setStandardButtons(QMessageBox.Ok)
        error_dialog.exec_()
        sys.exit(1)  # Exit the program with an error code
