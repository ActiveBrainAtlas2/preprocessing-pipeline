import sys
import argparse

from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QPushButton, QComboBox, QMessageBox

from utilities.metadata import ordered_pipeline_steps
from utilities.a_driver_utilities import get_current_step_from_progress_ini, revert_to_prev_step

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='Select a step to reqind to')
parser.add_argument("stack", type=str, help="stack name")
args = parser.parse_args()
stack = args.stack

curr_step = get_current_step_from_progress_ini( stack )
prev_steps = []

for step in ordered_pipeline_steps:
    if step==curr_step:
        prev_steps.append(step)
        break
    prev_steps.append(step)
    

class init_GUI(QWidget):
    def __init__(self, parent = None):
        super(init_GUI, self).__init__(parent)
        self.font1 = QFont("Arial",16)
        self.font2 = QFont("Arial",12)

        # Stack specific info, determined from dropdown menu selection
        self.stack = ""
        
        self.curr_step = curr_step
        
        self.initUI()

    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid = QGridLayout()
        
        #self.setFixedSize(400, 200)
        self.resize(400, 200)

        ### Grid Top (1 row) ###
        # Static Text Field
        self.e1 = QLineEdit()
        self.e1.setValidator( QIntValidator() )
        self.e1.setMaxLength(6)
        self.e1.setAlignment(Qt.AlignRight)
        self.e1.setFont( self.font1 )
        self.e1.setReadOnly( True )
        self.e1.setText( "Select the step you'd like to start at:" )
        self.e1.setFrame( False )
        self.grid.addWidget( self.e1, 0, 0)
        # Dropbown Menu (ComboBox) for selecting Stack
        self.cb = QComboBox()
        self.cb.addItems( prev_steps )
        self.cb.setFont( self.font1 )
        #self.cb.currentIndexChanged.connect( self.updateFields )
        self.grid.addWidget(self.cb, 1, 0)
        # Button
        self.b_done = QPushButton("Done")
        #format_grid_button_initial( self.b_done )
        self.b_done.clicked.connect( lambda:self.button_push(self.b_done) )
        self.grid.addWidget( self.b_done, 2, 0)

        # Set layout and window title
        self.setLayout( self.grid )
        self.setWindowTitle("Align to Active Brainstem Atlas - Main Page")
        
        # Center the GUI
        self.center()
        
    def button_push(self, button):
        """
        Button callback function
        """
        if button == self.b_done:
            step_selection = self.cb.currentText()
            
            
            msgBox = QMessageBox()
            text = 'Are you sure you want to start the pipeline from this step?\n\n'
            text += 'This will overwrite any data past this step as you run the pipeline.'
            msgBox.setText( text )
            msgBox.addButton( QPushButton('No'), QMessageBox.NoRole)
            msgBox.addButton( QPushButton('Yes'), QMessageBox.YesRole)
            ret = msgBox.exec_()
            print(ret)
            
            # Yes
            if ret==1:
                #subprocess.call(['python', 'revert_to_prev_step.py', stack, step_selection)])
                revert_to_prev_step(stack, step_selection)
                sys.exit( app.exec_() )
            # No
            elif ret==0:
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
        
def main():
    global app 
    app = QApplication( sys.argv )
    
    global ex
    ex = init_GUI()
    ex.show()
    sys.exit( app.exec_() )

if __name__ == '__main__':
    main()