"""
Modern KPI Stat Card widget for metrics display.
Shows Title, Main Value, and Subtitle/Badge.
"""
from typing import Optional
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PySide6.QtCore import Qt


class KpiCard(QFrame):
    def __init__(
        self,
        title: str,
        initial_value: str = "—",
        initial_badge: str = "",
        badge_type: str = "neutral",  # 'positive', 'negative', 'neutral'
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(95)
        self.badge_type = badge_type

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        # Top row: Title + Badge
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel(title)
        self.title_label.setObjectName("kpiTitle")
        top_layout.addWidget(self.title_label)

        top_layout.addStretch()

        self.badge_label = QLabel(initial_badge)
        self.set_badge(initial_badge, badge_type)
        top_layout.addWidget(self.badge_label)

        layout.addLayout(top_layout)

        # Main value
        self.value_label = QLabel(initial_value)
        self.value_label.setObjectName("kpiValue")
        self.value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.value_label)

    def set_value(self, value: str):
        self.value_label.setText(value)

    def set_badge(self, text: str, badge_type: Optional[str] = None):
        if not text:
            self.badge_label.setVisible(False)
            return

        self.badge_label.setVisible(True)
        self.badge_label.setText(text)
        
        b_type = badge_type or self.badge_type
        if b_type == "positive":
            self.badge_label.setObjectName("kpiBadgePositive")
        elif b_type == "negative":
            self.badge_label.setObjectName("kpiBadgeNegative")
        else:
            self.badge_label.setObjectName("kpiBadgeNeutral")
        
        self.badge_label.style().unpolish(self.badge_label)
        self.badge_label.style().polish(self.badge_label)
