import sys
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QRubberBand, QWidget, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from rdkit import Chem
from rdkit.Chem import Draw
import io
from PIL import Image
from rdkit.Chem.Draw import rdMolDraw2D
from PyQt5.QtGui import QFont

class MoleculeViewer(QMainWindow):
    def __init__(self, smiles, parent=None):
        super(MoleculeViewer, self).__init__(parent)
        self.smiles = smiles
        self.initUI()
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

    def initUI(self):
        self.setWindowTitle('Molecule Viewer')
        self.setGeometry(100, 100, 1000, 900)  # Adjust the size to match the molecule pixmap size

        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)  # Align the label to the center

        self.atomNameLabel = QLabel("Selected Atom: None", self)
        self.atomNameLabel.setAlignment(Qt.AlignCenter)

        pixmap = self.get_molecule_pixmap(self.smiles)
        self.label.setPixmap(pixmap)

        # Set the label size to match the pixmap size
        self.label.resize(pixmap.width(), pixmap.height())

        # Center the label within the main window
        layout = QVBoxLayout()
        layout.addWidget(self.label, 0, Qt.AlignCenter)  # Add the molecule label to the layout, aligned center
        layout.addWidget(self.atomNameLabel, 0, Qt.AlignCenter)  # Add the atom name label below the molecule label

        # Central widget to hold the layout
        centralWidget = QWidget(self)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

    def get_molecule_pixmap(self, smiles):
        mol = Chem.MolFromSmiles(smiles)
        img = Draw.MolToImage(mol, size=(600, 600))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)
        return pixmap

    def mousePressEvent(self, event):
        self.origin = QPoint(event.pos())
        self.rubberBand.setGeometry(QRect(self.origin, QSize()))
        self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        pixmap_size = self.label.pixmap().size()
        self.rubberBand.hide()

        # Get the final release position
        release_pos = self.label.mapFromParent(event.pos())

        # Determine the top-left and bottom-right corners of the selection rectangle
        top_left_ui = QPoint(min(self.origin.x(), release_pos.x()), min(self.origin.y(), release_pos.y()))
        bottom_right_ui = QPoint(max(self.origin.x(), release_pos.x()), max(self.origin.y(), release_pos.y()))

        # Adjust the coordinates of both corners to molecule coordinates
        top_left_mol = self.adjust_coordinates(top_left_ui)
        bottom_right_mol = self.adjust_coordinates(bottom_right_ui)

        # Recompute atom positions based on the displayed image size
        mol = Chem.MolFromSmiles(self.smiles)
        Chem.rdDepictor.Compute2DCoords(mol)
        drawer = rdMolDraw2D.MolDraw2DCairo(self.label.pixmap().size().width(), self.label.pixmap().size().height())
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        atom_positions = [(drawer.GetDrawCoords(i).x, drawer.GetDrawCoords(i).y) for i in range(mol.GetNumAtoms())]

        # Find atoms within the selected region
        selected_atoms = [i for i, pos in enumerate(atom_positions) if top_left_mol[0] <= pos[0] <= bottom_right_mol[0] and top_left_mol[1] <= pos[1] <= bottom_right_mol[1]]

        # Highlight the selected atoms and update the UI
        if selected_atoms:
            self.highlight_atoms(selected_atoms, mol)
             # Create a new molecule object from the selected atoms
            submol = Chem.PathToSubmol(mol, selected_atoms)
            # Generate SMILES for the substructure
            submol_smiles = Chem.MolToSmiles(submol)
            print(f"Selected substructure SMILES: {submol_smiles}")
            self.atomNameLabel.setText(f"Selected substructure SMILES: {submol_smiles}")
            # Create a QFont object with the desired font size
            font = QFont()
            font.setPointSize(20)  # Set the font size to 12 points, adjust as needed
            # Set the font of the atomNameLabel to the QFont object
            self.atomNameLabel.setFont(font)

    def adjust_coordinates(self, point):
        # Adjusts UI coordinates to molecule coordinates
        pixmap_size = self.label.pixmap().size()
        scale_x = pixmap_size.width() / 600
        scale_y = pixmap_size.height() / 600
        offset_x = (self.label.width() - pixmap_size.width()) / 2
        offset_y = (self.label.height() - pixmap_size.height()) / 2

        adjusted_x = (point.x() - offset_x) / scale_x
        adjusted_y = (point.y() - offset_y) / scale_y

        return adjusted_x, adjusted_y

    def highlight_atoms(self, selected_atoms, mol):
        # Highlights selected atoms and updates the image
        drawer = rdMolDraw2D.MolDraw2DCairo(600, 600)
        drawer.DrawMolecule(mol, highlightAtoms=selected_atoms, highlightAtomColors={atom: (1.0, 0.0, 0.0) for atom in selected_atoms})
        drawer.FinishDrawing()

        data = bytes(drawer.GetDrawingText())
        qimage = QImage.fromData(data, 'PNG')
        pixmap = QPixmap.fromImage(qimage)
        self.label.setPixmap(pixmap)



def main():
    app = QApplication(sys.argv)
    #smiles = 'C1CCC(C2CCCCC2)CC1'  # Example SMILES string
    #smiles = 'c1cc(C(O)=O)ccc1'
    smiles = 'CC(=O)NCCC1=CNc2c1cc(OC)cc2'
    viewer = MoleculeViewer(smiles)
    viewer.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()