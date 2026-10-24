"""Native menus and settings around the toolkit-independent world scene."""

from collections.abc import Callable
from functools import partial
import sys

from PySide6.QtCore import QEventLoop, QSignalBlocker, Qt
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDockWidget,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from pyvistaqt import QtInteractor

from src.worldgen.config import WorldgenConfig
from src.worldgen.model import GeneratedWorld
from src.worldgen.render.rebuild import WorldRebuilder
from src.worldgen.render.viewer import WorldgenViewer


# Presentation groups only; the layer definitions and styles remain in layers.py.
LAYER_MENUS = (
    (
        "Geography",
        ("elevation", "coastal-elevation", "terrain-variation", "impact-relief"),
    ),
    (
        "Tectonic relief",
        (
            "tectonic-relief",
            "convergent-relief",
            "divergent-relief",
            "transform-relief",
            "shear-relief",
        ),
    ),
    ("Motion", ("convergence", "divergence", "shear")),
    (
        "Partitions and material",
        (
            "plates",
            "crust",
            "crust-regions",
            "continental-weight",
            "subduction-preference-strength",
            "max-plate-weight",
            "region-overlap",
        ),
    ),
    ("Volcanism", ("volcanic-relief", "volcanic-strength")),
    ("Surface", ("land-height", "water-depth", "slope", "local-relief", "roughness")),
    (
        "Climate",
        (
            "temperature",
            "axial-coordinate",
            "circulation-strength",
            "wind-speed",
            "wind-vectors",
        ),
    ),
)


