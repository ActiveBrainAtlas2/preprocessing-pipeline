import os, sys
import subprocess
import argparse
from tqdm import tqdm

sys.path.append("utilities")
from PyQt5.QtCore import *
from PyQt5.QtGui import QFont, QIntValidator, QColor, QBrush, QPixmap
from PyQt5.QtWidgets import QWidget, QApplication, QGridLayout, QLineEdit, QPushButton, QMessageBox, QGraphicsView, \
    QGraphicsScene, QGraphicsPixmapItem, QFrame, QCheckBox, QComboBox

from utilities.file_location import FileLocationManager
from utilities.sqlcontroller import SqlController

class ImageViewer(QGraphicsView):
    photoClicked = pyqtSignal(QPoint)

    def __init__(self, parent):
        super(ImageViewer, self).__init__(parent)
        self._zoom = 0
        self._empty = True
        self._scene = QGraphicsScene(self)
        self._photo = QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
        self.setFrameShape(QFrame.NoFrame)

    def hasPhoto(self):
        return not self._empty

    def fitInView(self, scale=True):
        rect = QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QRectF(0, 0, 1, 1))
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
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
        else:
            self._empty = True
            self.setDragMode(QGraphicsView.NoDrag)
            self._photo.setPixmap(QPixmap())
        self.fitInView()


    '''
    def paintOverlayImage(self, pixmap=None):
        painter = QPainter()
        painter.begin(image)
        painter.drawImage(0, 0, overlay)
        painter.end()
    '''

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
            self.setDragMode(QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        if self._photo.isUnderMouse():
            self.photoClicked.emit(QPoint(event.pos()))
        super(ImageViewer, self).mousePressEvent(event)


class QHLine(QFrame):
    def __init__(self):
        # https://doc.qt.io/qt-5/qframe.html
        # https://stackoverflow.com/questions/5671354/how-to-programmatically-make-a-horizontal-line-in-qt
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(5)


class QVLine(QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QFrame.VLine)
        self.setFrameShadow(QFrame.Plain)
        self.setLineWidth(5)


class init_GUI(QWidget):

    def __init__(self, stack, parent=None):
        super(init_GUI, self).__init__(parent)
        self.font_h1 = QFont("Arial", 32)
        self.font_p1 = QFont("Arial", 16)
        self.queued_transformations = []

        # create a dataManager object
        self.sqlController = SqlController()
        self.stack = stack
        self.fileLocationManager = FileLocationManager(self.stack)
        self.sqlController.get_animal_info(self.stack)

        self.valid_sections = self.sqlController.get_valid_sections(stack)
        self.valid_section_keys = sorted(list(self.valid_sections))

        section_length =  len(self.valid_section_keys)

        self.curr_section_index = section_length // 2
        self.prev_section_index = self.curr_section_index
        self.next_section_index = self.curr_section_index
        self.curr_section = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)

        self.initUI()

    def initUI(self):
        # Set Layout and Geometry of Window
        self.grid_top = QGridLayout()
        self.grid_body_upper = QGridLayout()
        self.grid_body = QGridLayout()
        self.grid_body_lower = QGridLayout()
        self.grid_bottom = QGridLayout()
        self.grid_blank = QGridLayout()

        # self.setFixedSize(1600, 1000)
        self.resize(1600, 1000)

        ### VIEWER ### (Grid Body)
        self.viewer = ImageViewer(self)
        self.viewer.photoClicked.connect(self.photoClicked)

        ### Grid TOP ###
        # Static Text Field (Title)
        self.e1 = QLineEdit()
        self.e1.setValidator(QIntValidator())
        self.e1.setAlignment(Qt.AlignCenter)
        self.e1.setFont(self.font_h1)
        self.e1.setReadOnly(True)
        self.e1.setText("Orient Images")
        self.e1.setFrame(False)
        self.grid_top.addWidget(self.e1, 0, 0)
        # Button Text Field
        self.b_help = QPushButton("HELP")
        self.b_help.setDefault(True)
        self.b_help.setEnabled(True)
        self.b_help.clicked.connect(lambda: self.help_button_press(self.b_help))
        self.b_help.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,250);")
        self.grid_top.addWidget(self.b_help, 0, 1)

        ### Grid BODY UPPER ###
        # Static Text Field
        self.e4 = QLineEdit()
        self.e4.setAlignment(Qt.AlignCenter)
        self.e4.setFont(self.font_p1)
        self.e4.setReadOnly(True)
        self.e4.setText("Filename: ")
        # self.e4.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget(self.e4, 0, 2)
        # Static Text Field
        self.e5 = QLineEdit()
        self.e5.setAlignment(Qt.AlignCenter)
        self.e5.setFont(self.font_p1)
        self.e5.setReadOnly(True)
        self.e5.setText("Section: ")
        # self.e5.setStyleSheet("color: rgb(250,50,50); background-color: rgb(250,250,250);")
        self.grid_body_upper.addWidget(self.e5, 0, 3)

        ### Grid BODY ###
        # Custom VIEWER
        self.grid_body.addWidget(self.viewer, 0, 0)

        ### Grid BODY LOWER ###
        # Button Text Field
        self.b1 = QPushButton("Flip image(s) across central vertical line")
        self.b1.setDefault(True)
        self.b1.setEnabled(True)
        self.b1.clicked.connect(lambda: self.buttonPress(self.b1))
        self.b1.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,200);")
        self.grid_body_lower.addWidget(self.b1, 0, 0)
        # Button Text Field
        self.b2 = QPushButton("Flop image(s) across central horozontal line")
        self.b2.setDefault(True)
        self.b2.setEnabled(True)
        self.b2.clicked.connect(lambda: self.buttonPress(self.b2))
        self.b2.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,250,200);")
        self.grid_body_lower.addWidget(self.b2, 1, 0)
        # Button Text Field
        self.b3 = QPushButton("Rotate Image(s)")
        self.b3.setDefault(True)
        self.b3.setEnabled(True)
        self.b3.clicked.connect(lambda: self.buttonPress(self.b3))
        self.b3.setStyleSheet("color: rgb(0,0,0); background-color: rgb(250,200,250);")
        self.grid_body_lower.addWidget(self.b3, 0, 1, 1, 2)
        # Checkbox
        self.cb_1 = QCheckBox("Apply transformation to ALL images")
        self.cb_1.setChecked(True)
        self.cb_1.setEnabled(False)
        self.grid_body_lower.addWidget(self.cb_1, 0, 3)
        # Static Text Field
        self.e6 = QLineEdit()
        self.e6.setMaximumWidth(250)
        self.e6.setAlignment(Qt.AlignRight)
        self.e6.setReadOnly(True)
        self.e6.setText("Degrees to rotate (clockwise!): ")
        self.grid_body_lower.addWidget(self.e6, 1, 1)
        # Dropbown Menu (ComboBox) for selecting Stack
        self.cb = QComboBox()
        self.cb.addItems(['90', '180', '270'])
        # self.cb.addItems( ['Rotate by 90 degrees', 'Rotate by 180 degrees', 'Rotate by 270 degrees'] )
        # self.cb.addItems( ['45', '90', '135', '180', '225', '270', '315'] )
        self.grid_body_lower.addWidget(self.cb, 1, 2)
        # Button Text Field
        self.b_done = QPushButton("Done orienting")
        self.b_done.setDefault(True)
        self.b_done.setEnabled(True)
        self.b_done.clicked.connect(lambda: self.buttonPress(self.b_done))
        self.b_done.setStyleSheet("color: rgb(0,0,0); background-color: #dfbb19;")
        self.grid_body_lower.addWidget(self.b_done, 1, 3)

        # Grid stretching
        # self.grid_body_upper.setColumnStretch(0, 2)
        self.grid_body_upper.setColumnStretch(2, 2)
        # self.grid_body_lower.setColumnStretch(3, 1)

        ### SUPERGRID ###
        self.supergrid = QGridLayout()
        self.supergrid.addLayout(self.grid_top, 0, 0)
        self.supergrid.addLayout(self.grid_body_upper, 1, 0)
        self.supergrid.addLayout(self.grid_body, 2, 0)
        # self.supergrid.addLayout( self.grid_body_lower, 4, 0)
        self.supergrid.addWidget(QHLine(), 6, 0, 1, 2)
        # self.supergrid.addLayout( self.grid_bottom, 6, 0)
        self.supergrid.addLayout(self.grid_body_lower, 7, 0)
        self.supergrid.addWidget(QHLine(), 8, 0, 1, 2)

        # Set layout and window title
        self.setLayout(self.supergrid)
        self.setWindowTitle("Q")

        # Loads self.curr_section as the current image and sets all fields appropriatly
        self.setCurrSection(self.curr_section_index)

    def help_button_press(self, button):
        info_text = "This GUI is used to align slices to each other. The shortcut commands are as follows: \n\n\
    -  `[`: Go back one section. \n\
    -  `]`: Go forward one section."

        QMessageBox.information(self, "Empty Field",
                                info_text)

    def loadImage(self):
        curr_fn = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['destination']
        # Get filepath of "curr_section" and set it as viewer's photo
        img_fp = os.path.join(self.fileLocationManager.prep_thumbnail, curr_fn)
        self.viewer.setPhoto(QPixmap(img_fp))


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

        if key == 91:  # [
            self.getPrevValidSection(self.curr_section_index)
            self.setCurrSection(self.prev_section_index)
        elif key == 93:  # ]
            self.getNextValidSection(self.curr_section_index)
            self.setCurrSection(self.next_section_index)
        else:
            print(key)


    def setCurrSection(self, section_index=-1):
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
        self.prev_section = self.getPrevValidSection(self.curr_section_index)
        self.next_section = self.getNextValidSection(self.curr_section_index)
        # Update the section and filename at the top
        self.updateCurrHeaderFields()
        # Update the quality selection in the bottom left
        self.loadImage()

    def getNextValidSection(self, section_index):
        self.next_section_index = section_index + 1
        if self.next_section_index > len(self.valid_sections) - 1:
            self.next_section_index = 0
        self.next_section = self.valid_sections[self.valid_section_keys[self.next_section_index]]['destination']
        return self.next_section

    def getPrevValidSection(self, section_index):
        self.prev_section_index = int(section_index) - 1
        if self.prev_section_index < 0:
            self.prev_section_index = len(self.valid_sections) - 1
        self.prev_section = self.valid_sections[self.valid_section_keys[self.prev_section_index]]['destination']
        return self.prev_section

    def buttonPress(self, button):
        # Brighten an image
        if button in [self.b1, self.b2, self.b3]:
            # "Flip image(s) across central vertical line"
            if button == self.b1:
                self.transform_thumbnails('flip')
            # "Flop image(s) across central horozontal line"
            elif button == self.b2:
                self.transform_thumbnails('flop')
            # "Rotate Image(s)"
            elif button == self.b3:
                self.transform_thumbnails('rotate', degrees=str(self.cb.currentText()))
            # Update the Viewer info and displayed image
            self.setCurrSection(self.curr_section_index)
        elif button == self.b_done:
            QMessageBox.about(self, "Popup Message", "All selected operations will now be performed on the\
                full sized raw images. This may take an hour or two, depending on how many operations are queued.")
            self.apply_queued_transformations()
            self.finished()

    def updateCurrHeaderFields(self):
        label = self.valid_sections[self.valid_section_keys[self.curr_section_index]]['source']
        self.e4.setText(label)
        self.e5.setText(str(self.curr_section))


    def transform_thumbnails(self, transform_type, degrees=0):
        """
        Transform_type must be "rotate", "flip", or "flop".
        These transformations get applied to all the active sections. The actual
        conversions take place on the thumbnails and the raw files.
        The transformed raw files get placed in the preps/oriented dir.
        """
        if transform_type == 'rotate':
            base_cmd = ['convert', '-' + transform_type, str(degrees)]
        else:
            base_cmd = ['convert', '-' + transform_type]

        self.queued_transformations.append(base_cmd)
        # Apply transforms to just the thumbnails
        THUMBNAIL = os.path.join(self.fileLocationManager.prep_thumbnail, 'thumbnail')
        for k,v in self.valid_sections.items():
            thumbnail = os.path.join(THUMBNAIL, v['destination'])
            subprocess.call(base_cmd + [thumbnail, thumbnail])

    def finished(self):
        self.sqlController.set_step_completed_in_progress_ini(self.stack, '1-5_setup_orientations')
        # close_main_gui( ex )
        sys.exit(app.exec_())


    def apply_queued_transformations(self):
        print('queued_transformations',  self.queued_transformations)
        if self.queued_transformations == []:
            print('No transformations to do. Exit stage left ...')
        else:
            # Apply to "raw" images
            RAW = self.fileLocationManager.tif
            ORIENTED = self.fileLocationManager.oriented
            for base_cmd in tqdm(self.queued_transformations):
                for k, v in self.valid_sections.items():
                    raw = os.path.join(RAW, v['source'])
                    oriented = os.path.join(ORIENTED, v['destination'])
                    subprocess.call(base_cmd + [raw, oriented])
                    #print(base_cmd + [raw, oriented])
        # Clear the queued transformations
        self.queued_transformations = []



def close_gui():
    # ex.hide()
    sys.exit(app.exec_())

def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='GUI for sorting filenames')
    parser.add_argument("stack", type=str, help="stack name")
    args = parser.parse_args()
    stack = args.stack
    sqlController = SqlController()
    sections = list(sqlController.get_valid_sections(stack))
    # Queued transformations keeps track of each transformation the user wants to perform
    #   on ALL the images. The transformations are applied to the large "raw" files after
    #   the user clicks "done orienting"

    if len(sections) > 0:
        global app
        app = QApplication(sys.argv)
        global ex
        ex = init_GUI(stack)
        # Run GUI as usual
        ex.show()
        # Simulate a user's keypress because otherwise the autozoom is weird
        ex.keyPressEvent(91)
        sys.exit(app.exec_())
    else:
        print('There are no sections to work with.')




if __name__ == '__main__':
    main()
