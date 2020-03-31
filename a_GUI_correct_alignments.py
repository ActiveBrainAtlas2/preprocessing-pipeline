#! /usr/bin/env python

import sys, os
import argparse
import math
import cv2
import numpy as np

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator, QBrush, QColor, QPixmap, QPainter, QImage
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QWidget, QGridLayout, QLineEdit, \
    QPushButton, QMessageBox, QApplication
from matplotlib import image

from a_GUI_atlas_local_main import create_input_spec_ini_all
from utilities.a_driver_utilities import call_and_time
from utilities.data_manager_v2 import DataManager
from utilities.utilities2015 import execute_command
from utilities.metadata import stack_metadata, stain_to_metainfo

sys.path.append( os.path.join(os.environ['REPO_DIR'] , 'utilities') )
sys.path.append( os.path.join(os.environ['REPO_DIR'] , 'gui', 'widgets') )
sys.path.append( os.path.join(os.environ['REPO_DIR'] , 'gui') )
sys.path.append(os.path.join(os.environ['REPO_DIR'], 'web_services'))

def get_padding_color(stack):
    stain = stack_metadata[stack]['stain']
    
    if stain.lower() == 'ntb':
        return 'black'
    elif stain.lower() == 'thionin':
        return 'white'
    else:
        return 'auto'
    
def get_version(stack):
    stain = stack_metadata[stack]['stain']
    return stain_to_metainfo[stain.lower()]['img_version_1']

def get_img( section, prep_id='None', resol='thumbnail', version='' ):
    if version=='':
        version = get_version(stack)
        
    return DataManager.load_image(stack=stack,
                          section=section, prep_id=prep_id,
                          resol=resol, version=version)

def get_fp( section, prep_id='None', resol='thumbnail', version='' ):
    if version=='':
        version = get_version(stack)
    
    return DataManager.get_image_filepath(stack=stack, section=section, resol=resol, version=version)

def apply_transform( stack, T, fn, output_fp=None ):
    """
    Applies transform T onto the image at img_fp and return the result
    """
    
    version = get_version(stack)
    
    img_fp = DataManager.get_image_filepath(stack=stack, section=DataManager.metadata_cache['filenames_to_sections'][stack][fn], resol='thumbnail', version=version)
    
    op_str = ''
    op_str += " +distort AffineProjection '%(sx)f,%(rx)f,%(ry)f,%(sy)f,%(tx)f,%(ty)f' " % {
     'sx':T[0,0],
     'sy':T[1,1],
     'rx':T[1,0],
     'ry':T[0,1],
     'tx':T[0,2],
     'ty':T[1,2],}
    
    x = 0
    y = 0
    w = 2000
    h = 1000
    op_str += ' -crop %(w)sx%(h)s%(x)s%(y)s\! ' % {
                     'x': '+' + str(x) if int(x) >= 0 else str(x),
                     'y': '+' + str(y) if int(y) >= 0 else str(y),
                     'w': str(w),
                     'h': str(h)}
    
    if output_fp==None:
        output_fp_root = os.path.join( os.environ['ROOT_DIR'], 'CSHL_data_processed', stack, 'tmp')
        if not os.path.exists( output_fp_root ):
            os.makedirs(output_fp_root)
        output_fp = os.path.join( output_fp_root, 'tmp_'+fn+'.tif' )
        delete_after = True
    else:
        if not os.path.exists( os.path.dirname(output_fp) ):
            os.makedirs( os.path.dirname(output_fp) )
        delete_after = False

    try:
        bg_color = get_padding_color(stack)
        
        execute_command("convert \"%(input_fp)s\"  +repage -virtual-pixel background -background %(bg_color)s %(op_str)s -flatten -compress lzw \"%(output_fp)s\"" % \
                    {'op_str': op_str,
                     'input_fp': img_fp,
                     'output_fp': output_fp,
                     'bg_color': bg_color})
        
        img = cv2.imread( output_fp )
        if delete_after:
            os.remove( output_fp ) 
            pass
        return img
    except Exception as e:
        print(e)
        return None
    
