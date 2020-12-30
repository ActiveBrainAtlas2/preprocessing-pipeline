import sys, os
import argparse
import subprocess

sys.path.append(os.path.join(os.getcwd(), 'utilities'))

from PyQt5.QtGui import QFont, QIntValidator
from PyQt5.QtCore import *
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QComboBox, QPushButton, QMessageBox

from metadata import ordered_pipeline_steps, ROOT_DIR
from data_manager_v2 import DataManager
from a_driver_utilities import set_step_completed_in_progress_ini

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Optional to include a stack, in which the metadata autofills')

parser.add_argument('--stack', default="", type=str)
args = parser.parse_args()
stack = args.stack


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


class init_GUI(QWidget):
    def __init__(self, parent=None):
        super(init_GUI, self).__init__(parent)
        self.font_header = QFont("Arial", 32)
        self.font_left_col = QFont("Arial", 16)

        self.default_textbox_val = ""

        self.stack = ""
        self.stain = ""
        self.planar_res = 0
        self.section_thickness = 0
        self.cutting_plane = ""
        self.input_filetype = "tiff"
        self.new_stacks = new_stacks
        self.stain_options = ['ntb', 'thionin', 'other fluorescent', 'other brightfield']
        self.cutting_plane_options = ['sagittal', 'horozontal', 'coronal']
        self.cutting_planar_resolution_options = [0.46, 0.325]
        self.section_thickness_options = [20]
        self.input_filetype_options = ['tiff', 'jp2', 'czi', 'ndpi', 'ngr']
        # create a dataManager object
        self.dataManager = DataManager()
        self.initUI()
        # self.updateFields()

    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_body = QGridLayout()

        # self.setFixedSize(900, 350)
        self.resize(900, 350)

        ### Grid TOP (1 row) ###
        # Static Text Field
        self.e1 = QLineEdit()
        self.e1.setValidator(QIntValidator())
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont(self.font_header)
        self.e1.setReadOnly(True)
        self.e1.setText("Enter Metadata")
        self.e1.setFrame(False)
        self.grid_top.addWidget(self.e1, 0, 0)

        ### Grid BODY (1 row) ###
        # Static Text Field
        self.e2 = QLineEdit()
        self.e2.setValidator(QIntValidator())
        self.e2.setMaxLength(50)
        self.e2.setAlignment(Qt.AlignRight)
        self.e2.setFont(self.font_left_col)
        self.e2.setReadOnly(True)
        self.e2.setText("Stack name:")
        self.e2.setFrame(False)
        self.grid_body.addWidget(self.e2, 0, 0)
        # Static Text Field
        self.e3 = QLineEdit()
        self.e3.setValidator(QIntValidator())
        self.e3.setMaxLength(50)
        self.e3.setAlignment(Qt.AlignRight)
        self.e3.setFont(self.font_left_col)
        self.e3.setReadOnly(True)
        self.e3.setText("Stain (ntb/thionin):")
        self.e3.setFrame(False)
        self.grid_body.addWidget(self.e3, 1, 0)
        # Static Text Field
        self.e4 = QLineEdit()
        self.e4.setValidator(QIntValidator())
        self.e4.setMaxLength(50)
        self.e4.setAlignment(Qt.AlignRight)
        self.e4.setFont(self.font_left_col)
        self.e4.setReadOnly(True)
        self.e4.setText("Cutting plane (sagittal/horozontal/coronal):")
        self.e4.setFrame(False)
        self.grid_body.addWidget(self.e4, 2, 0)
        # Static Text Field
        self.e5 = QLineEdit()
        self.e5.setValidator(QIntValidator())
        self.e5.setMaxLength(50)
        self.e5.setAlignment(Qt.AlignRight)
        self.e5.setFont(self.font_left_col)
        self.e5.setReadOnly(True)
        self.e5.setText("Slice thickness in um (usually 20):")
        self.e5.setFrame(False)
        self.grid_body.addWidget(self.e5, 3, 0)
        # Static Text Field
        self.e6 = QLineEdit()
        self.e6.setValidator(QIntValidator())
        self.e6.setMaxLength(50)
        self.e6.setAlignment(Qt.AlignRight)
        self.e6.setFont(self.font_left_col)
        self.e6.setReadOnly(True)
        self.e6.setText("Planar resolution in um (0.46/0.325):")
        self.e6.setFrame(False)
        self.grid_body.addWidget(self.e6, 4, 0)
        # Static Text Field
        self.e7 = QLineEdit()
        self.e7.setValidator(QIntValidator())
        self.e7.setMaxLength(50)
        self.e7.setAlignment(Qt.AlignRight)
        self.e7.setFont(self.font_left_col)
        self.e7.setReadOnly(True)
        self.e7.setText("Input filetype (images):")
        self.e7.setFrame(False)
        self.grid_body.addWidget(self.e7, 5, 0)

        # Dropbown Menu (ComboBox) for selecting Stack
        self.dd1 = QComboBox()
        self.dd1.addItems(self.new_stacks)
        self.dd1.currentIndexChanged.connect(lambda: self.dd_selection(self.dd1))
        self.dd1.setEnabled(True)
        self.grid_body.addWidget(self.dd1, 0, 1)
        # Stain Editable Text Field
        self.t2 = QLineEdit()
        self.t2.setMaxLength(50)
        self.t2.setAlignment(Qt.AlignLeft)
        self.t2.setFont(self.font_left_col)
        self.t2.setText(self.default_textbox_val)
        self.t2.setFrame(True)
        self.grid_body.addWidget(self.t2, 1, 1)

        # Cutting Plane Editable Text Field
        self.t3 = QLineEdit()
        self.t3.setMaxLength(50)
        self.t3.setAlignment(Qt.AlignLeft)
        self.t3.setFont(self.font_left_col)
        self.t3.setText(self.default_textbox_val)
        self.t3.setFrame(True)
        self.grid_body.addWidget(self.t3, 2, 1)
        # Slice Thickness Editable Text Field
        self.t4 = QLineEdit()
        self.t4.setMaxLength(50)
        self.t4.setAlignment(Qt.AlignLeft)
        self.t4.setFont(self.font_left_col)
        self.t4.setText(self.default_textbox_val)
        self.t4.setFrame(True)
        self.grid_body.addWidget(self.t4, 3, 1)
        # Planar Res Editable Text Field
        self.t5 = QLineEdit()
        self.t5.setMaxLength(50)
        self.t5.setAlignment(Qt.AlignLeft)
        self.t5.setFont(self.font_left_col)
        self.t5.setText(self.default_textbox_val)
        self.t5.setFrame(True)
        self.grid_body.addWidget(self.t5, 4, 1)
        # Dropbown Menu (ComboBox) for selecting file types
        self.dd2 = QComboBox()
        self.dd2.addItems(self.input_filetype_options)
        self.dd2.currentIndexChanged.connect(lambda: self.dd_selection(self.dd2))
        self.dd2.setEnabled(True)
        self.grid_body.addWidget(self.dd2, 5, 1)

        # Static Text Field
        self.e7 = QLineEdit()
        self.e7.setValidator(QIntValidator())
        self.e7.setMaxLength(50)
        self.e7.setAlignment(Qt.AlignRight)
        self.e7.setFont(self.font_left_col)
        self.e7.setReadOnly(True)
        self.e7.setText("Push `Submit` when finished")
        self.e7.setFrame(False)
        self.grid_body.addWidget(self.e7, 6, 0)
        # Button Text Field
        self.b1 = QPushButton("Submit")
        self.b1.setDefault(True)
        self.b1.clicked.connect(lambda: self.buttonPressSubmit(self.b1))
        self.grid_body.addWidget(self.b1, 6, 1)

        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout(self.grid_top, 0, 0)
        self.supergrid.addLayout(self.grid_body, 1, 0)

        # Set layout and window title
        self.setLayout(self.supergrid)
        self.setWindowTitle("Setup new brain metadata")

        # Center the GUI
        self.center()

        #########################################################
        # self.buttonPressSubmit(self.b1)
        #########################################################

    def validateEntries(self):
        entered_stack = str(self.dd1.currentText() )
        entered_stain = str(self.t2.text())
        entered_plane = str(self.t3.text())
        entered_thickness = str(self.t4.text())
        entered_resolution = str(self.t5.text())
        entered_input_filetype = str(self.dd2.currentText())

        for field in [entered_stack, entered_stain, entered_plane, entered_thickness,
                      entered_resolution, entered_input_filetype]:
            if field == "":
                self.e7.setText('Not all fields have been filled in!')

        if self.default_textbox_val != '' and self.default_textbox_val in \
                entered_stack + entered_stain + entered_plane + entered_thickness + entered_resolution:
            self.e7.setText('All fields must be filled out!')
            return False
        if ' ' in entered_stack + entered_stain + entered_plane + entered_thickness + entered_resolution:
            self.e7.setText('There should not be any spaces!')
            return False

        if not is_number(entered_thickness):
            self.e7.setText('Thickness is not a number!')
            return False
        if not is_number(entered_resolution):
            self.e7.setText('Resolution is not a number!')
            return False

        if entered_stain.lower() not in self.stain_options:
            self.e7.setText('Stain not valid!')
            return False
        if entered_plane.lower() not in self.cutting_plane_options:
            self.e7.setText('Cutting plane not valid!')
            return False
        if float(entered_thickness) not in self.section_thickness_options:
            self.e7.setText('Thickness not valid!')
            return False
        if float(entered_resolution) not in self.cutting_planar_resolution_options:
            self.e7.setText('Resolution not valid!')
            return False

        self.e7.setText('Logging brain metadata')
        return True

    def checkForSortedFilenames(self):
        stack = str(self.dd1.currentText())
        sorted_filename = os.path.join(ROOT_DIR, stack, 'brains_info', 'sorted_filenames.txt')
        return os.path.exists(sorted_filename)


    def dd_selection(self, dropdown):
        # stack filetype dropdown
        if dropdown == self.dd1:
            self.stack = dropdown.currentText()
        # filetype dropdown
        if dropdown == self.dd2:
            self.input_filetype = dropdown.currentText()

    def autofill(self, stack):
        stack_metadata = DataManager.get_brain_info_metadata(stack)

        #self.t1.setText(stack_metadata['stack_name'])
        self.t2.setText(stack_metadata['stain'])
        self.t3.setText(stack_metadata['cutting_plane'])
        self.t4.setText(str(stack_metadata['section_thickness_um']))
        self.t5.setText(str(stack_metadata['planar_resolution_um']))

    def buttonPressSubmit(self, button):
        if button == self.b1:
            validated = self.validateEntries()
            sorted_filename_exists = self.checkForSortedFilenames()
            #####################################################################################################################
            # validated = True
            #####################################################################################################################
            if validated and sorted_filename_exists:
                entered_stack = str(self.dd1.currentText())
                entered_stain = str(self.t2.text()).lower()
                entered_plane = str(self.t3.text()).lower()
                entered_thickness = float(str(self.t4.text()))
                entered_resolution = float(str(self.t5.text()))
                entered_input_filetype = str(self.dd2.currentText())
                #####################################################################################################################

                set_stack_metadata(entered_stack, entered_stain, entered_plane, entered_thickness, entered_resolution)
                set_step_completed_in_progress_ini(entered_stack, '1-1_setup_metadata')

                # hide_gui()

                # Need to use the Bioformats GUI if czi or ndpi
                bioformats_extraction = False
                if entered_input_filetype in ['czi', 'ndpi']:
                    bioformats_extraction = True

                if bioformats_extraction:
                    subprocess.call(['python', 'a_GUI_setup_images_bioformats.py',
                                     entered_stack])
                else:
                    self.dataManager.copy_over_tif_files(entered_stack)
                    # subprocess.call( ['python', 'a_GUI_setup_images_nonbioformats.py',  entered_stack, entered_input_filetype] )
                    set_step_completed_in_progress_ini(entered_stack, '1-2_setup_images')

                sys.exit(app.exec_())
            else:
                message = "The form is invalid and/or the file: {} is missing"\
                    .format(os.path.join(ROOT_DIR, str(self.dd1.currentText()), 'brains_info', 'sorted_filenames.txt'))
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText(message)
                msg.setWindowTitle("Error trying to process files.")
                msg.exec_()

    def center(self):
        """
        This function simply aligns the GUI to the center of your monitor.
        """
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber(QApplication.desktop().cursor().pos())
        centerPoint = QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def closeEvent(self, event):
        sys.exit(app.exec_())
        # close_main_gui( ex )


