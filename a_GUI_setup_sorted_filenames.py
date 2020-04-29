import os
import sys
import argparse
from skimage import io
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QPushButton,  QComboBox, QMessageBox, QProgressBar

from image_viewer import ImageViewer
from utilities.sqlcontroller import SqlController
from utilities.file_location import FileLocationManager

class GUISortedFilenames(QWidget):

    def __init__(self, stack, parent=None):
        super(GUISortedFilenames, self).__init__(parent)

        self.stack = stack
        self.fileLocationManager = FileLocationManager(self.stack)
        self.sqlController = SqlController()
        self.sqlController.get_animal_info(self.stack)

        self.valid_sections = self.sqlController.get_valid_sections(stack)
        self.valid_section_keys = sorted(list(self.valid_sections))

        self.curr_section_index = 0
        self.curr_section = None

        self.init_ui()

        self.b_quality.currentIndexChanged.connect(lambda: self.click_button(self.b_quality))
        self.b_move_left.clicked.connect(lambda: self.click_button(self.b_move_left))
        self.b_move_right.clicked.connect(lambda: self.click_button(self.b_move_right))
        self.b_rotate_left.clicked.connect(lambda: self.click_button(self.b_rotate_left))
        self.b_rotate_right.clicked.connect(lambda: self.click_button(self.b_rotate_right))
        self.b_flip_vertical.clicked.connect(lambda: self.click_button(self.b_flip_vertical))
        self.b_flip_horozontal.clicked.connect(lambda: self.click_button(self.b_flip_horozontal))
        self.b_remove.clicked.connect(lambda: self.click_button(self.b_remove))
        self.b_help.clicked.connect(lambda: self.click_button(self.b_help))
        self.b_done.clicked.connect(lambda: self.click_button(self.b_done))

        self.set_curr_section(self.curr_section_index)

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
        self.b_quality = QComboBox()
        self.b_quality.addItems(['Section quality: unusable', 'Section quality: blurry', 'Section quality: good'])
        self.grid_body_lower.addWidget(self.b_quality, 0, 0, 1, 2)

        self.b_move_left = QPushButton("<--   Move Section Left   <--")
        self.grid_body_lower.addWidget(self.b_move_left, 0, 2)

        self.b_move_right = QPushButton("-->   Move Section Right   -->")
        self.grid_body_lower.addWidget(self.b_move_right, 0, 3)

        self.b_flip_vertical = QPushButton("Flip vertically")
        self.grid_body_lower.addWidget(self.b_flip_vertical, 1, 0)

        self.b_flip_horozontal = QPushButton("Flop horizontally")
        self.grid_body_lower.addWidget(self.b_flip_horozontal, 1, 1)

        self.b_rotate_left = QPushButton("Rotate Left")
        self.grid_body_lower.addWidget(self.b_rotate_left, 1, 2)

        self.b_rotate_right = QPushButton("Rotate Right")
        self.grid_body_lower.addWidget(self.b_rotate_right, 1, 3)

        self.b_remove = QPushButton("Remove section")
        self.grid_body_lower.addWidget(self.b_remove, 2, 0)

        self.progress = QProgressBar(self)
        self.grid_body_lower.addWidget(self.progress, 2, 1, 1, 2)
        self.progress.hide()

        self.b_done = QPushButton("Finished")
        self.grid_body_lower.addWidget(self.b_done, 2, 3)

        # Super grid
        self.supergrid = QGridLayout()
        self.supergrid.addLayout(self.grid_top, 0, 0)
        self.supergrid.addLayout(self.grid_body_upper, 1, 0)
        self.supergrid.addLayout(self.grid_body, 2, 0)
        self.supergrid.addLayout(self.grid_body_lower, 3, 0)

        # Set layout and window title
        self.setLayout(self.supergrid)
        self.setWindowTitle("Q")

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
        self.curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]

        # Update the section and filename at the top
        self.e_filename.setText(self.curr_section['destination'])
        self.e_section.setText(str(self.curr_section['section_number']))

        # Get filepath of "curr_section" and set it as viewer's photo
        img_fp = os.path.join(self.fileLocationManager.thumbnail_prep, self.curr_section['destination'])
        self.viewer.set_photo(img_fp)

        # Update the quality selection in the bottom left
        index = self.b_quality.findText(self.curr_section['quality'], Qt.MatchFixedString)
        if index >= 0:
            self.b_quality.setCurrentIndex(index)

    def get_valid_section_index(self, section_index):
        if section_index >= len(self.valid_sections):
            return 0
        elif section_index < 0:
            return len(self.valid_sections) - 1
        else:
            return section_index

    def click_button(self, button):
        if button == self.b_quality:
            curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]
            curr_section['quality'] = self.b_quality.currentText()
            self.sqlController.save_valid_sections(self.valid_sections)

        elif button in [self.b_move_left, self.b_move_right, self.b_remove]:
            if button == self.b_move_left:
                self.sqlController.move_section(self.stack, self.curr_section['section_number'], -1)
            elif button == self.b_move_right:
                self.sqlController.move_section(self.stack, self.curr_section['section_number'], 1)
            elif button == self.b_remove:
                result = self.message_box(
                    'Are you sure you want to totally remove this section from this brain?\n\n' +
                    'Warning: The image will be marked as irrelevant to the current brain!',
                    True
                )

                # The answer is Yes
                if result == 2:
                    # Remove the current section from "self.valid_sections
                    self.sqlController.inactivate_section(self.stack, self.curr_section['section_number'])

                    self.valid_sections = self.sqlController.get_valid_sections(self.stack)
                    self.valid_section_keys = sorted(list(self.valid_sections))

                    if self.curr_section_index == 0:
                        self.curr_section_index = len(self.valid_section_keys) - 1
                    else:
                        self.curr_section_index = self.curr_section_index - 1
            else:
                pass

            # Update the Viewer info and displayed image
            self.valid_sections = self.sqlController.get_valid_sections(self.stack)
            self.valid_section_keys = sorted(list(self.valid_sections))
            self.set_curr_section(self.curr_section_index)

        elif button in [self.b_flip_vertical, self.b_flip_horozontal, self.b_rotate_right, self.b_rotate_left]:
            """
            Transform_type must be "rotate", "flip", or "flop".
            These transformations get applied to all the active sections. The actual
            conversions take place on the thumbnails and the raw files.
            The transformed raw files get placed in the preps/oriented dir.
            """

            index = [self.b_flip_vertical, self.b_flip_horozontal, self.b_rotate_right, self.b_rotate_left].index(button)
            op = ['flip', 'flop', 'right', 'left'][index]

            size = len(self.valid_sections.values()) - 1
            self.progress_bar(True, size)

            for index, section in enumerate(self.valid_sections.values()):
                thumbnail_path = os.path.join(self.fileLocationManager.thumbnail_prep, section['destination'])
                if os.path.isfile(thumbnail_path):
                    self.transform_image(thumbnail_path, op)

                self.progress.setValue(index)

            self.progress_bar(False, size)
            self.set_curr_section(section_index=-1)

        elif button == self.b_help:
            self.message_box(
                'This GUI is used to align slices to each other. The shortcut commands are as follows: \n\n' +
                '-  `[`: Go back one section. \n' +
                '-  `]`: Go forward one section. \n\n' +
                'Use the buttons on the bottom panel to move',
                False
            )

        elif button == self.b_done:
            self.message_box(
                "All selected operations will now be performed on the full sized raw images" +
                "This may take an hour or two, depending on how many operations are queued.",
                False
            )

            # self.apply_queued_transformations()
            self.sqlController.set_step_completed_in_progress_ini(self.stack, '1-4_setup_sorted_filenames')
            self.sqlController.set_step_completed_in_progress_ini(self.stack, '1-5_setup_orientations')
            sys.exit(app.exec_())

    def transform_image(self, filename, op):
        def get_last_2d(data):
            if data.ndim <= 2:
                return data
            m,n = data.shape[-2:]
            return data.flat[:m*n].reshape(m,n)

        img = io.imread(filename)
        img = get_last_2d(img)

        # Rotating a multidimensional image has to be done backwards.
        # To rotate right, do np.rot(img, 3), to rotate left, do np.rot(img, 1)
        if op == 'left':
            img = np.rot90(img, 3)
        elif op == 'right':
            img = np.rot90(img, 1)
        elif op == 'flip':
            img = np.flipud(img)
        elif op == 'flop':
            img = np.fliplr(img)

        os.unlink(filename)
        io.imsave(filename, img)
        self.save_to_web_thumbnail(filename, img)

    def save_to_web_thumbnail(self, filename, img):
        filename = os.path.basename(filename)
        png_file = os.path.splitext(filename)[0] + '.png'
        png_path = os.path.join(self.fileLocationManager.thumbnail_web, png_file)
        if os.path.exists(png_path):
            os.unlink(png_path)
        io.imsave(png_path, img)

    def progress_bar(self, show, max_value):
        if show:
            self.progress.setMaximum(max_value)
            self.progress.show()
        else:
            self.progress.hide()

        self.b_quality.setDisabled(show)
        self.b_move_left.setDisabled(show)
        self.b_move_right.setDisabled(show)
        self.b_flip_vertical.setDisabled(show)
        self.b_flip_horozontal.setDisabled(show)
        self.b_rotate_right.setDisabled(show)
        self.b_rotate_left.setDisabled(show)
        self.b_remove.setDisabled(show)
        self.b_done.setDisabled(show)

    def message_box(self, text, is_warn):
        msg_box = QMessageBox()
        msg_box.setText(text)

        if is_warn:
            msg_box.addButton(QPushButton('Cancel'), QMessageBox.RejectRole)
            msg_box.addButton(QPushButton('No'), QMessageBox.NoRole)
            msg_box.addButton(QPushButton('Yes'), QMessageBox.YesRole)

        return msg_box.exec_()

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
        else:
            print(key)

    def closeEvent(self, event):
        sys.exit(app.exec_())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='GUI for sorting filenames')
    parser.add_argument("stack", type=str, help="stack name")
    args = parser.parse_args()
    stack = args.stack

    app = QApplication(sys.argv)
    ex = GUISortedFilenames(stack)
    ex.keyPressEvent(91)
    ex.show()
    sys.exit(app.exec_())
