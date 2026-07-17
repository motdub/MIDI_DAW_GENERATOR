"""
Seed Widget - Custom widget for seed control with Randomize button.
Provides reproducibility controls for MIDI generation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QSpinBox
)


class SeedWidget(QWidget):
    """Widget containing seed field and randomize button."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.seed_value = 0
        
        # Set minimum size for the widget itself
        self.setMinimumSize(350, 120)  # Minimum width and height
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Seed label
        self.seed_label = QLabel("Seed (for reproducibility):")
        self.seed_label.setMinimumSize(0, 25)  # Ensure minimum height
        self.seed_label.setStyleSheet("color: #aaaaaa; font-weight: normal;")
        layout.addWidget(self.seed_label)
        
        # Spin box for seed input
        self.seed_spinbox = QSpinBox()
        self.seed_spinbox.setRange(0, 2147483647)
        self.seed_spinbox.setValue(0)
        self.seed_spinbox.setMaximum(2147483647)
        self.seed_spinbox.setMinimumSize(250, 30)  # Ensure minimum width
        self.seed_spinbox.setStyleSheet("""
            QSpinBox {
                background-color: #353535;
                border: 1px solid #444444;
                color: #ffffff;
                padding: 6px;
            }
        """)
        layout.addWidget(self.seed_spinbox)
        
        # Randomize button
        self.randomize_btn = QPushButton("Randomize Seed")
        self.randomize_btn.setMinimumSize(150, 35)  # Ensure minimum size for button
        self.randomize_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                border: 1px solid #2b5fa3;
                color: #ffffff;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2b7fff;
            }
        """)
        self.randomize_btn.clicked.connect(self._randomize_seed)
        layout.addWidget(self.randomize_btn)
        
        layout.addStretch()
    
    def _randomize_seed(self):
        """Generate a random seed value."""
        import random
        
        # Generate random integer between 0 and 2^31-1
        self.seed_value = random.randint(0, 2147483647)
        self.seed_spinbox.setValue(self.seed_value)
    
    def get_seed(self) -> int:
        """Get the current seed value."""
        return self.seed_value
    
    def set_seed(self, seed: int):
        """Set the seed value and update UI."""
        self.seed_value = seed
        self.seed_spinbox.setValue(seed)
