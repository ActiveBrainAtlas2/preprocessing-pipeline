import os
import sys
import subprocess
import argparse

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QPushButton, QMessageBox

from utilities.a_driver_utilities import (get_current_step_from_progress_ini, set_step_completed_in_progress_ini,
                                          get_prep5_limits_from_prep1_thumbnail_masks)

from utilities.metadata import stack_metadata, stain_to_metainfo
from utilities.utilities_pipeline_status import get_pipeline_status, all_img_files_present
from utilities.data_manager_v2 import DataManager

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Setup main page')
parser.add_argument("stack", type=str, help="stack name")
args = parser.parse_args()
stack = args.stack

def format_grid_button_initial( button ):
    button.setDefault( True )
    button.setEnabled(True)
    button.setStyleSheet('QPushButton { \
                          background-color: #FDB0B0; \
                          color: black; \
                          border-radius: 15px; \
                          font-size: 18px;}')
    button.setMinimumSize(QSize(50, 40))
    
def format_grid_button_cantStart( button ):
    button.setEnabled(False)
    button.setStyleSheet('QPushButton { \
                          background-color: #868686; \
                          color: black; \
                          border-radius: 15px; \
                          font-size: 18px;}')

def format_grid_button_completed( button ):
    #button.setEnabled(False)
    button.setStyleSheet('QPushButton { \
                          background-color: #B69696; \
                          color: black; \
                          border-radius: 15px; \
                          font-size: 18px;}')

