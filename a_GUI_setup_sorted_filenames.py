import os
import subprocess
import argparse
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator, QBrush, QColor, QPixmap, QImage
from PyQt5.QtWidgets import (QWidget, QApplication, QGridLayout, QLineEdit,
                             QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QComboBox,
                             QMessageBox)

from tkinter import filedialog
from tkinter import *

sys.path.append(os.path.join(os.getcwd(), 'utilities'))
from utilities.a_driver_utilities import set_step_completed_in_progress_ini
from data_manager_v2 import DataManager
from metadata import ON_DOCKER, ROOT_DIR

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='GUI for sorting filenames')
parser.add_argument("stack", type=str, help="stack name")
args = parser.parse_args()
stack = args.stack

# Check if a sorted_filenames already exists
sfns_fp = DataManager.get_sorted_filenames_filename(stack=stack)
sfns_already_exists = os.path.exists(sfns_fp)

# Defining possible quality options for each slice
quality_options = ['unusable', 'blurry', 'good']

# Cannot assume we have the sorted_filenames file. Load images a different way
thumbnail_folder = os.path.join(ROOT_DIR, stack, 'preps', 'thumbnail')
sections_to_filenames = {}
fn_to_quality = {}
fn_list = os.listdir(thumbnail_folder)
fn_list.sort()
for i, img_name in enumerate(fn_list):
    print(img_name)
    sections_to_filenames[i] = img_name
    fn_to_quality[img_name] = 'good'


def get_thumbnail_img_fp_from_section(fn):
    img_fp = os.path.join(thumbnail_folder, fn)
    return img_fp