class WorldgenWindow(QMainWindow):
    """Own native controls while the scene owns sampled data and rendering."""

    def __init__(
        self,
        world: GeneratedWorld,
        *,
        layer: str = "elevation",
        field_frequency: int = 80,
        terrain_relief: bool = False,
        vertical_exaggeration: float = 1.0,
        sea_level: bool = False,
        elevation_range: tuple[float, float] | None = None,
        hex_edges: bool = True,
        continuous_field: bool = True,
        rebuild_config: WorldgenConfig | None = None,
    ) -> None:
        super().__init__()
        self.resize(1200, 820)
        self.plotter = QtInteractor(self, auto_update=False)
        self.setCentralWidget(self.plotter.interactor)
        self.scene = WorldgenViewer(
            world,
            plotter=self.plotter,
            field_frequency=field_frequency,
            terrain_relief=terrain_relief,
            vertical_exaggeration=vertical_exaggeration,
            sea_level=sea_level,
            elevation_range=elevation_range,
            hex_edges=hex_edges,
            continuous_field=continuous_field,
        )
        self.scene.select_layer(layer)
        self.rebuilder = (
            WorldRebuilder(rebuild_config, self.scene.replace_world)
            if rebuild_config is not None
            else None
        )
        self.layer_actions: dict[str, QAction] = {}
        self.display_actions: dict[str, QAction] = {}
        self._build_settings()
        self._build_menus()
        self._sync_controls()
        self._update_title()
        self.statusBar().showMessage(
            "Drag to rotate · scroll to zoom · use Layers to inspect the world"
        )

    def _build_menus(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        save = file_menu.addAction("Save &screenshot…")
        save.setShortcut(QKeySequence.StandardKey.Save)
        save.triggered.connect(self._save_screenshot)
        file_menu.addSeparator()
        close = file_menu.addAction("&Close")
        close.setShortcut(QKeySequence.StandardKey.Close)
        close.triggered.connect(self.close)

        layers = self.menuBar().addMenu("&Layers")
        self.layer_group = QActionGroup(self)
        self.layer_group.setExclusive(True)
        for title, names in LAYER_MENUS:
            menu = layers.addMenu(title)
            for name in names:
                action = menu.addAction(name.replace("-", " ").capitalize())
                action.setObjectName(f"layer-{name}")
                action.setCheckable(True)
                self.layer_group.addAction(action)
                action.triggered.connect(partial(self._select_layer, name))
                self.layer_actions[name] = action

        view = self.menuBar().addMenu("&View")
        for name, title, setter in (
            ("terrain-relief", "Terrain relief", self.scene.set_terrain_relief),
            ("water", "Water surface", self.scene.set_sea_level),
            ("hex-edges", "Hex outlines", self.scene.set_hex_edges),
            ("continuous-field", "Continuous field", self.scene.set_continuous_field),
        ):
            action = view.addAction(title)
            action.setObjectName(name)
            action.setCheckable(True)
            action.toggled.connect(partial(self._change_display, setter))
            self.display_actions[name] = action
        self.display_actions["continuous-field"].setToolTip(
            "Use dense field samples; categorical and surface layers still use hex samples"
        )
        view.addSeparator()
        view.addAction(self.settings_dock.toggleViewAction())
        reset = view.addAction("Reset camera")
        reset.setShortcut("Home")
        reset.triggered.connect(self._reset_camera)

        generation = self.menuBar().addMenu("&Generation")
        self.rebuild_action = generation.addAction("Rebuild world")
        self.rebuild_action.setShortcut("Ctrl+R")
        self.rebuild_action.setEnabled(self.rebuilder is not None)
        self.rebuild_action.triggered.connect(self._rebuild)
        settings = generation.addAction("Generation settings")
        settings.triggered.connect(self._show_settings)

    def _build_settings(self) -> None:
        self.settings_dock = QDockWidget("Settings", self)
        self.settings_dock.setObjectName("world-settings")
        self.settings_dock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea
        )
        self.settings_dock.setMinimumWidth(260)
        self.settings_dock.setMaximumWidth(340)
        panel = QWidget()
        layout = QVBoxLayout(panel)

        display = QGroupBox("Display")
        display_layout = QVBoxLayout(display)
        self.exaggeration = QDoubleSpinBox()
        self.exaggeration.setObjectName("vertical-exaggeration")
        self.exaggeration.setRange(0.0, max(100.0, self.scene.vertical_exaggeration))
        self.exaggeration.setDecimals(2)
        self.exaggeration.setSuffix(" ×")
        self.exaggeration.setValue(self.scene.vertical_exaggeration)
        form = QFormLayout()
        form.addRow("Exaggeration", self.exaggeration)
        display_layout.addLayout(form)
        self.exaggeration_slider = QSlider(Qt.Orientation.Horizontal)
        self.exaggeration_slider.setRange(0, round(self.exaggeration.maximum() * 10))
        self.exaggeration_slider.setValue(round(self.scene.vertical_exaggeration * 10))
        self.exaggeration_slider.setTracking(False)
        self.exaggeration_slider.valueChanged.connect(
            lambda value: self.exaggeration.setValue(value / 10)
        )
        self.exaggeration.valueChanged.connect(self._change_exaggeration)
        display_layout.addWidget(self.exaggeration_slider)
        hint = QLabel(
            "Display settings do not regenerate the world.\nCategorical and surface layers use hex samples."
        )
        hint.setWordWrap(True)
        display_layout.addWidget(hint)
        layout.addWidget(display)

        generation = QGroupBox("Generation")
        generation_layout = QVBoxLayout(generation)
        self.plate_count = QSpinBox()
        self.plate_count.setObjectName("plate-count")
        count = len(self.scene.world.field.geology.plate_influence.partition.seeds)
        self.plate_count.setRange(2, max(256, count))
        self.plate_count.setValue(count)
        self.plate_count.setEnabled(self.rebuilder is not None)
        form = QFormLayout()
        form.addRow("Plate count", self.plate_count)
        generation_layout.addLayout(form)
        self.rebuild_button = QPushButton("Rebuild world")
        self.rebuild_button.setEnabled(self.rebuilder is not None)
        self.rebuild_button.clicked.connect(self._rebuild)
        generation_layout.addWidget(self.rebuild_button)
        self.rebuild_status = QLabel(
            "Change plate count, then rebuild. The seed, camera, and display settings are retained."
            if self.rebuilder
            else "Rebuild controls require a world-generation configuration."
        )
        self.rebuild_status.setWordWrap(True)
        self.rebuild_status.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        generation_layout.addWidget(self.rebuild_status)
        layout.addWidget(generation)
        layout.addStretch()
        self.settings_dock.setWidget(panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.settings_dock)
        self.resizeDocks([self.settings_dock], [300], Qt.Orientation.Horizontal)

    def _select_layer(self, layer: str, checked: bool = True) -> None:
        self.scene.select_layer(layer)
        self._sync_controls()
        self._update_title()

    def _change_display(self, setter: Callable[[bool], None], enabled: bool) -> None:
        setter(enabled)
        self._sync_controls()

    def _sync_controls(self) -> None:
        for name, action in self.layer_actions.items():
            with QSignalBlocker(action):
                action.setChecked(name == self.scene.layer)
        for name, enabled in (
            ("terrain-relief", self.scene.terrain_relief),
            ("water", self.scene.sea_level),
            ("hex-edges", self.scene.hex_edges),
            ("continuous-field", self.scene.continuous_field),
        ):
            with QSignalBlocker(self.display_actions[name]):
                self.display_actions[name].setChecked(enabled)

    def _change_exaggeration(self, value: float) -> None:
        with QSignalBlocker(self.exaggeration_slider):
            self.exaggeration_slider.setValue(round(value * 10))
        self.scene.set_vertical_exaggeration(value)

    def _reset_camera(self) -> None:
        self.scene.prepare_camera()
        self.plotter.camera.zoom(1.3)
        self.plotter.render()

    def _show_settings(self) -> None:
        self.settings_dock.show()
        self.settings_dock.raise_()

    def _update_title(self) -> None:
        title = self.scene.layer.replace("-", " ").capitalize()
        self.setWindowTitle(f"Worldgen — {title}")

    def _rebuild(self) -> None:
        count = self.plate_count.value()
        self.rebuild_status.setText(f"Rebuilding {count} plates…")
        self.statusBar().showMessage("Rebuilding world…")
        self.rebuild_button.setEnabled(False)
        self.rebuild_action.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        QApplication.processEvents(QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)
        timing = self.rebuilder.rebuild(count)
        QApplication.restoreOverrideCursor()
        self.rebuild_button.setEnabled(True)
        self.rebuild_action.setEnabled(True)
        message = (
            f"{count} plates · generation {timing.generation_seconds:.3f}s · "
            f"display {timing.display_seconds:.3f}s · total {timing.total_seconds:.3f}s"
        )
        self.rebuild_status.setText(message)
        self.statusBar().showMessage(message)
        self._sync_controls()
        print(message, flush=True)

    def _save_screenshot(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Save globe screenshot", "world.png", "PNG image (*.png)"
        )
        if path:
            self.plotter.screenshot(path)
            self.statusBar().showMessage(f"Screenshot saved: {path}")

    def closeEvent(self, event: QCloseEvent) -> None:
        self.plotter.close()
        super().closeEvent(event)


def show_world_window(
    world: GeneratedWorld,
    *,
    layer: str,
    terrain_relief: bool,
    vertical_exaggeration: float,
    sea_level: bool,
    elevation_range: tuple[float, float] | None,
    hex_edges: bool,
    field_frequency: int,
    continuous_field: bool,
    screenshot: str | None,
    rebuild_config: WorldgenConfig | None,
) -> None:
    """Run the native menu-driven viewer; off-screen exports never import Qt."""
    application = QApplication.instance() or QApplication(sys.argv[:1])
    window = WorldgenWindow(
        world,
        layer=layer,
        terrain_relief=terrain_relief,
        vertical_exaggeration=vertical_exaggeration,
        sea_level=sea_level,
        elevation_range=elevation_range,
        hex_edges=hex_edges,
        field_frequency=field_frequency,
        continuous_field=continuous_field,
        rebuild_config=rebuild_config,
    )
    window.show()
    application.processEvents()
    window._reset_camera()
    if screenshot is not None:
        window.plotter.screenshot(screenshot)
    application.exec()