# Records a stack's metadata after it is validated
def set_stack_metadata(stack, stain, plane, thickness, resolution):
    if stain == 'ntb':
        stain_capitalized = 'NTB'
    if stain == 'thionin':
        stain_capitalized = 'Thionin'

    # Save METADATA ini
    input_dict = {}
    input_dict['DEFAULT'] = {'stack_name': stack,
                             'cutting_plane': plane,
                             'planar_resolution_um': resolution,
                             'section_thickness_um': thickness,
                             'stain': stain_capitalized}

    fp = DataManager.get_brain_info_metadata_fp(stack)
    try:
        os.makedirs(DataManager.get_brain_info_root_folder(stack))
    except:
        pass

    save_dict_as_ini(input_dict, fp)
    save_metadata_in_shell_script(stack, stain, plane, thickness, resolution)

    # Now save PROGRESS ini
    input_dict_p = {}
    input_dict_p['DEFAULT'] = {}
    # Populate with contents of 'ordered_pipeline_steps' from src/utilities/metadata.py
    for pipeline_step in ordered_pipeline_steps:
        if pipeline_step == 'setup_metadata':
            input_dict_p['DEFAULT'][pipeline_step] = True
        else:
            input_dict_p['DEFAULT'][pipeline_step] = False

    fp = DataManager.get_brain_info_progress_fp(stack)

    save_dict_as_ini(input_dict_p, fp)