class init_GUI(QWidget):
    def __init__(self, parent = None):
        super(init_GUI, self).__init__(parent)
        self.font1 = QFont("Arial",16)
        self.font2 = QFont("Arial",12)

        # Stack specific info, determined from dropdown menu selection
        self.stack = ""
        self.stain = ""
        
        self.curr_step = ""
        
        self.initUI()

    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_buttons = QGridLayout()
        self.grid_bottom = QGridLayout()
        
        #self.setFixedSize(1000, 450)
        self.resize(1000, 450)

        ### Grid Top (1 row) ###
        # Static Text Field
        self.e1 = QLineEdit()
        self.e1.setValidator( QIntValidator() )
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont( self.font1 )
        self.e1.setReadOnly( True )
        self.e1.setText( "Mask Step: Main Page" )
        self.e1.setFrame( False )
        self.grid_top.addWidget( self.e1, 0, 0)

        ### Grid Buttons ###
        # Button
        self.b_1 = QPushButton("1) Create Initial Masks")
        format_grid_button_initial( self.b_1 )
        self.b_1.clicked.connect( lambda:self.button_grid_push(self.b_1) )
        self.grid_buttons.addWidget( self.b_1, 0, 0)
        # Button
        self.b_2 = QPushButton("2) Completed Mask Generation Script")
        format_grid_button_initial( self.b_2 )
        self.b_2.clicked.connect( lambda:self.button_grid_push(self.b_2) )
        self.grid_buttons.addWidget( self.b_2, 1, 0)
        # Button
        self.b_3 = QPushButton("3) Correct Complete Masks")
        format_grid_button_initial( self.b_3 )
        self.b_3.clicked.connect( lambda:self.button_grid_push(self.b_3) )
        self.grid_buttons.addWidget( self.b_3, 2, 0)
        # Button
        self.b_4 = QPushButton("4) Create Mask Image Files Script")
        format_grid_button_initial( self.b_4 )
        self.b_4.clicked.connect( lambda:self.button_grid_push(self.b_4) )
        self.grid_buttons.addWidget( self.b_4, 3, 0)
        
        ### Grid Bottom ###
        # Button Text Field
        self.b_exit = QPushButton("Exit")
        self.b_exit.setDefault(True)
        self.b_exit.clicked.connect(lambda:self.button_push(self.b_exit))
        self.grid_bottom.addWidget(self.b_exit, 0, 4)

        #self.grid_buttons.setColumnStretch(1, 3)
        #self.grid_buttons.setRowStretch(1, 2)

        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout( self.grid_top, 0, 0)
        self.supergrid.addLayout( self.grid_buttons, 1, 0)
        self.supergrid.addLayout( self.grid_bottom, 2, 0)

        # Set layout and window title
        self.setLayout( self.supergrid )
        self.setWindowTitle("Align to Active Brainstem Atlas - Setup Page")

        # Update interactive windows
        self.updateFields()
        
        # Center the GUI
        self.center()
    
    def updateFields(self):
        # Set stack-specific variables
        self.stack = stack
        self.stain = stack_metadata[stack]
        try:
            self.stain = stack_metadata[ self.stack ]['stain']
            # Check the brains_info/STACK_progress.ini file for which step we're on
            self.curr_step = get_current_step_from_progress_ini( self.stack )
            # Disable all grid buttons except for the one corresponding to our current step
            self.format_grid_buttons()
        # If there are no stacks/brains that have been started
        except KeyError:
            for grid_button in [self.b_1, self.b_2, self.b_3, self.b_4]:
                format_grid_button_cantStart( grid_button )
        
    def format_grid_buttons(self):
        """
        Locates where you are in the pipeline by reading the brains_info/STACK_progress.ini
        
        Buttons corresponding to previous steps are marked as "completed", buttons corresponding
        to future steps are marked as "unpressable" and are grayed out.
        """
        curr_step = self.curr_step
        
        if '3-1' in curr_step:
            active_button = self.b_1
        elif '3-2' in curr_step:
            active_button = self.b_2
        elif '3-3' in curr_step:
            active_button = self.b_3
        elif '3-4' in curr_step:
            active_button = self.b_4
        else:
            active_button = None
            print(curr_step)
            
        passed_curr_step = False
        for grid_button in [self.b_1, self.b_2, self.b_3, self.b_4]:
            if not passed_curr_step and grid_button != active_button:
                format_grid_button_completed( grid_button )
            elif grid_button == active_button:
                passed_curr_step = True
                format_grid_button_initial(active_button)
            elif passed_curr_step and grid_button != active_button:
                format_grid_button_cantStart( grid_button )
                        
    def button_grid_push(self, button):
        """
        If any of the "grid" buttons are pressed, this is the callback function.
        
        In this case, "grid" buttons have a one-to_one correspondance to the steps in the pipeline.
        The completion of each step means you move onto the next one.
        """
        # User creates initial masks
        if button == self.b_1:
            subprocess.call(['python', 'mask_editing_tool.py',
                             stack, stain_to_metainfo[self.stain.lower()]['img_version_1']  ])
            
            # Mark this step as complete if these two files were created
            fp_to_check_1 = os.path.join( DataManager.get_images_root_folder(self.stack),
                                         self.stack+'_prep1_thumbnail_initSnakeContours.pkl' )
            fp_to_check_2 = os.path.join( DataManager.get_images_root_folder(self.stack),
                                         self.stack+'_prep1_thumbnail_anchorInitSnakeContours.pkl' )
            if os.path.exists( fp_to_check_1 ) and os.path.exists( fp_to_check_2 ):
                set_step_completed_in_progress_ini( self.stack, '3-1_mask_initial_contours')
            
        # Automatic mask generation
        elif button == self.b_2:
            try:
                QMessageBox.about(self, "Popup Message", "This operation is expected to take at least 6 hours.")
                subprocess.call(['python','a_script_preprocess_3.py', self.stack, self.stain])
                set_step_completed_in_progress_ini( self.stack, '3-2_mask_scripts_1')
            except Exception as e:
                sys.stderr.write( str(e) )
                
        # Correct auto-generated masks
        elif button == self.b_3:
            try:
                subprocess.call(['python', 'mask_editing_tool.py',
                             stack, stain_to_metainfo[self.stain.lower()]['img_version_1']  ])
                # Mark this step as complete if all masks files exist
                if all_img_files_present( self.stack, prep_id=1, version='mask', resol='thumbnail' ):
                    set_step_completed_in_progress_ini( self.stack, '3-3_mask_correct_contours')
            except Exception as e:
                sys.stderr.write( str(e) )
                
        # Run automatic scripts
        elif button == self.b_4:
            try:
                QMessageBox.about(self, "Popup Message", "This operation is expected to take at least 12 hours.")
                # Run script 4
                subprocess.call(['python','a_script_preprocess_4.py', self.stack, self.stain])
                # Run script 5 (automatically finds the bounds first)
                rostral_lim, caudal_lim, dorsal_lim, ventral_lim = get_prep5_limits_from_prep1_thumbnail_masks(self.stack)
                command = ['python', 'a_script_preprocess_5.py', self.stack, self.stain, '-l', 
                           str(rostral_lim), str(caudal_lim), str(dorsal_lim), str(ventral_lim)]
                subprocess.call( command )
                
                progress = get_pipeline_status( self.stack )
                if not progress=='a_script_preprocess_4' and not progress=='a_script_preprocess_5':
                    set_step_completed_in_progress_ini( self.stack, '3-4_mask_scripts_2')
                    
            except Exception as e:
                sys.stderr.write( str(e) )
            
        self.updateFields()
            
    def button_push(self, button):
        """
        Secondary button callback function
        """
        if button == self.b_exit:
            sys.exit( app.exec_() )
     
    def center(self):
        """
        This function simply aligns the GUI to the center of your monitor.
        """
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber( QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())
            
    def closeEvent(self, event):
        sys.exit( app.exec_() )
        #close_main_gui( ex, reopen=True )
        
def main():
    global app 
    app = QApplication( sys.argv )
    
    global ex
    ex = init_GUI()
    ex.show()
    sys.exit( app.exec_() )

if __name__ == '__main__':
    main()
