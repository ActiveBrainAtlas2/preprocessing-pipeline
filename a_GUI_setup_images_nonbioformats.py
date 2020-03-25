import os, sys
import subprocess
import argparse
import json

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QTextEdit, QPushButton

#import tkFileDialog as filedialog
#from Tkinter import *

from tkinter import filedialog
from tkinter import *



sys.path.append(os.path.join(os.getcwd(),'utilities'))
#print(sys.path)
from utilities.metadata import ON_DOCKER
from utilities.a_driver_utilities import set_step_completed_in_progress_ini, call_and_time
from data_manager_v2 import DataManager

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='')
parser.add_argument("stack", type=str, help="The name of the stack")
parser.add_argument("input_filetype", type=str, help="The name of the stack")
args = parser.parse_args()
stack = args.stack
input_filetype = args.input_filetype

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

class init_GUI(QWidget):
    def __init__(self, parent = None):
        super(init_GUI, self).__init__(parent)
        self.font_header = QFont("Arial",32)
        self.font_sub_header = QFont("Arial",16)
        self.font_left_col = QFont("Arial",16)
        
        self.stack = stack
        
        self.filepath_sfns = ""
        self.filepath_sfns_folder = ""
        self.filepath_img = ""
        self.filepath_img_folder = ""
        
        self.initUI()
        
    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_body = QGridLayout()
        
        #self.setFixedSize(800, 350)
        self.resize(800, 350)
        
        ### Grid TOP (1 row) ###
        # Static Text Field
        self.e1 = QLineEdit()
        self.e1.setValidator( QIntValidator() )
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont( self.font_header )
        self.e1.setReadOnly( True )
        self.e1.setText( "Select File Locations" )
        self.e1.setFrame( False )
        self.grid_top.addWidget( self.e1, 0, 0)
        # Static Text Field
        self.e1 = QTextEdit()
        self.e1.setFont( self.font_sub_header )
        self.e1.setReadOnly( True )
        self.e1.setText( "You must select your sorted filenames (.txt) file created for "+self.stack+
                        ". This must be a text file formatted as described in the github page.\n"+
                       "Your raw image files are expected to be in "+input_filetype+" format and must all be "+
                       "located inside the same directory. Each filename in the sorted filenames must "+
                       "appear in the filename of a raw image file.")
        self.grid_top.addWidget( self.e1, 1, 0)
        
        ### Grid BODY (1 row) ###
        # Static Text Field
        self.e2 = QLineEdit()
        self.e2.setValidator( QIntValidator() )
        self.e2.setAlignment(Qt.AlignRight)
        self.e2.setFont( self.font_left_col )
        self.e2.setReadOnly( True )
        self.e2.setText( "Select sorted_filenames.txt file:" )
        self.e2.setFrame( False )
        self.grid_body.addWidget( self.e2, 0, 0)
        # Static Text Field
        self.e3 = QLineEdit()
        self.e3.setValidator( QIntValidator() )
        #self.e3.setMaxLength(50)
        self.e3.setAlignment(Qt.AlignRight)
        self.e3.setFont( self.font_left_col )
        self.e3.setReadOnly( True )
        self.e3.setText( "Select raw jp2 or tiff files:" )
        self.e3.setFrame( False )
        self.grid_body.addWidget( self.e3, 1, 0)
        
        # Button Text Field
        self.b2 = QPushButton("Select sorted filenames")
        self.b2.setDefault(True)
        self.b2.clicked.connect(lambda:self.buttonPress_selectSFS(self.b2))
        self.b2.setStyleSheet('QPushButton {background-color: #A3C1DA; color: black;}')
        self.grid_body.addWidget(self.b2, 0, 1)
        # Button Text Field
        self.b3 = QPushButton("Select one image file")
        self.b3.setDefault(True)
        self.b3.clicked.connect(lambda:self.buttonPress_selectIMG(self.b3))
        self.b3.setStyleSheet('QPushButton {background-color: #A3C1DA; color: black;}')
        self.grid_body.addWidget(self.b3, 1, 1)
        
        # Static Text Field
        self.e7 = QLineEdit()
        self.e7.setValidator( QIntValidator() )
        self.e7.setAlignment(Qt.AlignRight)
        self.e7.setFont( self.font_left_col )
        self.e7.setReadOnly( True )
        self.e7.setText( "Push `Submit` when finished" )
        self.e7.setFrame( False )
        self.grid_body.addWidget( self.e7, 6, 0)
        # Button Text Field
        self.b1 = QPushButton("Submit")
        self.b1.setDefault(True)
        self.b1.clicked.connect(lambda:self.buttonPressSubmit(self.b1))
        self.grid_body.addWidget(self.b1, 6, 1)
        
        #self.grid_top.setColumnStretch(1, 3)
        #self.grid_top.setRowStretch(1, 3)
        
        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout( self.grid_top, 0, 0)
        self.supergrid.addLayout( self.grid_body, 1, 0)
        
        # Set layout and window title
        self.setLayout( self.supergrid )
        self.setWindowTitle("Select tiffs/jp2 images")
        
    def validateEntries(self):
        if self.filepath_sfns=="" and self.filepath_img=="":
            return False
        if self.filepath_img=="":
            return False
        
        return True
        
    def buttonPressSubmit(self, button):
        if button == self.b1:
            validated = self.validateEntries()
            if validated:
                # Create parent folders if necessary
                create_parent_folder_for_files( self.stack )
                
                # Copy over sorted filenames if it was selected
                if self.filepath_sfns=="":
                    pass
                else:
                    # Copy sorted filenames file to proper lcoation
                    copy_over_sorted_filenames( self.stack, self.filepath_sfns )
                
                # Copy image files to proper location
                if '.jp2' in self.filepath_img:
                    self.e1.setText( "The jp2 images are being converted and copied, "+
                        "The process is expected to take 60-90 seconds per image.\n\n"+
                        "Please revisit this GUI in a few hours.")
                    self.e1.repaint()
                    copy_over_jp2_files( self.stack, self.filepath_img, self.filepath_img_folder )
                elif '.tif' in self.filepath_img:
                    self.e1.setText( "The tiff images are now being renamed and copied. This will take about 30s - 1m per image.")
                    self.e1.repaint()
                    copy_over_tif_files( self.stack, self.filepath_img_folder )
                    
                self.finished()
                                
    def buttonPress_selectSFS(self, button):
        if button == self.b2:
            fp = get_selected_fp( default_filetype=[("text files","*.txt"),("all files","*.*")] )
            self.filepath_sfns = fp
            self.filepath_sfns_folder = fp[0:max(loc for loc, val in enumerate(fp) if val == '/')]
            validated, err_msg = validate_sorted_filenames( fp )
            if validated:
                self.e2.setText( fp ) 
            else:
                self.e2.setText( err_msg )
                self.filepath_sfns = ""
                
    def buttonPress_selectIMG(self, button):
        if button == self.b3:
            if self.filepath_sfns_folder != '':
                fp = get_selected_fp( initialdir = self.filepath_sfns_folder,
                                     default_filetype=[("tiff files","*.tif*"), ("jp2 files","*.jp2"), ("all files","*.*")] )
            else:
                fp = get_selected_fp( default_filetype=[("tiff files","*.tif*"), ("jp2 files","*.jp2"), ("all files","*.*")] )
            self.filepath_img = fp
            self.filepath_img_folder = fp[0:max(loc for loc, val in enumerate(fp) if val == '/')]
            #validate_chosen_images()
            self.e3.setText( self.filepath_img_folder ) 
            
    def closeEvent(self, event):
        #close_main_gui( ex )
        sys.exit( app.exec_() )
        
    def finished(self):
        #if self.filepath_sfns != "":
            #set_step_completed_in_progress_ini( stack, '1-4_setup_sorted_filenames')
        
        subprocess.call( ['python', 'a_script_preprocess_setup.py', stack, 'unknown'] )
        
        set_step_completed_in_progress_ini( stack, '1-2_setup_images')
        
        close_gui()
        #close_main_gui( ex )
        #sys.exit( app.exec_() )
            