class ImageViewer(QGraphicsView):
    photoClicked = pyqtSignal(QPoint)

    def __init__(self, parent):
        super(ImageViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
            self._zoom = 0
        else:
            print('RECT IS NULL')

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInView()

    """
    EOD, 3/27/2020
    I can't find image or overlay, They are not assigned anywhere
    def paintOverlayImage(self, pixmap=None):
        painter = QPainter()
        painter.begin(image)
        painter.drawImage(0, 0, overlay)
        painter.end()
    """

    def wheelEvent(self, event):
        if self.hasPhoto():
            if event.delta() > 0:
                factor = 1.25
                self._zoom += 1
            else:
                factor = 0.8
                self._zoom -= 1
            if self._zoom > 0:
                self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0

    def toggleDragMode(self):
        if self.dragMode() == QGraphicsView.ScrollHandDrag:
            self.setDragMode(QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(QPoint(event.pos()))
        super(ImageViewer, self).mousePressEvent(event)


class QHLine(QFrame):
    def __init__(self):
        # https://doc.qt.io/qt-5/qframe.html
        # https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(5)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(5)


class init_GUI(QWidget):

    def __init__(self, parent=None):
        super(init_GUI, self).__init__(parent)
        self.font_h1 = QFont("Arial", 32)
        self.font_p1 = QFont("Arial", 16)
        self.valid_sections = sections_to_filenames
        self.valid_section_keys = sections_to_filenames.keys()
        self.curr_section_index = len(self.valid_section_keys) // 2
        self.prev_section_index = self.curr_section_index
        self.next_section_index = self.curr_section_index
        self.curr_section = self.valid_sections[self.curr_section_index]
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)
        # create a dataManager object
        self.dataManager = DataManager()
        self.initUI()

    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_body_upper = QGridLayout()
        self.grid_body = QGridLayout()
        self.grid_body_lower = QGridLayout()
        self.grid_bottom = QGridLayout()
        self.grid_blank = QGridLayout()

        # self.setFixedSize(1600, 1100)
        self.resize(1600, 1100)

        ### VIEWER ### (Grid Body)
        self.viewer = ImageViewer(self)
        self.viewer.photoClicked.connect(self.photoClicked)

        ### Grid TOP ###
        # Static Text Field (Title)
        self.e1 = QLineEdit()
        self.e1.setValidator(QIntValidator())
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont(self.font_h1)
        self.e1.setReadOnly(True)
        self.e1.setText("Setup Sorted Filenames")
        self.e1.setFrame(False)
        self.grid_top.addWidget(self.e1, 0, 0)
        # Button Text Field
        self.b_help = QPushButton("HELP")
        self.b_help.setDefault(True)
        self.b_help.setEnabled(True)
        self.b_help.clicked.connect(lambda: self.help_button_press(self.b_help))
        self.b_help.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,250);")
        self.grid_top.addWidget(self.b_help, 0, 1)

        ### Grid BODY UPPER ###
        # Static Text Field
        self.e4 = QLineEdit()
        self.e4.setAlignment(Qt.AlignCenter)
        self.e4.setFont(self.font_p1)
        self.e4.setReadOnly(True)
        self.e4.setText("Filename: ")
        # self.e4.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget(self.e4, 0, 2)
        # Static Text Field
        self.e5 = QLineEdit()
        self.e5.setAlignment(Qt.AlignCenter)
        self.e5.setFont(self.font_p1)
        self.e5.setReadOnly(True)
        self.e5.setText("Section: ")
        # self.e5.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget(self.e5, 0, 3)

        ### Grid BODY ###
        # Custom VIEWER
        self.grid_body.addWidget(self.viewer, 0, 0)

        ### Grid BODY LOWER ###
        # Vertical line
        self.grid_body_lower.addWidget(QVLine(), 0, 0, 1, 1)
        # Static Text Field
        self.e7 = QLineEdit()
        self.e7.setMaximumWidth(250)
        self.e7.setAlignment(Qt.AlignRight)
        self.e7.setReadOnly(True)
        self.e7.setText("Select section quality:")
        self.grid_body_lower.addWidget(self.e7, 0, 1)
        # Dropbown Menu (ComboBox) for selecting Stack
        self.dd = QComboBox()
        self.dd.addItems(quality_options)
        self.dd.currentIndexChanged.connect(self.updateDropdown)
        self.grid_body_lower.addWidget(self.dd, 0, 2)
        # Vertical line
        self.grid_body_lower.addWidget(QVLine(), 0, 3, 1, 1)
        # Button Text Field
        self.b_remove = QPushButton("Remove section")
        self.b_remove.setDefault(True)
        self.b_remove.setEnabled(True)
        self.b_remove.clicked.connect(lambda: self.buttonPress(self.b_remove))
        self.b_remove.setStyleSheet("color: rgb(0,0,0); background-color: #C91B1B;")
        self.grid_body_lower.addWidget(self.b_remove, 2, 1)
        # Button Text Field
        self.b_addPlaceholder = QPushButton("Add Placeholder as prev section")
        self.b_addPlaceholder.setDefault(True)
        self.b_addPlaceholder.setEnabled(True)
        self.b_addPlaceholder.clicked.connect(lambda: self.buttonPress(self.b_addPlaceholder))
        self.b_addPlaceholder.setStyleSheet("color: rgb(0,0,0); background-color: #41C91B;")
        self.grid_body_lower.addWidget(self.b_addPlaceholder, 2, 2)
        # Button Text Field
        self.b_left = QPushButton("<--   Move Section Left   <--")
        self.b_left.setDefault(True)
        self.b_left.setEnabled(True)
        self.b_left.clicked.connect(lambda: self.buttonPress(self.b_left))
        self.b_left.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,250,250);")
        self.grid_body_lower.addWidget(self.b_left, 0, 5)
        # Button Text Field
        self.b_right = QPushButton("-->   Move Section Right   -->")
        self.b_right.setDefault(True)
        self.b_right.setEnabled(True)
        self.b_right.clicked.connect(lambda: self.buttonPress(self.b_right))
        self.b_right.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,250,250);")
        self.grid_body_lower.addWidget(self.b_right, 0, 6)
        # Horozontal Line
        self.grid_body_lower.addWidget(QHLine(), 1, 0, 1, 7)
        # Button Text Field
        self.b_done = QPushButton("Finished")
        self.b_done.setDefault(True)
        self.b_done.setEnabled(True)
        self.b_done.clicked.connect(lambda: self.buttonPress(self.b_done))
        self.b_done.setStyleSheet("color: rgb(0,0,0); background-color: #dfbb19;")
        self.grid_body_lower.addWidget(self.b_done, 2, 6)

        # Grid stretching
        # self.grid_body_upper.setColumnStretch(0, 2)
        self.grid_body_upper.setColumnStretch(2, 2)
        # self.grid_body_lower.setColumnStretch(3, 1)

        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout(self.grid_top, 0, 0)
        self.supergrid.addLayout(self.grid_body_upper, 1, 0)
        self.supergrid.addLayout(self.grid_body, 2, 0)
        # self.supergrid.addLayout( self.grid_body_lower, 4, 0)
        self.supergrid.addWidget(QHLine(), 6, 0, 1, 2)
        # self.supergrid.addLayout( self.grid_bottom, 6, 0)
        self.supergrid.addLayout(self.grid_body_lower, 7, 0)
        self.supergrid.addWidget(QHLine(), 8, 0, 1, 2)

        # Set layout and window title
        self.setLayout(self.supergrid)
        self.setWindowTitle("Q")
        self.setCurrSection(self.curr_section_index)

        # Loads self.curr_section as the current image and sets all fields appropriatly
        # self.setCurrSection( self.curr_section )

    def help_button_press(self, button):
        info_text = "This GUI is used to align slices to each other. The shortcut commands are as follows: \n\n\
    -  `[`: Go back one section. \n\
    -  `]`: Go forward one section. \n\n"
        info_text += "Use the buttons on the bottom panel to move"

        QMessageBox.information(self, "Empty Field",
                                info_text)

    def updateDropdown(self):
        # Get dropdown selection
        dropdown_selection = self.dd.currentText()
        curr_fn = self.valid_sections[int(self.curr_section_index)]
        fn_to_quality[curr_fn] = dropdown_selection

    def load_sorted_filenames(self):
        #self.dataManager.generate_metadata_cache()
        self.valid_sections = self.dataManager.metadata_cache['sections_to_filenames'][stack]
        self.valid_section_keys = self.valid_sections.keys()
        self.curr_section_index = len(self.valid_section_keys) // 2
        self.curr_section = self.valid_sections[self.curr_section_index]
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)

        # Repopulate "fn_to_quality"
        fn_to_quality = {}
        for section, img_name in self.valid_sections.items():
            fn_to_quality[img_name] = 'good'

        self.setCurrSection(self.curr_section_index)

    def loadImage(self):
        curr_fn = self.valid_sections[int(self.curr_section_index)]

        if curr_fn == 'Placeholder':
            # Set a blank image if it is a placeholder
            img = np.zeros((100, 150, 3))
            img = np.array(img, dtype=np.uint8)

            height, width, channels = img.shape
            bytesPerLine = 3 * width
            qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)

            self.viewer.setPhoto(QPixmap(qImg))
        else:
            # Get filepath of "curr_section" and set it as viewer's photo
            img_fp = get_thumbnail_img_fp_from_section(curr_fn)
            self.viewer.setPhoto(QPixmap(img_fp))

    def photoClicked(self, pos):
        if self.viewer.dragMode() == QGraphicsView.NoDrag:
            print('%d, %d' % (pos.x(), pos.y()))

    def pixInfo(self):
        self.viewer.toggleDragMode()

    def keyPressEvent(self, event):
        try:
            key = event.key()
        except AttributeError:
            key = event

        if key == 91:  # [
            self.getPrevValidSection(self.curr_section_index)
            self.setCurrSection(self.prev_section_index)
        elif key == 93:  # ]
            self.getNextValidSection(self.curr_section_index)
            self.setCurrSection(self.next_section_index)
        else:
            print(key)

    def setCurrSection(self, section_index=-1):
        """
        Sets the current section to the section passed in.
        
        Will automatically update curr_section, prev_section, and next_section.
        Updates the header fields and loads the current section image.
        
        """
        if section_index == -1:
            section_index = self.curr_section_index

        # Update curr, prev, and next section
        self.curr_section_index = section_index
        self.curr_section = self.valid_sections[self.curr_section_index]
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)
        # Update the section and filename at the top
        self.updateCurrHeaderFields()
        # Update the quality selection in the bottom left
        self.updateQualityField()

        self.loadImage()

    def buttonPress(self, button):
        # Brighten an image
        if button in [self.b_left, self.b_right, self.b_addPlaceholder, self.b_remove]:
            # Get all relevant filenames
            curr_fn = self.valid_sections[int(self.curr_section_index)]
            prev_fn = self.valid_sections[int(self.prev_section_index)]
            next_fn = self.valid_sections[int(self.next_section_index)]

            # Move fn behind one section (100 -> 99)
            if button == self.b_left:
                # Swap mappings of 'curr_fn' and 'prev_fn'
                self.valid_sections[int(self.prev_section_index)] = curr_fn
                self.valid_sections[int(self.curr_section_index)] = prev_fn
                self.curr_section = self.getPrevValidSection(self.curr_section_index)

            # Move fn ahead one section (100 -> 101)
            elif button == self.b_right:
                # Swap mappings of 'curr_fn' and 'next_fn'
                self.valid_sections[int(self.next_section_index)] = curr_fn
                self.valid_sections[int(self.curr_section_index)] = next_fn
                self.curr_section = self.getNextValidSection(self.curr_section_index)

            elif button == self.b_addPlaceholder:
                # Set this current slice as a placeholder
                self.insertPlaceholder()
                # Go one section to the right
                self.keyPressEvent(93)
                pass

            elif button == self.b_remove:
                # Totally remove the current slice
                self.removeCurrSection()
                pass

            # Update the Viewer info and displayed image
            self.setCurrSection(self.curr_section_index)

        elif button == self.b_done:
            self.finished()

    def getNextValidSection(self, section_index):
        self.next_section_index = section_index + 1
        if self.next_section_index > len(self.valid_sections) - 1:
            self.next_section_index = 0
        self.next_section = self.valid_sections[self.next_section_index]
        return self.next_section

    def getPrevValidSection(self, section_index):
        self.prev_section_index = int(section_index) - 1
        if self.prev_section_index < 0:
            self.prev_section_index = len(self.valid_sections) - 1
        self.prev_section = self.valid_sections[self.prev_section_index]
        return self.prev_section

    def removeCurrSection(self):
        msgBox = QMessageBox()
        text = 'Are you sure you want to totally remove this section from this brain?\n\n'
        text += 'Warning: The image will be marked as irrelevant to the current brain!'
        msgBox.setText(text)
        msgBox.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        msgBox.addButton(QPushButton('No'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Yes'), QMessageBox.YesRole)
        ret = msgBox.exec_()
        # Cancel
        if ret == 0:
            pass
        # No
        elif ret == 1:
            pass
        # Yes
        elif ret == 2:
            print('aaa', self.valid_sections)
            curr_fn = self.valid_sections[int(self.curr_section_index)]
            # Remove the current section from "self.valid_sections
            try:
                del self.valid_sections[self.curr_section_index]
            except KeyError:
                print('Key {} missing'.format(self.curr_section_index))
            print('bbb', self.valid_sections)

            new_sections_to_filenames = sorted(self.valid_sections.values())

            for i, v in enumerate(new_sections_to_filenames):
                self.valid_sections[i] = v
            # Go back a section if you deleted the last section
            if int(self.curr_section_index) == len(self.valid_sections):
                self.curr_section_index = self.curr_section_index - 1

    def insertPlaceholder(self):
        new_sections_to_filenames = {}
        # Iterate through all sections
        for i in range(len(self.valid_section_keys) + 1):
            # If before the current section
            if i < self.curr_section_index:
                new_sections_to_filenames[i] = self.valid_sections[i]
            # If on the current section
            elif i == self.curr_section_index:
                new_sections_to_filenames[i] = 'Placeholder'
            # If after the current section
            else:
                new_sections_to_filenames[i] = self.valid_sections[i - 1]
        # Save changes
        self.valid_sections = new_sections_to_filenames
        self.valid_section_keys = self.valid_sections.keys()

    def updateCurrHeaderFields(self):
        self.e4.setText(str(self.valid_sections[self.curr_section_index]))
        self.e5.setText(str(self.curr_section))

    def updateQualityField(self):
        curr_fn = self.valid_sections[self.curr_section_index]
        print('curr_fn', curr_fn)
        print()
        if curr_fn == 'Placeholder':
            text = 'unusable'
        else:
            text = fn_to_quality[curr_fn]
        index = self.dd.findText(text, Qt.MatchFixedString)
        if index >= 0:
            self.dd.setCurrentIndex(index)

    def finished(self):
        set_step_completed_in_progress_ini(stack, '1-4_setup_sorted_filenames')

        write_results_to_sorted_filenames(self.valid_sections, fn_to_quality)

        # close_main_gui( ex )
        sys.exit(app.exec_())


def close_gui():
    # ex.hide()
    sys.exit(app.exec_())


def write_results_to_sorted_filenames(sections_to_filenames, fn_to_quality):
    """
    Create the sorted_filenames.txt file from the user's "sections_to_filenames".
    Determine quality of each slice from "fn_to_quality".
    
    Quality levels:
        - unusable: Mark as placeholder
        - good: Write to the file as usual
        - blurry: Write to a special file meant to be used until intra-stack alignment, ignored after
    """

    first_section = min(sections_to_filenames.keys())
    offset = 1 - first_section

    sfns_text = ""
    sfns_till_alignment_text = ""
    for section, fn in sections_to_filenames.items():

        if fn == 'Placeholder':
            quality = 'unusable'
        else:
            quality = fn_to_quality[fn]

        # section_str is the section encoded as a string, padded with zeros
        section_str = str(section + offset).zfill(3)

        # If section is marked "unusable"
        if quality == 'unusable':
            sfns_text += 'Placeholder ' + section_str + '\n'
            sfns_till_alignment_text += 'Placeholder ' + section_str + '\n'
            continue
        elif quality == 'good':
            sfns_text += fn + ' ' + section_str + '\n'
            sfns_till_alignment_text += fn + ' ' + section_str + '\n'
            continue
        elif quality == 'blurry':
            sfns_text += 'Placeholder ' + section_str + '\n'
            sfns_till_alignment_text += fn + ' ' + section_str + '\n'
            continue
    # Remove trailing '\n' at the end of each file
    sfns_text = sfns_text[:-1]
    sfns_till_alignment_text = sfns_till_alignment_text[:-1]

    # Save the "sorted_filenames_till_alignment" as the active sfns file
    with open(sfns_fp, 'w') as f:
        f.write(sfns_till_alignment_text)

    # Write the "post alignment" version
    sfns_post_alignment_fp = sfns_fp.replace('_sorted_filenames', '_sorted_filenames_post_slice_alignment')
    with open(sfns_post_alignment_fp, 'w') as f:
        f.write(sfns_text)

    # Write the "pre alignment" version
    sfns_till_alignment_fp = sfns_fp.replace('_sorted_filenames', '_sorted_filenames_till_slice_alignment')
    with open(sfns_till_alignment_fp, 'w') as f:
        f.write(sfns_till_alignment_text)


def main():
    global app
    app = QApplication(sys.argv)

    global ex
    ex = init_GUI()

    # If True, then the sorted filenames DOES exist but the user does NOT want to load it
    not_loading_curr_sfns = False

    if sfns_already_exists:
        msgBox = QMessageBox()
        text = 'The sorted_filenames seems to already exist in the right place, Do you want to load it?\n\n'
        text += 'Warning: If you select no, it will be overwritten!'
        msgBox.setText(text)
        msgBox.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
        msgBox.addButton(QPushButton('No'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Yes'), QMessageBox.YesRole)
        ret = msgBox.exec_()
        # Cancel
        if ret == 0:
            # sys.exit( app.exec_() )
            return None
        # No
        elif ret == 1:
            # Ask the user if they want to load one that already exists
            not_loading_curr_sfns = True
        # Yes
        elif ret == 2:
            # Load in information on current sorted_filenames
            ex.load_sorted_filenames()
            ex.show()
            # Simulate a user's keypress because otherwise the autozoom is weird
            ex.keyPressEvent(91)
            # set_step_completed_in_progress_ini( stack, '1-4_setup_sorted_filenames')
            sys.exit(app.exec_())
    # If sorted_filenames does NOT exist, we must make a new one
    if (not sfns_already_exists) or (not_loading_curr_sfns):
        msgBox = QMessageBox()
        text = 'Do you want to load a sorted_filenames text file that has already been made?\n\n'
        text += 'If you select no, you will need to create one using a custom GUI.'
        msgBox.setText(text)
        msgBox.addButton(QPushButton('No'), QMessageBox.NoRole)
        msgBox.addButton(QPushButton('Yes'), QMessageBox.YesRole)
        ret = msgBox.exec_()
        print(ret)
        # Yes
        if ret == 1:
            fp = get_selected_fp(default_filetype=[("text files", "*.txt"), ("all files", "*.*")])
            filepath_sfns = fp
            filepath_sfns_folder = fp[0:max(loc for loc, val in enumerate(fp) if val == '/')]
            validated, err_msg = validate_sorted_filenames(fp)

            if validated:
                copy_over_sorted_filenames(stack, fp)
                sys.stderr.write('\nCopying sorted filenames was successful!\n')
                set_step_completed_in_progress_ini(stack, '1-4_setup_sorted_filenames')
            else:
                sys.stderr.write('\n' + err_msg + '\n')

            # sys.exit( app.exec_() )
        # No
        elif ret == 0:
            # Run GUI as usual
            ex.show()
            # Simulate a user's keypress because otherwise the autozoom is weird
            ex.keyPressEvent(91)
            sys.exit(app.exec_())


### All functions below this point are meant for copying over an existing sorted_filenames file
def get_selected_fp(initialdir='/', default_filetype=("jp2 files", "*.jp2")):
    if ON_DOCKER:
        initialdir = '/mnt/computer_root/'

    root = Tk()
    root.filename = filedialog.askopenfilename(initialdir=initialdir,
                                               title="Select file",
                                               filetypes=default_filetype)
    fn = root.filename
    root.destroy()
    return fn


def validate_sorted_filenames(fp):
    section_names, section_numbers = load_sorted_filenames(fp)

    if len(section_names) != len(set(section_names)):
        return False, "Error: A section name appears multiple times"
    if len(section_numbers) != len(set(section_numbers)):
        return False, "Error: A section number appears multiple times"
    if len(section_numbers) != len(section_names):
        return False, "Error: Every Section name must have a corresponding section number"

    return True, ""


def copy_over_sorted_filenames(stack, sfns_input_fp):
    correct_sorted_fns_fp = DataManager.get_sorted_filenames_filename(stack)
    command = ["cp", sfns_input_fp, correct_sorted_fns_fp]
    subprocess.call(command)


def load_sorted_filenames(fp):
    '''
        load_sorted_filenames( stack ) returns a list of section names
        and their associated section numbers
    '''
    # fn = stack+'_sorted_filenames.txt'

    file_sfns = open(fp, 'r')
    section_names = []
    section_numbers = []

    for line in file_sfns:
        if 'Placeholder' in line:
            continue
        elif line == '':
            continue
        elif line == '\n':
            continue
        else:
            try:
                space_index = line.index(" ")
            except Exception as e:
                print(e)
                print('ignoring the line with this error')
                continue
            section_name = line[0: space_index]
            section_number = line[space_index + 1:]
            section_names.append(section_name)
            section_numbers.append(section_number)
    return section_names, section_numbers


if __name__ == '__main__':
    main()
