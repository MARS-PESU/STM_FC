
import sys
import folium
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QLabel, QComboBox, QSpinBox)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtPositioning import QGeoPositionInfoSource 
import os
import tempfile

class GPSMapTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GPS Map")

        # Initialize properties
        self.map_file = os.path.join(tempfile.gettempdir(), "gps_map.html")
        self.current_lat = None
        self.current_lon = None
        self.location_source = None

        # Setup the UI and location services
        self.init_ui()
        self.setup_location_services()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # === COORDINATE INPUT SECTION ===
        coord_frame = QWidget()
        coord_frame.setMaximumHeight(50)
        coord_layout = QHBoxLayout(coord_frame)
        coord_layout.setContentsMargins(5, 5, 5, 5)

        lat_label = QLabel("Latitude:")
        lat_label.setMinimumWidth(60)
        self.lat_input = QLineEdit()
        self.lat_input.setPlaceholderText("Enter latitude (-90 to 90)")
        self.lat_input.returnPressed.connect(self.update_map_to_coords)
        self.lat_input.setMaximumWidth(150)

        lon_label = QLabel("Longitude:")
        lon_label.setMinimumWidth(70)
        self.lon_input = QLineEdit()
        self.lon_input.setPlaceholderText("Enter longitude (-180 to 180)")
        self.lon_input.returnPressed.connect(self.update_map_to_coords)
        self.lon_input.setMaximumWidth(150)

        coord_layout.addWidget(lat_label)
        coord_layout.addWidget(self.lat_input)
        coord_layout.addWidget(lon_label)
        coord_layout.addWidget(self.lon_input)
        coord_layout.addStretch()

        # === CONTROLS SECTION ===
        controls_frame = QWidget()
        controls_frame.setMaximumHeight(50)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(5, 5, 5, 5)

        self.search_button = QPushButton("\ud83c\udf0f Go to Coordinates")
        self.search_button.clicked.connect(self.update_map_to_coords)
        self.search_button.setMaximumWidth(150)

        self.current_location_button = QPushButton("\ud83d\udccd My Location")
        # The button is now enabled and connected
        self.current_location_button.clicked.connect(self.get_current_location)
        self.current_location_button.setMaximumWidth(120)

        map_label = QLabel("Map Style:")
        self.map_type = QComboBox()
        self.map_type.addItems([
            "OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron"
        ])
        self.map_type.currentTextChanged.connect(self.update_map_style)
        self.map_type.setMaximumWidth(140)

        zoom_label = QLabel("Zoom:")
        self.zoom_spinbox = QSpinBox()
        self.zoom_spinbox.setRange(1, 18)
        self.zoom_spinbox.setValue(15)
        self.zoom_spinbox.valueChanged.connect(self.update_zoom)
        self.zoom_spinbox.setMaximumWidth(60)

        controls_layout.addWidget(self.search_button)
        controls_layout.addWidget(self.current_location_button)
        controls_layout.addStretch()
        controls_layout.addWidget(map_label)
        controls_layout.addWidget(self.map_type)
        controls_layout.addWidget(zoom_label)
        controls_layout.addWidget(self.zoom_spinbox)

        self.status_label = QLabel("\ud83c\udf0d Ready.")
        self.status_label.setMaximumHeight(25)
        self.status_label.setStyleSheet("QLabel { color: #2E8B57; font-weight: bold; }")

        self.webview = QWebEngineView()
        self.webview.setMinimumHeight(500)

        main_layout.addWidget(coord_frame)
        main_layout.addWidget(controls_frame)
        main_layout.addWidget(self.status_label)
        main_layout.addWidget(self.webview, 1)

        self.setLayout(main_layout)

    def setup_location_services(self):
        """Initializes the location source and connects signals."""
        self.location_source = QGeoPositionInfoSource.createDefaultSource(self)
        if self.location_source:
            # Connect signals to handlers
            self.location_source.positionUpdated.connect(self.position_updated)
            self.location_source.error.connect(self.position_error)
            # Start by getting the current location
            self.get_current_location()
        else:
            # If no location service is available
            self.status_label.setText("Location services not available.")
            self.current_location_button.setDisabled(True)
            # Show a default map (e.g., world view)
            self.generate_map(0, 0, 2)


    def get_current_location(self):
        """Requests a single update from the location source."""
        if self.location_source:
            self.status_label.setText("Acquiring GPS location...")
            self.location_source.requestUpdate(60000) # 60-second timeout

    def position_updated(self, position):
        """Handles the positionUpdated signal from the location source."""
        coord = position.coordinate()
        lat = coord.latitude()
        lon = coord.longitude()

        self.current_lat = lat
        self.current_lon = lon

        # Update the input fields and status
        self.lat_input.setText(f"{lat:.6f}")
        self.lon_input.setText(f"{lon:.6f}")
        self.status_label.setText(f"Current location: {lat:.6f}, {lon:.6f}")

        # Generate the map with the new location
        self.generate_map(lat, lon)

    def position_error(self, error):
        """Handles errors from the location source."""
        error_messages = {
            QGeoPositionInfoSource.AccessError: "Access denied",
            QGeoPositionInfoSource.ClosedError: "Service closed",
            QGeoPositionInfoSource.UnknownSourceError: "Unknown error",
        }
        message = error_messages.get(error, "An unknown error occurred")
        self.status_label.setText(f"Error getting location: {message}")

    def get_map_tiles(self):
        tile_map = {
            "OpenStreetMap": "OpenStreetMap",
            "Stamen Terrain": "Stamen Terrain",
            "Stamen Toner": "Stamen Toner",
            "CartoDB positron": "CartoDB positron"
        }
        return tile_map.get(self.map_type.currentText(), "OpenStreetMap")

    def generate_map(self, lat, lon, zoom=None):
        try:
            # Use provided zoom or the spinbox value
            map_zoom = zoom if zoom is not None else self.zoom_spinbox.value()

            m = folium.Map(
                location=[lat, lon],
                zoom_start=map_zoom,
                tiles=self.get_map_tiles()
            )

            popup_text = f"<b>Location</b><br>Latitude: {lat:.6f}<br>Longitude: {lon:.6f}"
            folium.Marker(
                [lat, lon],
                tooltip="Click for details",
                popup=folium.Popup(popup_text, max_width=200)
            ).add_to(m)

            folium.Circle(
                [lat, lon],
                radius=500,
                popup="500m radius",
                color="blue",
                fill=True,
                fillOpacity=0.2
            ).add_to(m)

            m.save(self.map_file)
            self.webview.setUrl(QUrl.fromLocalFile(self.map_file))

        except Exception as e:
            self.status_label.setText(f"Error generating map: {e}")

    def update_map_to_coords(self):
        try:
            lat_text = self.lat_input.text().strip()
            lon_text = self.lon_input.text().strip()

            if not lat_text or not lon_text:
                self.status_label.setText("Please enter both latitude and longitude")
                return

            lat = float(lat_text)
            lon = float(lon_text)

            if not (-90 <= lat <= 90):
                self.status_label.setText("Latitude must be between -90 and 90")
                return
            if not (-180 <= lon <= 180):
                self.status_label.setText("Longitude must be between -180 and 180")
                return

            self.current_lat = lat
            self.current_lon = lon

            self.status_label.setText(f"Showing: {lat:.6f}, {lon:.6f}")
            self.generate_map(lat, lon)

        except ValueError:
            self.status_label.setText("Invalid coordinates. Please enter valid numbers.")
        except Exception as e:
            self.status_label.setText(f"Error: {e}")

    def update_map_style(self):
        if self.current_lat is not None and self.current_lon is not None:
            self.generate_map(self.current_lat, self.current_lon)

    def update_zoom(self):
        if self.current_lat is not None and self.current_lon is not None:
            self.generate_map(self.current_lat, self.current_lon)

    def closeEvent(self, event):
        if os.path.exists(self.map_file):
            try:
                os.remove(self.map_file)
            except OSError:
                pass
        event.accept()