def create_parent_folder_for_files( stack ):
    try:
        raw_fp = DataManager.get_image_filepath_v2(stack, None, version=None, resol="raw", fn='$')
        raw_fp = raw_fp[0:raw_fp.index('$')]
        os.makedirs( raw_fp )
    except:
        pass
            
def copy_over_jp2_files( stack, raw_jp2_input_fn_fp, raw_jp2_input_fp ):
    # Use name of jp2 image to find how the resolution is encoded
    if 'raw' in raw_jp2_input_fn_fp:
        resolution = '_raw'
    elif 'lossless' in raw_jp2_input_fn_fp:
        resolution = '_lossless'
    else:
        resolution = ''
    
    # CONVERT *.jp2 to *.tif
    json_fn = stack+'_raw_input_spec.json'
    # Create the data file necessary to run the jp2_to_tiff script
    json_data = [{"version": None, \
                 "resolution": "raw", \
                 "data_dirs": raw_jp2_input_fp, \
                 "filepath_to_imageName_mapping": raw_jp2_input_fp+"/(.*?)"+resolution+".jp2", \
                 "imageName_to_filepath_mapping": raw_jp2_input_fp+"/%s"+resolution+".jp2"}]
    with open( json_fn, 'w') as outfile:
        json.dump( json_data, outfile)
        
    command = ["python", "jp2_to_tiff.py", stack, json_fn]
    completion_message = 'Completed converting and copying jp2 to tiff for all files in folder.'
    call_and_time( command, completion_message=completion_message)
    