def get_anchor_transform( stack, fn ):
    T = DataManager.load_transforms(stack, downsample_factor=32, use_inverse=True)[fn]
    return T
    
def get_pairwise_transform( stack, fn, prev_fn):
    T = DataManager.load_consecutive_section_transform(
                moving_fn=fn, 
                fixed_fn=prev_fn, 
                stack=stack)
    T = np.linalg.inv(T)
    return T

def get_comulative_pairwise_transform( stack, fn):
    
    T = np.zeros((3,3))#[[0,0,0],[0,0,0],[0,0,1]]
    T[2,2]=1
    
    #valid_fn_prev = DataManager.metadata_cache['valid_filenames_all'][stack][0]
    #for valid_fn in DataManager.metadata_cache['valid_filenames_all'][stack][1:]:
    #    if valid_fn == fn:
    #        break
    #    T_i = DataManager.load_consecutive_section_transform(
    #                moving_fn=valid_fn, 
    #                fixed_fn=valid_fn_prev, 
    #                stack=stack)
    
    valid_sections = DataManager.metadata_cache['valid_sections_all'][stack]
    valid_sections.sort()
    valid_sections.reverse()
    
    valid_sec = valid_sections[0]
    for valid_sec_prev in valid_sections[1:]:
        valid_fn = DataManager.metadata_cache['sections_to_filenames'][stack][valid_sec]
        valid_fn_prev = DataManager.metadata_cache['sections_to_filenames'][stack][valid_sec_prev]
        
        if valid_fn == fn:
            break
            
            
        T_i = DataManager.load_consecutive_section_transform(
                    moving_fn=valid_fn, 
                    fixed_fn=valid_fn_prev, 
                    stack=stack)
    
        T_i = np.linalg.inv(T_i)
        
        T[0,0] = math.cos( math.acos( T[0,0] ) +  math.acos( T_i[0,0] ) )
        T[1,1] = math.cos( math.acos( T[1,1] ) + math.acos( T_i[1,1] ) )
        T[0,1] = -math.sin( math.asin( -T[0,1] ) + math.asin( -T_i[0,1] ) )
        T[1,0] = math.sin( math.asin( T[1,0] ) + math.asin( T_i[1,0] ) )
        T[0,2] += T_i[0,2]
        T[1,2] += T_i[1,2]
        
        #valid_fn_prev = valid_fn
        valid_sec = valid_sec_prev
        
    #T[0,2] = 0
    #T[1,2] = 0
    return T

def get_transformed_image(section, transformation='anchor', prev_section=-1):
    assert transformation in ['anchor', 'pairwise']

    fn = DataManager.metadata_cache['sections_to_filenames'][stack][section]
        
    img_fp = DataManager.get_image_filepath(stack=stack, section=section, resol='thumbnail', version='NtbNormalized')
    
    if transformation=='anchor':
        T = get_anchor_transform(stack, fn)
    elif transformation=='pairwise':
        assert prev_section!=-1
        prev_fn = DataManager.metadata_cache['sections_to_filenames'][stack][prev_section]
        T = get_pairwise_transform(stack, fn, prev_fn)
        
    img_transformed = apply_transform(stack, T, fn)
    
    return img_transformed, T

def apply_pairwise_transform(img):
    pass

