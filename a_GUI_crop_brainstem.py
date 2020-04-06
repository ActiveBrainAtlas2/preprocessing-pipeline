#! /usr/bin/env python

import sys, os
import argparse
import numpy as np
import cv2
from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QRectF
from PyQt5.QtGui import QBrush, QColor, QPixmap, QFont, QIntValidator, QImage
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QWidget, QGridLayout, QLineEdit, \
    QPushButton, QMessageBox, QApplication

from utilities.data_manager_v2 import DataManager
from utilities.metadata import stack_metadata, stain_to_metainfo

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Mask Editing GUI')
parser.add_argument("stack", type=str, help="stack name")
args = parser.parse_args()
global stack
stack = args.stack


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

#from PyQt4 import QtCore, QtGui

class ImageViewer( QGraphicsView):
    photoClicked = pyqtSignal( QPoint )

    def __init__(self, parent):
        super(ImageViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor( QGraphicsView.AnchorUnderMouse )
        self.setResizeAnchor( QGraphicsView.AnchorUnderMouse )
        self.setVerticalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.setHorizontalScrollBarPolicy( Qt.ScrollBarAlwaysOff )
        self.setBackgroundBrush( QBrush( QColor(30, 30, 30) ))
        self.setFrameShape( QFrame.NoFrame )
        # Added later
        self.scale_factor = 0

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect( QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                self.scale(factor, factor)
                self.scale_factor =  factor
            self._zoom = 0
        else:
            print 'RECT IS NULL'

    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            self.setDragMode( QGraphicsView.ScrollHandDrag )
            self._photo.setPixmap( pixmap )
        else:
            self._empty = True
            self.setDragMode( QGraphicsView.NoDrag )
            self._photo.setPixmap( QPixmap() )
        self.fitInView()

    def wheelEvent(self, event):
        if self.hasPhoto() and False:
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
            self.setDragMode( QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode( QGraphicsView.ScrollHandDrag )

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit( QPoint(event.pos()) )
        super(ImageViewer, self).mousePressEvent(event)


class init_GUI(QWidget):
    
    def __init__(self, parent = None):
        super(init_GUI, self).__init__(parent)
        self.font_h1 = QFont("Arial",32)
        self.font_p1 = QFont("Arial",16)
        
        self.valid_sections = DataManager.metadata_cache['valid_sections_all'][stack]
        self.sections_to_filenames = DataManager.metadata_cache['sections_to_filenames'][stack]
        self.curr_section = self.valid_sections[ len(self.valid_sections)/2 ]
        self.prev_section = self.getPrevValidSection( self.curr_section )
        self.next_section = self.getNextValidSection( self.curr_section )
        
        self.dragMode = False
        # self.active_selection can be one of: 
        #      'rostral', 'caudal',  'ventral', 'dorsal', 'first_slice', 'last_slice'
        # Depending on the button that is pushed
        self.active_selection = ''
        
        self.img_width = 2001
        self.img_height = 1001
        
        self.rostral = -1
        self.caudal = -1
        self.ventral = -1
        self.dorsal = -1
        self.first_slice = -1
        self.last_slice = -1
                
        self.initUI()
        
    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_body_upper = QGridLayout()
        self.grid_body = QGridLayout()
        self.grid_body_lower = QGridLayout()
        self.grid_bottom = QGridLayout()
        
        #self.setFixedSize(1500, 1000)
        self.resize(1500, 1000)
        
        ### VIEWER ### (Grid Body)
        self.viewer = ImageViewer(self)
        self.viewer.photoClicked.connect( self.photoClicked )
        
        ### Grid TOP ###
        # Static Text Field (Title)
        self.e0 = QLineEdit()
        self.e0.setValidator( QIntValidator() )
        self.e0.setAlignment(Qt.AlignCenter)
        self.e0.setFont( self.font_h1 )
        self.e0.setReadOnly( True )
        self.e0.setText( "Find Brainstem Cropbox" )
        self.e0.setFrame( False )
        self.grid_top.addWidget( self.e0, 0, 0)
        
        ### Grid BODY UPPER ###
        # Static Text Field
        self.e_fn = QLineEdit()
        self.e_fn.setAlignment(Qt.AlignCenter)
        self.e_fn.setFont( self.font_p1 )
        self.e_fn.setReadOnly( True )
        self.e_fn.setText( "Filename: " )
        #self.e_fn.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget( self.e_fn, 0, 0)
        # Static Text Field
        self.e_sc = QLineEdit()
        self.e_sc.setAlignment(Qt.AlignCenter)
        self.e_sc.setFont( self.font_p1 )
        self.e_sc.setReadOnly( True )
        self.e_sc.setText( "Section: " )
        #self.e_sc.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget( self.e_sc, 0, 1)
                
        ### Grid BODY ###
        # Custom VIEWER
        self.grid_body.addWidget( self.viewer, 0, 0)

        ### Grid BOTTOM LOWER ###
        # Button Text Field
        self.b1 = QPushButton("Rostral Limit:")
        self.b1.setDefault(True)
        self.b1.clicked.connect(lambda:self.buttonPress(self.b1))
        self.b1.setMaximumWidth( 200 )
        #self.b1.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower.addWidget(self.b1, 0, 0)
        # Static Text Field
        self.e1 = QLineEdit()
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont( self.font_p1 )
        #self.e1.setReadOnly( True )
        self.e1.setMaximumWidth( 120 )
        self.e1.setText( "" )
        self.grid_body_lower.addWidget( self.e1, 0, 1)
        # Button Text Field
        self.b2 = QPushButton("Caudal Limit:")
        self.b2.setDefault(True)
        self.b2.clicked.connect(lambda:self.buttonPress(self.b2))
        self.b2.setMaximumWidth( 200 )
        #self.b2.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower.addWidget(self.b2, 1, 0)
        # Static Text Field
        self.e2 = QLineEdit()
        self.e2.setAlignment(Qt.AlignCenter)
        self.e2.setFont( self.font_p1 )
        #self.e2.setReadOnly( True )
        self.e2.setMaximumWidth( 120 )
        self.e2.setText( "" )
        self.grid_body_lower.addWidget( self.e2, 1, 1)
        # Button Text Field
        self.b3 = QPushButton("Dorsal Limit:")
        self.b3.setDefault(True)
        self.b3.clicked.connect(lambda:self.buttonPress(self.b3))
        self.b3.setMaximumWidth( 200 )
        #self.b3.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower.addWidget(self.b3, 0, 2)
        # Static Text Field
        self.e3 = QLineEdit()
        self.e3.setAlignment(Qt.AlignCenter)
        self.e3.setFont( self.font_p1 )
        #self.e3.setReadOnly( True )
        self.e3.setMaximumWidth( 120 )
        self.e3.setText( "" )
        self.grid_body_lower.addWidget( self.e3, 0, 3)
        # Button Text Field
        self.b4 = QPushButton("Ventral Limit:")
        self.b4.setDefault(True)
        self.b4.clicked.connect(lambda:self.buttonPress(self.b4))
        self.b4.setMaximumWidth( 200 )
        #self.b4.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower.addWidget(self.b4, 1, 2)
        # Static Text Field
        self.e4 = QLineEdit()
        self.e4.setAlignment(Qt.AlignCenter)
        self.e4.setFont( self.font_p1 )
        #self.e4.setReadOnly( True )
        self.e4.setMaximumWidth( 120 )
        self.e4.setText( "" )
        self.grid_body_lower.addWidget( self.e4, 1, 3)
        # Button Text Field
        self.b5 = QPushButton("Mark as FIRST Slice With Brainstem:")
        self.b5.setDefault(True)
        self.b5.clicked.connect(lambda:self.buttonPress(self.b5))
        self.b5.setMaximumWidth( 350 )
        #self.b5.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower.addWidget(self.b5, 0, 4)
        # Static Text Field
        self.e5 = QLineEdit()
        self.e5.setAlignment(Qt.AlignCenter)
        self.e5.setFont( self.font_p1 )
        #self.e5.setReadOnly( True )
        self.e5.setMaximumWidth( 120 )
        self.e5.setText( "" )
        self.grid_body_lower.addWidget( self.e5, 0, 5)
        # Button Text Field
        self.b6 = QPushButton("Mark as LAST Slice With Brainstem:")
        self.b6.setDefault(True)
        self.b6.clicked.connect(lambda:self.buttonPress(self.b6))
        self.b6.setMaximumWidth( 350 )
        #self.b6.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower.addWidget(self.b6, 1, 4)
        # Static Text Field
        self.e6 = QLineEdit()
        self.e6.setAlignment(Qt.AlignCenter)
        self.e6.setFont( self.font_p1 )
        #self.e6.setReadOnly( True )
        self.e6.setMaximumWidth( 120 )
        self.e6.setText( "" )
        self.grid_body_lower.addWidget( self.e6, 1, 5)
        # Button Text Field
        self.b_done = QPushButton("DONE")
        self.b_done.setDefault(True)
        self.b_done.clicked.connect(lambda:self.buttonPress(self.b_done))
        #self.b_done.setMaximumWidth( 350 )
        self.b_done.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,250);")
        self.grid_body_lower.addWidget(self.b_done, 1, 6)
        
        ### STRETCH rows + cols
        self.grid_body_upper.setColumnStretch(0, 2)
        #self.grid_body_upper.setColumnStretch(2, 2)
        
        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout( self.grid_top, 0, 0)
        self.supergrid.addLayout( self.grid_body_upper, 1, 0)
        self.supergrid.addLayout( self.grid_body, 2, 0)
        self.supergrid.addLayout( self.grid_body_lower, 3, 0)
        self.supergrid.addLayout( self.grid_bottom, 4, 0)
        
        # Set layout and window title
        self.setLayout( self.supergrid )
        self.setWindowTitle("Q")
        
        # Loads self.curr_section as the current image and sets all fields appropriatly
        self.setCurrSection( self.curr_section )
        
        #time.sleep(2)
        #self.keyPressEvent(91)
        
    def loadImageSimple(self):
        # Get filepath of "curr_section" and set it as viewer's photo
        fp = get_fp( self.curr_section )
        self.viewer.setPhoto( QPixmap( fp ) )
        
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
        
        self.viewer.setPhoto( QPixmap( qImg ) )
        
    def photoClicked(self, pos):
        if self.viewer.dragMode() == QGraphicsView.NoDrag:
            x = pos.x()
            y = pos.y()
            print('%d, %d' % (pos.x(), pos.y()))
            # Record the selected coordinates using the 'active_selection'
            self.record_selected_coordinates(x,y)
            
    def pixInfo(self):
        self.viewer.toggleDragMode()
        self.dragMode = not self.dragMode
        
    def record_selected_coordinates(self, x, y):
        scale_factor = 1.0 / self.viewer.scale_factor
        
        if self.active_selection=='':
            pass
        elif self.active_selection=='rostral':
            self.rostral = int(x*scale_factor)
            self.rostral = min(self.rostral, self.img_width-5)
            self.rostral = max(self.rostral, 5)
            self.e1.setText( str(self.rostral) )
        elif self.active_selection=='caudal':
            self.caudal = int(x*scale_factor)
            self.caudal = min(self.caudal, self.img_width-5)
            self.caudal = max(self.caudal, 5)
            self.e2.setText( str(self.caudal) )
        elif self.active_selection=='dorsal':
            self.dorsal = int(y*scale_factor)
            self.dorsal = min(self.dorsal, self.img_height-5)
            self.dorsal = max(self.dorsal, 5)
            self.e3.setText( str(self.dorsal) )
        elif self.active_selection=='ventral':
            self.ventral = int(y*scale_factor)
            self.ventral = min(self.ventral, self.img_height-5)
            self.ventral = max(self.ventral, 5)
            self.e4.setText( str(self.ventral) )
        
        self.active_selection = ''
        
    def keyPressEvent(self, event):
        try:
            key = event.key()
        except AttributeError:
            key = event
        
        if key==91: # [
            self.setCurrSection( self.getPrevValidSection( self.curr_section ) )
            
        elif key==93: # ]
            self.setCurrSection( self.getNextValidSection( self.curr_section ) )
            
        elif key==16777220: # Enter
            self.setCurrSection( self.curr_section )
            
        else:
            print(key)
            
    def setCurrSection(self, section=-1):
        """
        Sets the current section to the section passed in.
        
        Will automatically update curr_section, prev_section, and next_section.
        Updates the header fields and loads the current section image.
        
        """
        # Update curr, prev, and next section
        self.curr_section = section
        self.prev_section = self.getPrevValidSection( self.curr_section )
        self.next_section = self.getNextValidSection( self.curr_section )
        # Update the section and filename at the top
        self.updateCurrHeaderFields()
        # Update the internal crop values based on text boxes
        self.updateCropVals()
            
        self.loadImage()
            
    def buttonPress(self, button):
        # rostral/caudal/ventral/dorsal
        if button in [self.b1, self.b2, self.b3, self.b4]:
            # If Pixel selection mode is not activated
            if not self.dragMode:
                # Turn dragMode on (Turns off on next click)
                self.pixInfo()
                
            if button == self.b1:
                self.active_selection = 'rostral'
            elif button == self.b2:
                self.active_selection = 'caudal'
            elif button == self.b3:
                self.active_selection = 'dorsal'
            elif button == self.b4:
                self.active_selection = 'ventral'
        # Prep2 section limits
        elif button in [self.b5, self.b6]:
            if button == self.b5:
                self.first_slice = int( self.curr_section )
                self.e5.setText( str(self.curr_section) )
            elif button == self.b6:
                self.last_slice = int( self.curr_section )
                self.e6.setText( str(self.curr_section) )
            
        elif button == self.b_done:
            validated = self.validateChoices()
            if not validated:
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
        
    def getNextValidSection(self, section):
        section_index = self.valid_sections.index( section )
        next_section_index = section_index + 1
        if next_section_index > len(self.valid_sections)-1:
            next_section_index = 0
        next_section = self.valid_sections[ next_section_index ]
        return next_section
    
    def getPrevValidSection(self, section):
        section_index = self.valid_sections.index( section )
        prev_section_index = section_index - 1
        if prev_section_index < 0:
            prev_section_index = len(self.valid_sections)-1
        prev_section = self.valid_sections[ prev_section_index ]
        return prev_section
        
    def updateCurrHeaderFields(self):
        self.e_fn.setText( str(self.sections_to_filenames[self.curr_section]) )
        self.e_sc.setText( str(self.curr_section) )
        
    def updateCropVals(self):
        
        if self.e1.text()!='':
            try:
                self.rostral = int( self.e1.text() )
            except:
                self.rostral = -1
                self.e1.setText( "" )
        if self.e2.text()!='':
            try:
                self.caudal = int( self.e2.text() )
            except:
                self.caudal = -1
                self.e2.setText( "" )
        if self.e3.text()!='':
            try:
                self.dorsal = int( self.e3.text() )
            except:
                self.dorsal = -1
                self.e3.setText( "" )
        if self.e4.text()!='':
            try:
                self.ventral = int( self.e4.text() )
            except:
                self.ventral = -1
                self.e4.setText( "" )
        if self.e5.text()!='':
            try:
                self.first_slice = int( self.e5.text() )
            except:
                self.first_slice = -1
                self.e5.setText( "" )
        if self.e6.text()!='':
            try:
                self.last_slice = int( self.e6.text() )
            except:
                self.last_slice = -1
                self.e6.setText( "" )
                
    def validateChoices(self):
        validated = True
        
        if -1 in [self.rostral, self.caudal, self.dorsal, self.ventral, self.first_slice, self.last_slice]:
            QMessageBox.about(self, "Popup Message", "Make sure all six fields have values!")
            validated = False
        elif self.rostral >= self.caudal:
            #sys.stderr.write( 'Rostral Limit must be smaller than caudal limit!' )
            QMessageBox.about(self, "Popup Message", "Rostral Limit must be smaller than caudal limit!")
            validated = False
        elif self.dorsal >= self.ventral:
            #sys.stderr.write( 'Dorsal Limit must be smaller than Ventral limit!' )
            QMessageBox.about(self, "Popup Message", "Dorsal Limit must be smaller than Ventral limit!")
            validated = False
        elif self.first_slice >= self.last_slice:
            #sys.stderr.write( 'Last slice must be after the first slice!' )
            QMessageBox.about(self, "Popup Message", "Last slice must be after the first slice!")
            validated = False
        
        return validated
        
        
    def mousePressEvent(self, event):
        if self.dragMode:
            # Turn dragMode off
            self.pixInfo()
            self.setCurrSection( self.curr_section )
        
                    
def close_gui():
    #ex.hide()
    sys.exit( app.exec_() )

def main():
    global app 
    app = QApplication( sys.argv )
    
    global ex
    ex = init_GUI()
    ex.show()
    # Simulate a user's keypress because otherwise the autozoom is weird
    ex.keyPressEvent(91)
    
    sys.exit( app.exec_() )

if __name__ == '__main__':
    main()