# Save the STACK.ini file
def save_dict_as_ini(input_dict, fp):
    import configparser
    assert 'DEFAULT' in input_dict.keys()

    config = configparser.ConfigParser()

    for key in input_dict.keys():
        config[key] = input_dict[key]

    with open(fp, 'w') as configfile:
        config.write(configfile)


# Save the brain_metadata.sh file
def save_metadata_in_shell_script(stack, stain, plane, thickness, resolution):
    fp = os.path.join(ROOT_DIR, stack, 'brains_info', 'metadata.sh')

    # Change ntb->NTB and thionin->Thionin
    if stain == 'ntb':
        stain = 'NTB'
        detector_id = 799
        img_version_1 = 'NtbNormalized'
        img_version_2 = 'NtbNormalizedAdaptiveInvertedGamma'
    elif stain == 'thionin':
        stain = 'Thionin'
        detector_id = 19
        img_version_1 = 'gray'
        img_version_2 = 'gray'

    data = 'export stack=' + stack + '\n' + \
           'export stain=' + stain + '\n' + \
           'export detector_id=' + str(detector_id) + '\n' + \
           'export img_version_1=' + img_version_1 + '\n' + \
           'export img_version_2=' + img_version_2 + '\n'

    with open(fp, 'w') as file:
        file.write(data)


def hide_gui():
    ex.hide()


def main():
    global app
    app = QApplication(sys.argv)

    global ex
    ex = init_GUI()
    ex.show()

    # User has passed in a stack
    if stack != "":
        ex.autofill(stack)

    ###########################################################################################################################################
    # ex.buttonPressSubmit(ex.b1)
    ###########################################################################################################################################
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
