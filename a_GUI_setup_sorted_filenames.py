import os
import argparse
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator, QBrush, QColor, QPixmap, QImage
from PyQt5.QtWidgets import (QWidget, QApplication, QGridLayout, QLineEdit,
                             QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QComboBox,
                             QMessageBox)

from tkinter import *

sys.path.append(os.path.join(os.getcwd(), 'utilities'))
from utilities.a_driver_utilities import set_step_completed_in_progress_ini
from utilities.sqlcontroller import SqlController
from utilities.metadata import ROOT_DIR


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

    def __init__(self, stack, parent=None):
        super(init_GUI, self).__init__(parent)
        self.font_h1 = QFont("Arial", 32)
        self.font_p1 = QFont("Arial", 16)
        # create a dataManager object
        self.sqlController = SqlController()
        self.stack = stack
        self.sqlController.get_animal_info(self.stack)

        self.valid_sections = self.sqlController.get_valid_sections(stack)
        self.valid_section_keys = sorted(list(self.valid_sections))

        section_length =  len(self.valid_section_keys)

        self.curr_section_index = section_length // 2
        self.prev_section_index = self.curr_section_index
        self.next_section_index = self.curr_section_index
        self.curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)

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
        quality_options = ['unusable', 'blurry', 'good']
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
        curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]

        curr_section['quality'] = dropdown_selection

    def load_sorted_filenames(self):
        self.valid_sections = self.sqlController.get_valid_sections(self.stack)
        self.valid_section_keys = sorted(list(self.valid_sections))
        self.curr_section_index = len(self.valid_section_keys) // 2
        self.prev_section_index = self.curr_section_index
        self.next_section_index = self.curr_section_index
        self.curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)
        self.setCurrSection(self.curr_section_index)


    def loadImage(self):
        curr_fn = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
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
            img_fp = os.path.join(ROOT_DIR, self.stack, 'preps', 'thumbnail', curr_fn)
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
        self.curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)

        # Update the section and filename at the top
        self.updateCurrHeaderFields()
        # Update the quality selection in the bottom left
        self.updateQualityField()

        self.loadImage()

    def getNextValidSection(self, section_index):
        self.next_section_index = section_index + 1
        if self.next_section_index > len(self.valid_sections) - 1:
            self.next_section_index = 0
        self.next_section = self.valid_sections[self.valid_section_keys[self.next_section_index]]['destination']
        return self.next_section

    def getPrevValidSection(self, section_index):
        self.prev_section_index = int(section_index) - 1
        if self.prev_section_index < 0:
            self.prev_section_index = len(self.valid_sections) - 1
        self.prev_section = self.valid_sections[self.valid_section_keys[self.prev_section_index]]['destination']
        return self.prev_section

    def buttonPress(self, button):
        # Brighten an image
        if button in [self.b_left, self.b_right, self.b_addPlaceholder, self.b_remove]:
            # Get all relevant filenames
            curr_fn = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
            prev_fn = self.valid_sections[self.valid_section_keys[self.prev_section_index]]['destination']
            next_fn = self.valid_sections[self.valid_section_keys[self.next_section_index]]['destination']

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
            # Remove the current section from "self.valid_sections
            try:
                self.sqlController.inactivate_section(self.valid_section_keys[self.curr_section_index])
            except KeyError:
                print('Key {} missing'.format(self.curr_section_index))

            self.valid_sections = self.sqlController.get_valid_sections(self.stack)
            self.valid_section_keys = sorted(list(self.valid_sections))

            if self.curr_section_index == 0:
                self.curr_section_index = len(self.valid_section_keys) - 1
            else:
                self.curr_section_index = self.curr_section_index - 1

            print('remove curr_section_index', self.curr_section_index)
            self.setCurrSection(self.curr_section_index)


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
        label = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['source']
        self.e4.setText(label)
        self.e5.setText(str(self.curr_section))

    def updateQualityField(self):
        curr_fn = self.valid_sections[self.valid_section_keys[self.curr_section_index]]
        if curr_fn['destination'] == 'Placeholder':
            text = 'unusable'
        else:
            text = curr_fn['quality']
        index = self.dd.findText(text, Qt.MatchFixedString)
        if index >= 0:
            self.dd.setCurrentIndex(index)

    def finished(self):
        # TODO change this to database update
        set_step_completed_in_progress_ini(self.stack, '1-4_setup_sorted_filenames')
        self.sqlController.save_valid_sections(self.valid_sections)
        # close_main_gui( ex )
        sys.exit(app.exec_())


def close_gui():
    # ex.hide()
    sys.exit(app.exec_())


def write_results_to_sorted_filenames(sections_to_filenames, fn_to_quality):
    """
    TODO this needs to get changed to updating the database table raw_section
    Create the sorted_filenames.txt file from the user's "sections_to_filenames".
    Determine quality of each slice from "fn_to_quality".
    
    Quality levels:
        - unusable: Mark as placeholder
        - good: Write to the file as usual
        - blurry: Write to a special file meant to be used until intra-stack alignment, ignored after
    """
    sfns_text = ""
    sfns_till_alignment_text = ""
    for k, filename in sections_to_filenames.items():

        if filename == 'Placeholder':
            quality = 'unusable'
        else:
            quality = fn_to_quality[filename]

        # section_str is the section encoded as a string, padded with zeros
        #section_str = str(section + offset).zfill(3)

        # If section is marked "unusable"
        if quality == 'unusable':
            sfns_text += 'Placeholder ' + str(k) + '\n'
            sfns_till_alignment_text += 'Placeholder ' + str(k) + '\n'
            continue
        elif quality == 'good':
            sfns_text += filename + ' ' + str(k) + '\n'
            sfns_till_alignment_text += filename + ' ' + str(k) + '\n'
            continue
        elif quality == 'blurry':
            sfns_text += 'Placeholder ' + str(k) + '\n'
            sfns_till_alignment_text += filename + ' ' + str(k) + '\n'
            continue
    # Remove trailing '\n' at the end of each file
    sfns_text = sfns_text[:-1]
    sfns_till_alignment_text = sfns_till_alignment_text[:-1]

    # Save the "sorted_filenames_till_alignment" as the active sfns file
    #with open(sfns_fp, 'w') as f:
    #    f.write(sfns_till_alignment_text)



def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='GUI for sorting filenames')
    parser.add_argument("stack", type=str, help="stack name")
    args = parser.parse_args()
    stack = args.stack
    sqlController = SqlController()
    sections = list(sqlController.get_valid_sections(stack))

    if len(sections) > 0:
        global app
        app = QApplication(sys.argv)
        global ex
        ex = init_GUI(stack)
        # Run GUI as usual
        ex.show()
        # Simulate a user's keypress because otherwise the autozoom is weird
        ex.keyPressEvent(91)
        sys.exit(app.exec_())
    else:
        print('There are no sections to work with.')

if __name__ == '__main__':
    main()
