APP_STYLESHEET = """
QWidget {
    background-color: #0d1219;
    color: #f5f7fb;
    font-size: 10pt;
    font-family: "Pretendard", "Malgun Gothic", "Segoe UI Variable Text", "Segoe UI";
}

QLabel {
    background: transparent;
}

QWidget#ButtonStrip {
    background: transparent;
}

QWidget#RootWidget {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #0b1017,
        stop: 0.45 #101824,
        stop: 1 #0a0f16
    );
}

QFrame#HeroPanel,
QFrame#GroupPanel,
QFrame#StatusPanel,
QFrame#LogPanel,
QFrame#EmptyState,
QFrame#AddSlotCard,
QFrame#DropOverlayCard {
    background-color: rgba(15, 21, 31, 0.96);
    border: 1px solid #1e2937;
    border-radius: 24px;
}

QFrame#AddSlotCard {
    border: 1px dashed #2e4f70;
    background-color: rgba(13, 19, 28, 0.94);
}

QFrame#AddSlotCard:hover,
QFrame#AddSlotCard[dropActive="true"] {
    border: 1px solid #64dce4;
    background-color: rgba(17, 28, 40, 0.98);
}

QFrame#DropOverlay {
    background-color: rgba(7, 11, 18, 0.68);
    border-radius: 28px;
}

QFrame#DropOverlayCard {
    min-width: 460px;
    max-width: 680px;
    min-height: 164px;
    background-color: rgba(14, 22, 33, 0.98);
    border: 1px solid #6ce0e5;
}

QFrame#InsertIndicator {
    background-color: #6ce0e5;
    border-radius: 1px;
}

QLabel#DropOverlayEyebrow {
    color: #79e3e7;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#DropOverlayTitle {
    color: #fbfdff;
    font-size: 15pt;
    font-weight: 700;
    padding-top: 2px;
}

QLabel#DropOverlaySubtitle {
    color: #a0b1c3;
    font-size: 10pt;
}

QLabel#HeroEyebrow {
    color: #74e1e5;
    font-size: 9pt;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#HeroTitle {
    color: #fbfcff;
    font-size: 24pt;
    font-weight: 700;
    font-family: "Pretendard SemiBold", "Pretendard", "Malgun Gothic", "Segoe UI Variable Display", "Segoe UI";
}

QLabel#HeroSubtitle,
QLabel#SectionSubtitle,
QLabel#StatusDetail,
QLabel#EmptyStateSubtitle {
    color: #98a6b8;
    line-height: 1.4;
}

QLabel#SectionTitle {
    font-size: 12pt;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#DropZoneTitle {
    font-size: 11.5pt;
    font-weight: 700;
    color: #f7fbff;
}

QLabel#DropZoneSubtitle {
    color: #95a9bf;
    line-height: 1.4;
}

QLabel#AddSlotPlus {
    background-color: #142334;
    border: 1px solid #2b455f;
    border-radius: 14px;
    color: #7be2e7;
    font-size: 18pt;
    font-weight: 500;
}

QLabel#AddSlotTitle {
    color: #f8fafc;
    font-size: 12.5pt;
    font-weight: 700;
}

QLabel#AddSlotSubtitle {
    color: #95a9bf;
    line-height: 1.4;
}

QLineEdit,
QComboBox,
QPlainTextEdit {
    background-color: #111826;
    border: 1px solid #243245;
    border-radius: 16px;
    padding: 12px 14px;
    color: #f5f7fb;
    selection-background-color: #6ce0e5;
    selection-color: #091016;
}

QLineEdit:focus,
QComboBox:focus,
QPlainTextEdit:focus {
    border: 1px solid #6ce0e5;
    background-color: #151f2d;
}

QLineEdit#SearchInput {
    min-height: 22px;
    font-size: 10.5pt;
    padding-left: 16px;
}

QComboBox::drop-down {
    width: 28px;
    border: none;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
}

QPushButton,
QToolButton {
    background-color: #152132;
    border: 1px solid #243245;
    border-radius: 16px;
    color: #eef2f7;
    padding: 11px 16px;
    font-weight: 600;
}

QPushButton:hover,
QToolButton:hover {
    background-color: #1a2940;
    border-color: #335072;
}

QPushButton:pressed,
QToolButton:pressed {
    background-color: #0f1722;
}

QPushButton#PrimaryButton {
    background-color: #6ce0e5;
    border: none;
    color: #071016;
    padding: 12px 18px;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background-color: #87e6ea;
}

QPushButton#CompactPrimaryButton,
QPushButton#FlatActionButton,
QPushButton#CompactDangerButton {
    padding: 8px 12px;
    border-radius: 12px;
    min-height: 18px;
}

QPushButton#CompactPrimaryButton {
    background-color: #6ce0e5;
    border: none;
    color: #071016;
    font-weight: 700;
}

QPushButton#CompactPrimaryButton:hover {
    background-color: #87e6ea;
}

QPushButton#FlatActionButton {
    background-color: #152132;
    border: 1px solid #243245;
    color: #eef2f7;
}

QPushButton#FlatActionButton:hover {
    background-color: #1a2940;
    border-color: #335072;
}

QPushButton#GhostActionButton {
    background-color: rgba(18, 31, 46, 0.92);
    border: 1px solid #2b455f;
    color: #dff7fa;
    padding: 9px 14px;
    border-radius: 12px;
}

QPushButton#GhostActionButton:hover {
    background-color: rgba(23, 39, 58, 0.98);
    border-color: #64dce4;
}

QPushButton#DangerButton {
    background-color: #3a1720;
    border: 1px solid #5f2332;
    color: #f8d8df;
}

QPushButton#DangerButton:hover {
    background-color: #4a1c28;
}

QPushButton#CompactDangerButton {
    background-color: #3a1720;
    border: 1px solid #5f2332;
    color: #f8d8df;
}

QPushButton#CompactDangerButton:hover {
    background-color: #4a1c28;
}

QScrollArea {
    border: none;
    background: transparent;
}

QFrame#ItemFrame {
    background-color: rgba(16, 22, 31, 0.98);
    border: 1px solid #1f2d3e;
    border-radius: 24px;
}

QFrame#ItemFrame[hovered="true"] {
    background-color: rgba(18, 26, 37, 0.99);
    border: 1px solid #31465f;
}

QFrame#ItemFrame[selectedItem="true"] {
    background-color: rgba(18, 28, 41, 0.99);
    border: 1px solid #5acfd7;
}

QFrame#ItemFrame[pressed="true"] {
    background-color: rgba(12, 18, 27, 0.99);
    border: 1px solid #3b556f;
}

QFrame#ItemFrame[disabledItem="true"] {
    background-color: rgba(13, 18, 26, 0.92);
    border: 1px solid #1a2432;
}

QFrame#ItemFrame[dragActive="true"] {
    background-color: rgba(18, 27, 39, 0.92);
    border: 1px solid #5a7a98;
}

QWidget#ItemInfoHost,
QWidget#ItemTextBlock {
    background: transparent;
}

QFrame#IconChip {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #24384d,
        stop: 1 #182333
    );
    border: 1px solid #30445e;
    border-radius: 20px;
}

QLabel#IconText {
    color: #dffbfc;
    font-size: 12pt;
    font-weight: 700;
}

QLabel#ItemTitle {
    color: #f8fafc;
    font-size: 12.8pt;
    font-weight: 700;
    font-family: "Pretendard SemiBold", "Pretendard", "Malgun Gothic", "Segoe UI Variable Display", "Segoe UI";
}

QLabel#ItemSubtitle {
    color: #8fa2b7;
    font-size: 9.5pt;
}

QLabel#ItemAppIcon {
    background-color: rgba(19, 32, 47, 0.94);
    border: 1px solid #2b425b;
    border-radius: 16px;
    color: #cfeaf0;
    font-size: 8.5pt;
    font-weight: 700;
}

QLabel#DragHandle {
    color: #60758d;
    font-size: 12pt;
    font-weight: 700;
    padding: 0 2px;
}

QLabel#DragHandle:hover {
    color: #abc0d8;
}

QFrame#UrlChip {
    background-color: rgba(20, 31, 45, 0.94);
    border: 1px solid #2d435b;
    border-radius: 14px;
}

QLabel#UrlChipIcon {
    color: #82e2e7;
}

QLabel#UrlChipText {
    color: #dce7f3;
    font-size: 9.2pt;
}

QFrame#AppMetaRow {
    background: transparent;
}

QLabel#AppMetaIcon {
    background: transparent;
    color: #9eb4c8;
}

QLabel#AppMetaText {
    color: #8fa2b7;
    font-size: 9.3pt;
}

QLabel#ItemDescription,
QLabel#ItemDetail,
QLabel#ScriptDetail,
QLabel#TargetPreview,
QLabel#MetaLabel {
    color: #98a6b8;
}

QLabel#TypeBadge,
QLabel#EnabledBadge,
QLabel#MetricPill,
QLabel#OrderBadge {
    border-radius: 12px;
    padding: 6px 10px;
    font-size: 8.5pt;
    font-weight: 700;
}

QLabel#TypeBadge {
    background-color: #15283a;
    color: #76dfe4;
    border: 1px solid #264057;
}

QLabel#EnabledBadge {
    background-color: #13211d;
    color: #86ebb8;
    border: 1px solid #294438;
}

QLabel#EnabledBadge[disabledState="true"] {
    background-color: #2a1a1f;
    color: #efb8c4;
    border: 1px solid #5b2a35;
}

QLabel#MetricPill {
    background-color: #111c2a;
    color: #b6c7da;
    border: 1px solid #243245;
}

QLabel#OrderBadge {
    background-color: #162435;
    color: #dff8fa;
    border: 1px solid #2c4762;
    min-width: 32px;
}

QFrame#ItemActionGroup {
    background-color: rgba(11, 17, 25, 0.84);
    border: 1px solid #223547;
    border-radius: 18px;
}

QWidget#SecondaryActionRow {
    background: transparent;
}

QPushButton#ItemPrimaryAction,
QPushButton#ItemSelectAction,
QPushButton#ItemSecondaryAction,
QPushButton#ItemDangerAction {
    min-height: 36px;
    border-radius: 12px;
    padding: 8px 14px;
    font-weight: 700;
}

QPushButton#ItemPrimaryAction {
    background-color: #6ce0e5;
    border: none;
    color: #071016;
}

QPushButton#ItemPrimaryAction:hover {
    background-color: #85e6ea;
}

QPushButton#ItemPrimaryAction:pressed {
    background-color: #54cfd5;
}

QPushButton#ItemSelectAction {
    background-color: rgba(17, 28, 40, 0.82);
    border: 1px solid #2d445d;
    color: #d5e1ee;
}

QPushButton#ItemSelectAction:hover {
    background-color: rgba(22, 35, 50, 1);
    border-color: #3a5978;
}

QPushButton#ItemSelectAction:checked {
    background-color: rgba(18, 61, 66, 0.96);
    border: 1px solid #6ce0e5;
    color: #e8fdff;
}

QPushButton#ItemSelectAction:pressed {
    background-color: rgba(14, 45, 49, 1);
}

QPushButton#ItemSecondaryAction {
    background-color: rgba(18, 28, 40, 0.72);
    border: 1px solid rgba(45, 62, 83, 0.72);
    color: #bcc9d8;
}

QPushButton#ItemSecondaryAction:hover {
    background-color: rgba(24, 38, 55, 1);
    border-color: #3a556f;
    color: #eef4fb;
}

QPushButton#ItemSecondaryAction:pressed {
    background-color: rgba(16, 27, 39, 1);
}

QPushButton#ItemDangerAction {
    background-color: rgba(47, 22, 30, 0.42);
    border: 1px solid rgba(108, 52, 66, 0.56);
    color: #dec2cb;
}

QPushButton#ItemDangerAction:hover {
    background-color: rgba(56, 26, 34, 0.54);
    border-color: rgba(128, 60, 76, 0.7);
}

QPushButton#ItemDangerAction:pressed {
    background-color: rgba(43, 20, 27, 0.62);
}

QToolButton#CardMenuButton {
    min-width: 34px;
    max-width: 34px;
    min-height: 34px;
    max-height: 34px;
    padding: 0;
    border-radius: 12px;
}

QToolButton#CardMenuButton::menu-indicator {
    image: none;
    width: 0;
    height: 0;
}

QPlainTextEdit#LogEditor {
    background-color: #0b1119;
    border: 1px solid #1d2736;
    border-radius: 18px;
    padding: 12px;
    color: #d8e1ec;
    font-family: "Cascadia Code";
    font-size: 9.5pt;
}

QMenu {
    background-color: #101722;
    border: 1px solid #243245;
    border-radius: 14px;
    padding: 8px;
}

QMenu::item {
    padding: 8px 18px;
    border-radius: 8px;
}

QMenu::item:selected {
    background-color: #1a2738;
}

QCheckBox {
    color: #e4ebf5;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid #304255;
    background-color: #101722;
}

QCheckBox::indicator:checked {
    background-color: #6ce0e5;
    border: 1px solid #6ce0e5;
}

QMessageBox {
    background-color: #0e141d;
}

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 4px;
}

QScrollBar::handle:vertical {
    background: #253548;
    min-height: 36px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background: #31465f;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
"""