def copy_over_tif_files( stack, raw_tiff_input_fp ):
    raw_tiff_input_fns = os.listdir( raw_tiff_input_fp )
        
    # Make STACKNAME_raw/ folder
    try:
        raw_fp = DataManager.get_image_filepath_v2(stack, None, version=None, resol="raw", fn="$")
        os.makedirs( raw_fp[:raw_fp.index('$')] )
    except Exception as e:
        #print(e)
        pass

    filenames_list = DataManager.load_sorted_filenames(stack)[0].keys()
    # Rename and copy over all tiff files in the selected folder
    for fn in filenames_list:
        for raw_tiff_input_fn in raw_tiff_input_fns:
            if fn in raw_tiff_input_fn:
                old_fp = os.path.join( raw_tiff_input_fp, raw_tiff_input_fn )
                new_fp = DataManager.get_image_filepath_v2(stack, None, version=None, resol="raw", fn=fn)
                command = ["cp", old_fp, new_fp]
                completion_message = 'Finished copying and renaming tiff file into the proper location.'
                call_and_time( command, completion_message=completion_message)
                    
def copy_over_sorted_filenames( stack, sfns_input_fp ):
    correct_sorted_fns_fp = DataManager.get_sorted_filenames_filename(stack)
    command = ["cp", sfns_input_fp, correct_sorted_fns_fp]
    completion_message = 'Successfully copied sorted_filenames.txt over.'
    call_and_time( command, completion_message=completion_message)
    
def load_sorted_filenames( fp ):
    '''
        load_sorted_filenames( stack ) returns a list of section names
        and their associated section numbers
    '''
    #fn = stack+'_sorted_filenames.txt'
    
    file_sfns = open( fp, 'r')
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
            section_name = line[ 0 : space_index ]
            section_number = line[ space_index+1 : ]
            section_names.append( section_name )
            section_numbers.append( section_number )
    return section_names, section_numbers

def validate_sorted_filenames( fp ):
    section_names, section_numbers = load_sorted_filenames( fp )
    
    if len(section_names) != len(set(section_names)):
        return False, "Error: A section name appears multiple times"
    if len(section_numbers) != len(set(section_numbers)):
        return False, "Error: A section number appears multiple times"
    
    return True, ""

def get_selected_fp( initialdir='/', default_filetype=("jp2 files","*.jp2") ):
    # initialdir=os.environ['ROOT_DIR'
    # Use tkinter to ask user for filepath to jp2 images
    #from tkinter import filedialog
    #from tkinter import *
    if ON_DOCKER:
        initialdir = '/mnt/computer_root/'
        
    root = Tk()
    root.filename = filedialog.askopenfilename(initialdir = initialdir,\
                                                title = "Select file",\
                                                filetypes = default_filetype)
    fn = root.filename
    root.destroy()
    return fn
    
def close_gui():
    sys.exit( app.exec_() )
#    ex.hide()
    #sys.exit()
    
def main():
    global app 
    app = QApplication( sys.argv )
    
    global ex
    ex = init_GUI()
    ex.show()
    sys.exit( app.exec_() )

if __name__ == '__main__':
    main()