class ImageViewer(QGraphicsView):
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
            self._zoom = 0
        else:
            print('RECT IS NULL')

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
        
    def paintOverlayImage(self, pixmap=None):
        painter = QPainter()
        painter.begin(image)
        painter.drawImage(0, 0, overlay)
        painter.end()

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
        
        self.valid_sections = DataManager.metadata_cache['valid_sections_all'][stack]
        self.sections_to_filenames = DataManager.metadata_cache['sections_to_filenames'][stack]
        self.curr_section = self.valid_sections[ len(self.valid_sections)/2 ]
        self.prev_section = self.getPrevValidSection( self.curr_section )
        self.next_section = self.getNextValidSection( self.curr_section )
        
        self.curr_T = None
        
        self.mode = 'view' 
        #self.mode = 'align' 
        
        self.transform_type = 'pairwise' # Can toggle to 'anchor'

        # Increasing this number will brighten the images
        self.curr_img_multiplier = 1
        self.prev_img_multiplier = 1
                
        self.initUI()
        
    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_body_upper = QGridLayout()
        self.grid_body = QGridLayout()
        self.grid_body_lower_align_mode = QGridLayout()
        self.grid_bottom = QGridLayout()
        self.grid_blank = QGridLayout()
        
        #self.setFixedSize(1600, 1100)
        self.resize(1600, 1100)
        
        ### VIEWER ### (Grid Body)
        self.viewer = ImageViewer(self)
        self.viewer.photoClicked.connect( self.photoClicked )
        
        ### Grid TOP ###
        # Static Text Field (Title)
        self.e1 = QLineEdit()
        self.e1.setValidator( QIntValidator() )
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont( self.font_h1 )
        self.e1.setReadOnly( True )
        self.e1.setText( "Quality Checker" )
        self.e1.setFrame( False )
        self.grid_top.addWidget( self.e1, 0, 0)
        # Button Text Field
        self.b_help = QPushButton("HELP")
        self.b_help.setDefault(True)
        self.b_help.setEnabled(True)
        self.b_help.clicked.connect(lambda:self.help_button_press(self.b_help))
        self.b_help.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,250);")
        self.grid_top.addWidget(self.b_help, 0, 1)
        
        ### Grid BODY UPPER ###
        # Static Text Field
        self.e2 = QLineEdit()
        self.e2.setAlignment(Qt.AlignCenter)
        self.e2.setFont( self.font_p1 )
        self.e2.setReadOnly( True )
        self.e2.setText( "Filename: " )
        self.e2.setStyleSheet("color: rgb(50,50,250); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget( self.e2, 0, 0)
        # Static Text Field
        self.e3 = QLineEdit()
        self.e3.setAlignment(Qt.AlignCenter)
        self.e3.setFont( self.font_p1 )
        self.e3.setReadOnly( True )
        self.e3.setText( "Section: " )
        self.e3.setStyleSheet("color: rgb(50,50,250); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget( self.e3, 0, 1)
        # Static Text Field
        self.e4 = QLineEdit()
        self.e4.setAlignment(Qt.AlignCenter)
        self.e4.setFont( self.font_p1 )
        self.e4.setReadOnly( True )
        self.e4.setText( "Filename: " )
        self.e4.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget( self.e4, 0, 2)
        # Static Text Field
        self.e5 = QLineEdit()
        self.e5.setAlignment(Qt.AlignCenter)
        self.e5.setFont( self.font_p1 )
        self.e5.setReadOnly( True )
        self.e5.setText( "Section: " )
        self.e5.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget( self.e5, 0, 3)
                
        ### Grid BODY ###
        # Custom VIEWER
        self.grid_body.addWidget( self.viewer, 0, 0)
        
        ### Grid BODY LOWER (align mode only) ###
        # Button Text Field
        self.b1 = QPushButton("Brighten blue image")
        self.b1.setDefault(True)
        self.b1.setEnabled(False)
        self.b1.clicked.connect(lambda:self.buttonPress(self.b1))
        self.b1.setStyleSheet("color: rgb(50,50,250); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b1, 0, 0)
        # Button Text Field
        self.b2 = QPushButton("Brighten red image")
        self.b2.setDefault(True)
        self.b2.setEnabled(False)
        self.b2.clicked.connect(lambda:self.buttonPress(self.b2))
        self.b2.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b2, 1, 0)
        # Button Text Field
        self.b_up = QPushButton("/\\")
        self.b_up.setDefault(True)
        self.b_up.setEnabled(False)
        self.b_up.clicked.connect(lambda:self.buttonPress(self.b_up))
        self.b_up.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_up, 0, 3)
        # Button Text Field
        self.b_left = QPushButton("<=")
        self.b_left.setDefault(True)
        self.b_left.setEnabled(False)
        self.b_left.clicked.connect(lambda:self.buttonPress(self.b_left))
        self.b_left.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_left, 1, 2)
        # Button Text Field
        self.b_down = QPushButton("\/")
        self.b_down.setDefault(True)
        self.b_down.setEnabled(False)
        self.b_down.clicked.connect(lambda:self.buttonPress(self.b_down))
        self.b_down.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_down, 1, 3)
        # Button Text Field
        self.b_right = QPushButton("=>")
        self.b_right.setDefault(True)
        self.b_right.setEnabled(False)
        self.b_right.clicked.connect(lambda:self.buttonPress(self.b_right))
        self.b_right.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_right, 1, 4)
        # Button Text Field
        self.b_clockwise = QPushButton("^--'")
        self.b_clockwise.setDefault(True)
        self.b_clockwise.setEnabled(False)
        self.b_clockwise.clicked.connect(lambda:self.buttonPress(self.b_clockwise))
        self.b_clockwise.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_clockwise, 0, 6)
        # Button Text Field
        self.b_cclockwise = QPushButton("'--^")
        self.b_cclockwise.setDefault(True)
        self.b_cclockwise.setEnabled(False)
        self.b_cclockwise.clicked.connect(lambda:self.buttonPress(self.b_cclockwise))
        self.b_cclockwise.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_cclockwise, 0, 7)
        # Button Text Field
        self.b_save_transform = QPushButton("Save Transformation")
        self.b_save_transform.setDefault(True)
        self.b_save_transform.setEnabled(False)
        self.b_save_transform.clicked.connect(lambda:self.buttonPress(self.b_save_transform))
        self.b_save_transform.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_save_transform, 1, 9)
        # Button Text Field
        self.b_done = QPushButton("DONE")
        self.b_done.setDefault(True)
        self.b_done.setEnabled(True)
        self.b_done.clicked.connect(lambda:self.buttonPress(self.b_done))
        self.b_done.setStyleSheet("color: rgb(0,0,0); background-color: rgb(200,250,250);")
        self.grid_body_lower_align_mode.addWidget(self.b_done, 1, 10)
        
        
        # Grid stretching
        self.grid_body_upper.setColumnStretch(0, 2)
        self.grid_body_upper.setColumnStretch(2, 2)
        
        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout( self.grid_top, 0, 0)
        self.supergrid.addLayout( self.grid_body_upper, 1, 0)
        self.supergrid.addLayout( self.grid_body, 2, 0)
        self.supergrid.addLayout( self.grid_body_lower_align_mode, 3, 0)
        self.supergrid.addLayout( self.grid_bottom, 4, 0)
        
        # Set layout and window title
        self.setLayout( self.supergrid )
        self.setWindowTitle("Q")
        
        # Loads self.curr_section as the current image and sets all fields appropriatly
        self.setCurrSection( self.curr_section )
        
    def help_button_press(self, button):
        info_text = "This GUI is used to align slices to each other. The shortcut commands are as follows: \n\n\
    -  `m`: Toggle between view mode (grayscale) and alignment mode (red & blue).\n\
    -  `[`: Go back one section. \n\
    -  `]`: Go forward one section. \n\n\
    \
    All changes must be done in alignment mode. Alignment mode will display the pairwise alignment between the current \
active section (red) and the previous section (blue). Using the buttons at the foot of the GUI, you can translate and \
rotate the active section (red) as well as brighten either the active or previous section. Adjust the red slice such \
that it is aligned to the blue slice as well as possible and press \"Save Transformation\".\n\n\
    \
    The grayscale images should all be aligned to one another. Please verify that all sections are aligned properly \
before you finish this step."
        
        QMessageBox.information( self, "Empty Field",
                    info_text)
        
        
    def loadImage(self):
        # Get filepath of "curr_section" and set it as viewer's photo
        fp = get_fp( self.curr_section, prep_id=1 )
        self.viewer.setPhoto( QPixmap( fp ) )
        self.curr_T = None
       # 
       # img, T = get_transformed_image( self.curr_section, 
       #                                 transformation='anchor', 
       #                                 prev_section=self.prev_section )
        
        
        #T = get_comulative_pairwise_transform( stack, 
        #               DataManager.metadata_cache['sections_to_filenames'][stack][self.curr_section] )
        #img = apply_transform( stack, T,  
        #               DataManager.metadata_cache['sections_to_filenames'][stack][self.curr_section])
        
        #height, width, channel = img.shape
        #bytesPerLine = 3 * width
        #qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
       # 
       # self.viewer.setPhoto( QPixmap( qImg ) )
        
    def loadImageThenNormalize(self):
        # Get filepath of "curr_section" and set it as viewer's photo
        fp = get_fp( self.curr_section, prep_id=1 )
        img = cv2.imread(fp) * 3
        
        height, width, channel = img.shape
        bytesPerLine = 3 * width
        qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        
        self.viewer.setPhoto( QPixmap( qImg ) )
        
    def loadImagesColored(self):
        # we want to load RED (current section) and BLUE (previous section) channels overlayed
        fp_curr_red = get_fp( self.curr_section )
        fp_prev_blue = get_fp( self.prev_section )
        # Load the untransformed images
        #img_curr_red = cv2.imread( fp_curr_red )
        #img_prev_blue = cv2.imread( fp_prev_blue )
        
        if self.transform_type=='anchor':
        # Load anchor-transformed images
            img_curr_red, T = get_transformed_image( self.curr_section, transformation='anchor' )
            img_prev_blue, Tb = get_transformed_image( self.prev_section, transformation='anchor' )
            self.curr_T = T
        elif self.transform_type=='pairwise' and self.curr_section>self.prev_section:
            # Load pairwise-transformed images
            # The current red image is transformed to the previous blue image
            img_curr_red, T = get_transformed_image( self.curr_section, 
                                                 transformation='pairwise', 
                                                 prev_section=self.prev_section )
            self.curr_T = T
            # Blue image does not change
            img_prev_blue = cv2.imread( fp_prev_blue )
        elif self.transform_type=='pairwise' and self.curr_section<self.prev_section:
            # In the case of wrapping (prev_section wrapps to the last section when curr_section is 0)
            #   We just load the red ad blue channels of curr_section making it appear purple
            self.curr_T = None
            
            img_curr_red = cv2.imread( get_fp( self.curr_section, prep_id=1 ) )
            img_prev_blue = cv2.imread( get_fp( self.curr_section, prep_id=1 ) )
        
        height_r, width_r, _ = img_curr_red.shape
        height_b, width_b, _ = img_prev_blue.shape
        new_height = max(height_r, height_b)
        new_width = max(width_r, width_b)
        
        img_combined = np.ones((new_height, new_width, 3))
        img_combined[0:height_r, 0:width_r, 0] += img_curr_red[:,:,0]
        img_combined[0:height_b, 0:width_b, 2] += img_prev_blue[:,:,0]
        
        img_combined = np.array(img_combined, dtype=np.uint8) # This line only change the type, not values
        
        # Create a "qImg" which allows you to create a QPixmap from a matrix
        bytesPerLine = 3 * new_width
        qImg = QImage(img_combined.data*2, new_width, new_height, 
                      bytesPerLine, QImage.Format_RGB888)
        
        pixmap = QPixmap(qImg)                                                                                                                                                                               
        #pixmap = pixmap.scaled(640,400, Qt.KeepAspectRatio) 
        
        self.viewer.setPhoto( pixmap )
        
    def transformImagesColored(self):
        # we want to load RED (current section) and BLUE (previous section) channels overlayed
        fp_curr_red = get_fp( self.curr_section )
        fp_prev_blue = get_fp( self.prev_section )
                
        if self.transform_type=='anchor':
        # Load anchor-transformed images
            img_curr_red = apply_transform( stack, self.curr_T,  
                                 DataManager.metadata_cache['sections_to_filenames'][stack][self.curr_section])
            img_prev_blue, Tb = get_transformed_image( self.prev_section, transformation='anchor' )
        elif self.transform_type=='pairwise':
            # Load pairwise-transformed images
            # The current red image is transformed to the previous blue image
            img_curr_red = apply_transform(stack, self.curr_T,  
                                 DataManager.metadata_cache['sections_to_filenames'][stack][self.curr_section])
            # Blue image does not change
            img_prev_blue = cv2.imread( fp_prev_blue )
        
        height_r, width_r, _ = img_curr_red.shape
        height_b, width_b, _ = img_prev_blue.shape
        new_height = max(height_r, height_b)
        new_width = max(width_r, width_b)
        
        img_combined = np.ones((new_height, new_width, 3))
        img_combined[0:height_r, 0:width_r, 0] += img_curr_red[:,:,0]*self.curr_img_multiplier
        img_combined[0:height_b, 0:width_b, 2] += img_prev_blue[:,:,0]*self.prev_img_multiplier
        
        img_combined = np.array(img_combined, dtype=np.uint8) # This line only change the type, not values
        
        # Create a "qImg" which allows you to create a QPixmap from a matrix
        bytesPerLine = 3 * new_width
        qImg = QImage( img_combined.data*2, new_width, new_height, 
                      bytesPerLine, QImage.Format_RGB888)
        
        pixmap = QPixmap(qImg)                                                                                                                                                                               
        #pixmap = pixmap.scaled(640,400, Qt.KeepAspectRatio) 
        
        self.viewer.setPhoto( pixmap )
        
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
        #print(key)
        
        if key==91: # [
            self.setCurrSection( self.getPrevValidSection( self.curr_section ) )
            
        elif key==93: # ]
            self.setCurrSection( self.getNextValidSection( self.curr_section ) )
            
        elif key==81: # Q
            self.pixInfo()
            
        elif key==77: # M
            self.toggleMode()
            
        else:
            print(key)
            
    def setCurrSection(self, section=-1):
        """
        Sets the current section to the section passed in.
        
        Will automatically update curr_section, prev_section, and next_section.
        Updates the header fields and loads the current section image.
        
        """
        if section==-1:
            section = self.curr_section
        
        # Update curr, prev, and next section
        self.curr_section = section
        self.prev_section = self.getPrevValidSection( self.curr_section )
        self.next_section = self.getNextValidSection( self.curr_section )
        # Update the section and filename at the top
        self.updateCurrHeaderFields()
        self.updatePrevHeaderFields()
        
        self.curr_img_multiplier = 1
        self.prev_img_multiplier = 1
            
        if self.mode=='view':
            self.loadImage()
            self.toggle_align_buttons( enabled=False )
            
        elif self.mode=='align':
            self.loadImagesColored()
            
            self.toggle_align_buttons( enabled=True )
        
    def toggleMode(self):
        if self.mode=='view':
            self.mode = 'align'
        elif self.mode=='align':
            self.mode = 'view'
        self.setCurrSection()
            
    def buttonPress(self, button):
        # Brighten an image
        if button in [self.b1, self.b2]:
            if button==self.b1:
                self.prev_img_multiplier += 1
                if self.prev_img_multiplier > 5:
                    self.prev_img_multiplier = 1
            if button==self.b2:
                self.curr_img_multiplier += 1
                if self.curr_img_multiplier > 5:
                    self.curr_img_multiplier = 1
        
        # Translate the red image and update T matrix
        if button in [self.b_right, self.b_left, self.b_up, self.b_down]:
            if button==self.b_right:
                self.curr_T[0,2] += 3
            if button==self.b_left:
                self.curr_T[0,2] -= 3
            if button==self.b_up:
                self.curr_T[1,2] -= 3
            if button==self.b_down:
                self.curr_T[1,2] += 3
            #self.transformImagesColored()
        
        # Rotate the red image and update T matrix
        if button in [self.b_clockwise, self.b_cclockwise]:
            if button==self.b_clockwise:
                degrees = 0.3
            if button==self.b_cclockwise:
                degrees = -0.3
            # Update matrix's rotation fields
            self.curr_T[0,0] = math.cos( math.acos(self.curr_T[0,0]) +  degrees*(math.pi/180) )
            self.curr_T[1,1] = math.cos( math.acos(self.curr_T[1,1]) + degrees*(math.pi/180) )
            self.curr_T[0,1] = -math.sin( math.asin(-self.curr_T[0,1]) + degrees*(math.pi/180) )
            self.curr_T[1,0] = math.sin( math.asin(self.curr_T[1,0]) + degrees*(math.pi/180) )
            
        if button==self.b_save_transform:
            self.saveCurrTransform()
            self.update_prep1_images()
            
        if button==self.b_done:
            sys.exit( app.exec_() )
        
        self.transformImagesColored()
        
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
    
    def toggle_align_buttons(self, enabled):
        self.b1.setEnabled( enabled )
        self.b2.setEnabled( enabled )
        self.b_right.setEnabled( enabled )
        self.b_left.setEnabled( enabled )
        self.b_up.setEnabled( enabled )
        self.b_down.setEnabled( enabled )
        self.b_clockwise.setEnabled( enabled )
        self.b_cclockwise.setEnabled( enabled )
        self.b_save_transform.setEnabled( enabled )
        
    def updateCurrHeaderFields(self):
        #self.e2.setText( "Filename: "+str(self.sections_to_filenames[self.curr_section]) )
        #self.e3.setText( "Section: "+str(self.curr_section) )
        self.e4.setText( str(self.sections_to_filenames[self.curr_section]) )
        self.e5.setText( str(self.curr_section) )
        
    def updatePrevHeaderFields(self):
        self.e2.setText( str(self.sections_to_filenames[self.prev_section]) )
        self.e3.setText( str(self.prev_section) )
        
    def update_prep1_images(self):
        stain = stack_metadata[stack]['stain'].lower()
        version = stain_to_metainfo[stain]['img_version_1']
        create_input_spec_ini_all( name='input_spec.ini', \
            stack=stack, prep_id='None', version=version, resol='thumbnail')
        
        # Call "compose" to regenerate the csv file
        command = ['python', 'compose_v3.py', 'input_spec.ini', '--op', 'from_none_to_aligned']
        completion_message = 'Finished creating transforms to anchor csv file.'
        call_and_time( command, completion_message=completion_message)
        
        # Apply transformations from csv and save as prep1 images
        command = ['python', 'warp_crop_v3.py','--input_spec', 'input_spec.ini', 
                   '--op_id', 'from_none_to_padded','--njobs','8','--pad_color', get_padding_color(stack)]
        completion_message = 'Finished transformation to padded (prep1).'
        call_and_time( command, completion_message=completion_message)
        
    def saveCurrTransform(self):
        if self.transform_type=='pairwise':
            stack_root_dir = os.path.join( os.environ['ROOT_DIR'], 'CSHL_data_processed', stack )
            curr_section_fn = self.sections_to_filenames[self.curr_section]
            prev_section_fn = self.sections_to_filenames[self.prev_section]


            custom_tf_txt_fn = os.path.join(stack_root_dir, stack+'_custom_transforms', 
                                        curr_section_fn + '_to_' + prev_section_fn, 
                                        curr_section_fn + '_to_' + prev_section_fn + '_customTransform.txt')
            custom_tf_img_fn = os.path.join(stack_root_dir, stack+'_custom_transforms', 
                                        curr_section_fn + '_to_' + prev_section_fn, 
                                        curr_section_fn + '_alignedTo_' + prev_section_fn + '.tif')
            T = self.curr_T

            # Saves the transformed image since we gave a specific output_fp
            apply_transform( stack, self.curr_T, self.sections_to_filenames[self.curr_section], 
                            output_fp=custom_tf_img_fn )

            with open(custom_tf_txt_fn, 'w') as file:
                file.write( str(T[0,0])+' '+str(T[0,1])+' '+str(T[0,2])+' '+\
                            str(T[1,0])+' '+str(T[1,1])+' '+str(T[1,2]) )
        else:
            pass
        
                    
def close_gui():
    #ex.hide()
    sys.exit( app.exec_() )

def main():
    
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Mask Editing GUI')
    parser.add_argument("stack", type=str, help="stack name")
    args = parser.parse_args()
    global stack
    stack = args.stack
    
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
