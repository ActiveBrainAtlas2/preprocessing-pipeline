#! /usr/bin/env python
import subprocess
import sys, os
import argparse

import cv2
from PyQt5.QtCore import pyqtSignal, QPoint, Qt, QRectF
from PyQt5.QtGui import QColor, QBrush, QPixmap, QFont, QIntValidator, QImage
from PyQt5.QtWidgets import QGraphicsView, QGraphicsPixmapItem, QGraphicsScene, QFrame, QWidget, QGridLayout, QLineEdit, \
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
stain = stack_metadata[stack]['stain'].lower()

def get_img( section, prep_id='None', resol='thumbnail', version='NtbNormalized' ):
    return DataManager.load_image(stack=stack,
                          section=section, prep_id=prep_id,
                          resol=resol, version=version)

def get_fp( section, prep_id=1, resol='thumbnail', version='auto' ):
    if version=='auto':
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
        
        self.valid_sections = DataManager.metadata_cache['valid_sections'][stack]
        self.sections_to_filenames = DataManager.metadata_cache['sections_to_filenames'][stack]
        self.curr_section = self.valid_sections[ len(self.valid_sections)/2 ]
        self.prev_section = self.getPrevValidSection( self.curr_section )
        self.next_section = self.getNextValidSection( self.curr_section )
        
        self.dragMode = False
        # self.active_selection can be one of: 
        #      'rostral', 'caudal',  'ventral', 'dorsal', 'first_slice', 'last_slice'
        # Depending on the button that is pushed
        self.active_selection = ''
        
        self.img_width = -1
        self.img_height = -1
        
        self.x_12N = -1
        self.y_12N = -1
        self.x_3N = -1
        self.y_3N = -1
        self.midline = -1
                
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
        # Static Text Field
        self.s1 = QLineEdit()
        self.s1.setAlignment(Qt.AlignCenter)
        self.s1.setFont( self.font_p1 )
        self.s1.setReadOnly( True )
        self.s1.setMaximumWidth( 220 )
        self.s1.setText( "12N, X coordinate:" )
        self.s1.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,200);")
        self.grid_body_lower.addWidget( self.s1, 0, 0)
        # Static Text Field
        self.e1 = QLineEdit()
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont( self.font_p1 )
        #self.e1.setReadOnly( True )
        self.e1.setMaximumWidth( 120 )
        self.e1.setText( "1200" )
        self.e1.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,200);")
        self.grid_body_lower.addWidget( self.e1, 0, 1)
        # Static Text Field
        self.s2 = QLineEdit()
        self.s2.setAlignment(Qt.AlignCenter)
        self.s2.setFont( self.font_p1 )
        self.s2.setReadOnly( True )
        self.s2.setMaximumWidth( 220 )
        self.s2.setText( "12N, Y coordinate:" )
        self.s2.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,200);")
        self.grid_body_lower.addWidget( self.s2, 1, 0)
        # Static Text Field
        self.e2 = QLineEdit()
        self.e2.setAlignment(Qt.AlignCenter)
        self.e2.setFont( self.font_p1 )
        #self.e2.setReadOnly( True )
        self.e2.setMaximumWidth( 120 )
        self.e2.setText( "500" )
        self.e2.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,200);")
        self.grid_body_lower.addWidget( self.e2, 1, 1)
        # Static Text Field
        self.s3 = QLineEdit()
        self.s3.setAlignment(Qt.AlignCenter)
        self.s3.setFont( self.font_p1 )
        self.s3.setReadOnly( True )
        self.s3.setMaximumWidth( 220 )
        self.s3.setText( "3N, X coordinate:" )
        self.s3.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,200,250);")
        self.grid_body_lower.addWidget( self.s3, 0, 2)
        # Static Text Field
        self.e3 = QLineEdit()
        self.e3.setAlignment(Qt.AlignCenter)
        self.e3.setFont( self.font_p1 )
        #self.e3.setReadOnly( True )
        self.e3.setMaximumWidth( 120 )
        self.e3.setText( "900" )
        self.e3.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,200,250);")
        self.grid_body_lower.addWidget( self.e3, 0, 3)
        # Static Text Field
        self.s4 = QLineEdit()
        self.s4.setAlignment(Qt.AlignCenter)
        self.s4.setFont( self.font_p1 )
        self.s4.setReadOnly( True )
        self.s4.setMaximumWidth( 220 )
        self.s4.setText( "3N, Y coordinate:" )
        self.s4.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,200,250);")
        self.grid_body_lower.addWidget( self.s4, 1, 2)
        # Static Text Field
        self.e4 = QLineEdit()
        self.e4.setAlignment(Qt.AlignCenter)
        self.e4.setFont( self.font_p1 )
        #self.e4.setReadOnly( True )
        self.e4.setMaximumWidth( 120 )
        self.e4.setText( "400" )
        self.e4.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,200,250);")
        self.grid_body_lower.addWidget( self.e4, 1, 3)
        # Static Text Field
        self.s5 = QLineEdit()
        self.s5.setAlignment(Qt.AlignCenter)
        self.s5.setFont( self.font_p1 )
        self.s5.setReadOnly( True )
        self.s5.setMaximumWidth( 220 )
        self.s5.setText( "Midline slice:" )
        self.s5.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,200);")
        self.grid_body_lower.addWidget( self.s5, 0, 4)
        # Static Text Field
        self.e5 = QLineEdit()
        self.e5.setAlignment(Qt.AlignCenter)
        self.e5.setFont( self.font_p1 )
        #self.e5.setReadOnly( True )
        self.e5.setMaximumWidth( 120 )
        self.e5.setText( str(self.curr_section) )
        self.e5.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,200);")
        self.grid_body_lower.addWidget( self.e5, 0, 5)
        # Button Text Field
        self.b_midline = QPushButton("Go to midline image")
        self.b_midline.setDefault(True)
        self.b_midline.clicked.connect(lambda:self.buttonPress(self.b_midline))
        self.b_midline.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,180);")
        self.grid_body_lower.addWidget( self.b_midline, 1, 4)
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
        
        self.loadImage()
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
        
        center_12N = ( self.x_12N, self.y_12N)
        cv2.circle(img, center_12N, radius=4, color=(255,0,0), thickness=8, lineType=8, shift=0)
        center_3N = ( self.x_3N, self.y_3N)
        cv2.circle(img, center_3N, radius=4, color=(0,0,255), thickness=8, lineType=8, shift=0)
        
        bytesPerLine = 3 * width
        qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        
        self.viewer.setPhoto( QPixmap( qImg ) )
        
    def photoClicked(self, pos):
        if self.viewer.dragMode() == QGraphicsView.NoDrag:
            print('%d, %d' % (pos.x(), pos.y()))
            
    def pixInfo(self):
        self.viewer.toggleDragMode()
        self.dragMode = not self.dragMode
        
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
        self.updatePositionVals()
            
        self.loadImage()
            
    def buttonPress(self, button):
        # Set midline slice as active slice
        if button == self.b_midline:
            curr_section = self.curr_section
            
            if self.midline in self.valid_sections:
                self.setCurrSection( self.midline )
            
        elif button == self.b_done:
            validated = self.validateChoices()
            if not validated:
                return
            
            try:
                QMessageBox.about(self, "Popup Message", "This operation will take roughly 1.5 minutes per image.")
                self.setCurrSection( self.curr_section )
                stain = stack_metadata[stack]['stain']
                subprocess.call(['python','a_script_preprocess_7.py', stack, stain, 
                                '-l', str(self.x_12N), str(self.y_12N), 
                                      str(self.x_3N), str(self.y_3N), 
                                      str(self.midline)])
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
        
    def updatePositionVals(self):
        x_12N = self.e1.text()
        y_12N = self.e2.text()
        x_3N = self.e3.text()
        y_3N = self.e4.text()
        midline = self.e5.text()
        
        try:
            x_12N = int(x_12N)
            assert x_12N > 0 
            assert x_12N < self.img_width
            self.x_12N = x_12N
        except Exception as e:
            sys.stderr.write( str(e) )
            self.e1.setText( '0' )
            self.x_12N = 0
            
        try:
            y_12N = int(y_12N)
            assert y_12N > 0 
            assert y_12N < self.img_height
            self.y_12N = y_12N
        except Exception as e:
            sys.stderr.write( str(e) )
            self.e2.setText( '0' )
            self.y_12N = 0
            
        try:
            x_3N = int(x_3N)
            assert x_3N > 0 
            assert x_3N < self.img_width
            self.x_3N = x_3N
        except Exception as e:
            sys.stderr.write( str(e) )
            self.e3.setText( '0' )
            self.x_3N = 0
            
        try:
            y_3N = int(y_3N)
            assert y_3N > 0 
            assert y_3N < self.img_height
            self.y_3N = y_3N
        except Exception as e:
            sys.stderr.write( str(e) )
            self.e4.setText( '0' )
            self.y_3N = 0
            
        try:
            midline = int(midline)
            assert midline >= min(self.valid_sections) 
            assert midline <= max(self.valid_sections)
            self.midline = midline
        except Exception as e:
            sys.stderr.write( str(e) )
            self.midline = self.valid_sections[ len(self.valid_sections)/2 ]
            self.e5.setText( str(self.valid_sections[ len(self.valid_sections)/2 ]) )
                
    def validateChoices(self):
        validated = True
        
        if self.y_12N < 0 or self.x_12N < 0 or self.y_3N < 0 or self.x_3N < 0:
            QMessageBox.about(self, "Popup Message", "Make sure there are no negative values!")
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
