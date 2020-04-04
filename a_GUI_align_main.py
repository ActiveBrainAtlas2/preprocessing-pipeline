import os, sys
import subprocess
import argparse

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QPushButton


sys.path.append(os.path.join(os.getcwd(),'utilities'))
from utilities.a_driver_utilities import get_current_step_from_progress_ini, set_step_completed_in_progress_ini
from utilities.sqlcontroller import SqlController


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
    def __init__(self, stack, parent = None):
        super(init_GUI, self).__init__(parent)
        self.font1 = QFont("Arial",16)
        self.font2 = QFont("Arial",12)

        # Stack specific info, determined from dropdown menu selection
        self.stack = stack
        self.curr_step = ""
        self.sqlController = SqlController()
        self.sqlController.get_animal_info(self.stack)
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
        self.e1.setText( "Align Step: Main Page" )
        self.e1.setFrame( False )
        self.grid_top.addWidget( self.e1, 0, 0)

        ### Grid Buttons ###
        # Button
        self.b_1 = QPushButton("1) Correct automatic alignments")
        format_grid_button_initial( self.b_1 )
        self.b_1.clicked.connect( lambda:self.button_grid_push(self.b_1) )
        self.grid_buttons.addWidget( self.b_1, 0, 0)
        
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
        self.setWindowTitle("Align to Active Brainstem Atlas - Aligning Slices Page")

        # Update interactive windows
        self.updateFields()
        
        # Center the GUI
        self.center()
    
    def updateFields(self):        
        # Set stack-specific variables
        try:
            self.stain = self.sqlController.histology.counterstain
            # Check the brains_info/STACK_progress.ini file for which step we're on
            self.curr_step = get_current_step_from_progress_ini( self.stack )
            # Disable all grid buttons except for the one corresponding to our current step
            self.format_grid_buttons()
        # If there are no stacks/brains that have been started
        except KeyError:
            for grid_button in [self.b_1]:
                format_grid_button_cantStart( grid_button )
        
    def format_grid_buttons(self):
        """
        Locates where you are in the pipeline by reading the brains_info/STACK_progress.ini
        
        Buttons corresponding to previous steps are marked as "completed", buttons corresponding
        to future steps are marked as "unpressable" and are grayed out.
        """
        curr_step = self.curr_step
        
        if '2_align' in curr_step:
            active_button = self.b_1
        else:
            active_button = None
            print(curr_step)
            
        passed_curr_step = False
        for grid_button in [self.b_1]:
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
        # Alignment Correction GUI
        if button == self.b_1:
            subprocess.call(['python','a_GUI_correct_alignments.py', self.stack])
            set_step_completed_in_progress_ini( self.stack, '2_align')
            
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
        sys.exit(app.exec_())
    else:
        print('There are no sections to work with.')


if __name__ == '__main__':
    main()
