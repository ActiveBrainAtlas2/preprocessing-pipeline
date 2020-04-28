#! /usr/bin/env python

import sys, os
import argparse
import numpy as np
import cv2
from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap, QFont, QIntValidator, QImage
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QWidget, QGridLayout, QLineEdit, \
    QPushButton, QMessageBox, QApplication

from image_viewer import ImageViewer
from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController


def get_img( section, prep_id='None', resol='thumbnail', version='NtbNormalized' ):
    return DataManager.load_image(stack=stack,
                          section=section, prep_id=prep_id,
                          resol=resol, version=version)

def get_fp( section, prep_id=1, resol='thumbnail', version='auto' ):
    if version=='auto':
        stain = stack_metadata[stack]['stain'].lower()
        version = stain_to_metainfo[stain]['img_version_1']
        
    return DataManager.get_image_filepath(stack=stack,
                          section=section, prep_id=prep_id,
                          resol=resol, version=version)

class GUICropBrainStem(QWidget):
    
    def __init__(self, stack, parent = None):
        super(GUICropBrainStem, self).__init__(parent)

        self.stack = stack
        self.fileLocationManager = FileLocationManager(self.stack)
        self.sqlController = SqlController()
        self.sqlController.get_animal_info(self.stack)

        self.valid_sections = self.sqlController.get_valid_sections(stack)
        self.valid_section_keys = sorted(list(self.valid_sections))

        self.curr_section_index = 0
        self.curr_section = None

        self.active_selection = ''
        self.img_width = 2001
        self.img_height = 1001
        
        self.rostral = -1
        self.caudal = -1
        self.ventral = -1
        self.dorsal = -1
        self.first_slice = -1
        self.last_slice = -1
                
        self.init_ui()

        self.b_rostral.clicked.connect(lambda:self.click_button(self.b_rostral))
        self.b_caudal.clicked.connect(lambda:self.click_button(self.b_caudal))
        self.b_dorsal.clicked.connect(lambda:self.click_button(self.b_dorsal))
        self.b_ventral.clicked.connect(lambda:self.click_button(self.b_ventral))
        self.b_first_slice.clicked.connect(lambda:self.click_button(self.b_first_slice))
        self.b_last_slice.clicked.connect(lambda:self.click_button(self.b_last_slice))
        self.b_done.clicked.connect(lambda:self.click_button(self.b_done))
        self.viewer.click.connect(self.click_photo)


    def init_ui(self):
        self.font_h1 = QFont("Arial", 32)
        self.font_p1 = QFont("Arial", 16)

        self.grid_top = QGridLayout()
        self.grid_body_upper = QGridLayout()
        self.grid_body = QGridLayout()
        self.grid_body_lower = QGridLayout()

        self.resize(1600, 1100)

        # Grid Top
        self.e_title = QLineEdit()
        self.e_title.setAlignment(Qt.AlignCenter)
        self.e_title.setFont(self.font_h1)
        self.e_title.setReadOnly(True)
        self.e_title.setText("Setup Sorted Filenames")
        self.e_title.setFrame(False)
        self.grid_top.addWidget(self.e_title, 0, 0)

        self.b_help = QPushButton("HELP")
        self.b_help.setDefault(True)
        self.b_help.setEnabled(True)
        self.grid_top.addWidget(self.b_help, 0, 1)

        # Grid BODY UPPER
        self.e_filename = QLineEdit()
        self.e_filename.setAlignment(Qt.AlignCenter)
        self.e_filename.setFont(self.font_p1)
        self.e_filename.setReadOnly(True)
        self.e_filename.setText("Filename: ")
        self.grid_body_upper.addWidget(self.e_filename, 0, 2)

        self.e_section = QLineEdit()
        self.e_section.setAlignment(Qt.AlignCenter)
        self.e_section.setFont(self.font_p1)
        self.e_section.setReadOnly(True)
        self.e_section.setText("Section: ")
        self.grid_body_upper.addWidget(self.e_section, 0, 3)

        # Grid BODY
        self.viewer = ImageViewer(self)
        self.grid_body.addWidget(self.viewer, 0, 0)

        # Grid BODY LOWER
        self.b_rostral = QPushButton("Rostral Limit:")
        self.grid_body_lower.addWidget(self.b_rostral, 0, 0)

        self.e_rostral = QLineEdit()
        self.e_rostral.setAlignment(Qt.AlignCenter)
        self.e_rostral.setFont(self.font_p1)
        self.grid_body_lower.addWidget(self.e_rostral, 0, 1)

        self.b_caudal = QPushButton("Caudal Limit:")
        self.grid_body_lower.addWidget(self.b_caudal, 1, 0)

        self.e_caudal = QLineEdit()
        self.e_caudal.setAlignment(Qt.AlignCenter)
        self.e_caudal.setFont(self.font_p1)
        self.grid_body_lower.addWidget(self.e_caudal, 1, 1)

        self.b_dorsal = QPushButton("Dorsal Limit:")
        self.grid_body_lower.addWidget(self.b_dorsal, 0, 2)

        self.e_dorsal = QLineEdit()
        self.e_dorsal.setAlignment(Qt.AlignCenter)
        self.e_dorsal.setFont(self.font_p1)
        self.grid_body_lower.addWidget(self.e_dorsal, 0, 3)

        self.b_ventral = QPushButton("Ventral Limit:")
        self.grid_body_lower.addWidget(self.b_ventral, 1, 2)

        self.e_ventral = QLineEdit()
        self.e_ventral.setAlignment(Qt.AlignCenter)
        self.e_ventral.setFont(self.font_p1)
        self.grid_body_lower.addWidget(self.e_ventral, 1, 3)

        self.b_first_slice = QPushButton("Mark as FIRST Slice With Brainstem:")
        self.grid_body_lower.addWidget(self.b_first_slice, 0, 4)

        self.e_first_slice = QLineEdit()
        self.e_first_slice.setAlignment(Qt.AlignCenter)
        self.e_first_slice.setFont(self.font_p1)
        self.grid_body_lower.addWidget(self.e_first_slice, 0, 5)

        self.b_last_slice = QPushButton("Mark as LAST Slice With Brainstem:")
        self.grid_body_lower.addWidget(self.b_last_slice, 1, 4)

        self.e_last_slice = QLineEdit()
        self.e_last_slice.setAlignment(Qt.AlignCenter)
        self.e_last_slice.setFont(self.font_p1)
        self.grid_body_lower.addWidget(self.e_last_slice, 1, 5)

        self.b_done = QPushButton("DONE")
        self.grid_body_lower.addWidget(self.b_done, 1, 6)

        # Super grid
        self.supergrid = QGridLayout()
        self.supergrid.addLayout( self.grid_top, 0, 0)
        self.supergrid.addLayout( self.grid_body_upper, 1, 0)
        self.supergrid.addLayout( self.grid_body, 2, 0)
        self.supergrid.addLayout( self.grid_body_lower, 3, 0)

        # Set layout and window title
        self.setLayout( self.supergrid )
        self.setWindowTitle("Q")

    def click_photo(self, pos):
        if self.viewer.dragMode() == QGraphicsView.NoDrag:
            x = pos.x()
            y = pos.y()
            print('%d, %d' % (pos.x(), pos.y()))

            scale_factor = 1.0 / self.viewer.scale_factor

            if self.active_selection=='':
                pass
            elif self.active_selection=='rostral':
                self.rostral = int(x * scale_factor)
                self.rostral = min(self.rostral, self.img_width - 5)
                self.rostral = max(self.rostral, 5)
                self.e_rostral.setText(str(self.rostral))
            elif self.active_selection=='caudal':
                self.caudal = int(x * scale_factor)
                self.caudal = min(self.caudal, self.img_width - 5)
                self.caudal = max(self.caudal, 5)
                self.e_caudal.setText(str(self.caudal))
            elif self.active_selection=='dorsal':
                self.dorsal = int(y * scale_factor)
                self.dorsal = min(self.dorsal, self.img_height - 5)
                self.dorsal = max(self.dorsal, 5)
                self.e_dorsal.setText(str(self.dorsal))
            elif self.active_selection=='ventral':
                self.ventral = int(y * scale_factor)
                self.ventral = min(self.ventral, self.img_height - 5)
                self.ventral = max(self.ventral, 5)
                self.e_ventral.setText(str(self.ventral))

            self.active_selection = ''
            self.viewer.set_drag_mode(1)

    def updateCropVals(self):
        if self.e_rostral.text()!= '':
            try:
                self.rostral = int(self.e_rostral.text())
            except:
                self.rostral = -1
                self.e_rostral.setText("")
        if self.e_caudal.text()!= '':
            try:
                self.caudal = int(self.e_caudal.text())
            except:
                self.caudal = -1
                self.e_caudal.setText("")
        if self.e_dorsal.text()!= '':
            try:
                self.dorsal = int(self.e_dorsal.text())
            except:
                self.dorsal = -1
                self.e_dorsal.setText("")
        if self.e_ventral.text()!= '':
            try:
                self.ventral = int(self.e_ventral.text())
            except:
                self.ventral = -1
                self.e_ventral.setText("")
        if self.e_first_slice.text()!= '':
            try:
                self.first_slice = int(self.e_first_slice.text())
            except:
                self.first_slice = -1
                self.e_first_slice.setText("")
        if self.e_last_slice.text()!= '':
            try:
                self.last_slice = int(self.e_last_slice.text())
            except:
                self.last_slice = -1
                self.e_last_slice.setText("")

    def loadImage(self):
        # Get filepath of "curr_section" and set it as viewer's photo
        fp = get_fp( self.curr_section )
        img = cv2.imread(fp) * 3
        height, width, channel = img.shape
        self.img_width = width
        self.img_height = height

        if self.rostral != -1:
            x_coordinate = int( self.rostral )
            img[:,x_coordinate-2:x_coordinate+2,:] = np.ones( ( height, 4, 3 ) ) *255
        if self.caudal != -1:
            x_coordinate = int( self.caudal )
            img[:,x_coordinate-2:x_coordinate+2,:] = np.ones( ( height, 4, 3 ) ) *255
        if self.dorsal != -1:
            y_coordinate = int( self.dorsal )
            img[y_coordinate-2:y_coordinate+2,:,:] = np.ones( ( 4, width, 3 ) ) *255
        if self.ventral != -1:
            y_coordinate = int( self.ventral )
            img[y_coordinate-2:y_coordinate+2,:,:] = np.ones( ( 4, width, 3 ) ) *255

        bytesPerLine = 3 * width
        qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)

        self.viewer.setPhoto(QPixmap(qImg))

    def set_curr_section(self, section_index=-1):
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

        # Update the section and filename at the top
        label = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['source']
        self.e_filename.setText(label)
        self.e_section.setText(str(self.curr_section))

        # Get filepath of "curr_section" and set it as viewer's photo
        img_fp = os.path.join(self.fileLocationManager.thumbnail_prep, self.curr_section)
        self.viewer.set_photo(img_fp)

        # Update the internal crop values based on text boxes
        #self.updateCropVals()

        #self.loadImage()

    def get_valid_section_index(self, section_index):
        if section_index >= len(self.valid_sections):
            return 0
        elif section_index < 0:
            return len(self.valid_sections) - 1
        else:
            return section_index

    def click_button(self, button):
        if button in [self.b_rostral, self.b_caudal, self.b_dorsal, self.b_ventral]:
            self.viewer.set_drag_mode(0)

            if button == self.b_rostral:
                self.active_selection = 'rostral'
            elif button == self.b_caudal:
                self.active_selection = 'caudal'
            elif button == self.b_dorsal:
                self.active_selection = 'dorsal'
            elif button == self.b_ventral:
                self.active_selection = 'ventral'

        # Prep2 section limits
        elif button in [self.b_first_slice, self.b_last_slice]:
            if button == self.b_first_slice:
                self.first_slice = int( self.curr_section )
                self.e_first_slice.setText(str(self.curr_section))
            elif button == self.b_last_slice:
                self.last_slice = int( self.curr_section )
                self.e_last_slice.setText(str(self.curr_section))
            
        elif button == self.b_done:
            if -1 in [self.rostral, self.caudal, self.dorsal, self.ventral, self.first_slice, self.last_slice]:
                QMessageBox.about(self, "Popup Message", "Make sure all six fields have values!")
                return
            elif self.rostral >= self.caudal:
                QMessageBox.about(self, "Popup Message", "Rostral Limit must be smaller than caudal limit!")
                return
            elif self.dorsal >= self.ventral:
                QMessageBox.about(self, "Popup Message", "Dorsal Limit must be smaller than Ventral limit!")
                return
            elif self.first_slice >= self.last_slice:
                QMessageBox.about(self, "Popup Message", "Last slice must be after the first slice!")
                return

            try:
                QMessageBox.about(self, "Popup Message", "This operation will take roughly 1.5 minutes per image.")
                self.setCurrSection( self.curr_section )
                stain = stack_metadata[stack]['stain']
                os.subprocess.call(['python', 'a_script_preprocess_6.py', stack, stain,
                                '-l', str(self.rostral), str(self.caudal),
                                    str(self.dorsal), str(self.ventral),
                                    str(self.first_slice), str(self.last_slice)])
                sys.exit( app.exec_() )
            except Exception as e:
                sys.stderr.write('\n ********************************\n')
                sys.stderr.write( str(e) )
                sys.stderr.write('\n ********************************\n')
        
    def keyPressEvent(self, event):
        try:
            key = event.key()
        except AttributeError:
            key = event

        if key == 91:  # [
            index = self.get_valid_section_index(self.curr_section_index - 1)
            self.set_curr_section(index)
        elif key == 93:  # ]
            index = self.get_valid_section_index(self.curr_section_index + 1)
            self.set_curr_section(index)
        elif key==16777220: # Enter
            index = self.get_valid_section_index(self.curr_section_index)
            self.set_curr_section(index)
        else:
            print(key)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='GUI for cropping brain stem')
    parser.add_argument("stack", type=str, help="stack name")
    args = parser.parse_args()
    stack = args.stack

    app = QApplication(sys.argv)
    ex = GUICropBrainStem(stack)
    ex.keyPressEvent(91)
    ex.show()
    sys.exit(app.exec_())
