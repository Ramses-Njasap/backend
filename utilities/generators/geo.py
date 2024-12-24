from utilities import response as error_response
from django.conf import settings
from typing import Optional, Dict, List

from django.contrib.gis.geos import Point, Polygon
from django.contrib.gis.db import models

import requests
import logging
import math


class Nominatim:
    def __init__(self, user_id: int, language: str = 'en'):
        self.user_id = user_id
        self.language = language

    def get_location_name(self, longitude: str, latitude: str) -> str:
        feature = self._get_feature_from_coordinates(longitude, latitude)

        if feature:
            return feature.get('place_name', "Unknown Location")
        else:
            return "Unknown Location"

    def get_place_data(self, longitude: str, latitude: str) -> Dict:
        feature = self._get_feature_from_coordinates(longitude, latitude)
        return self._extract_place_data(feature) if feature else {}

    def get_coordinates_from_place(self, place_name: str) -> Dict:
        feature = self._get_feature_from_place_name(place_name)
        return {
            'place_name': feature.get('place_name'),
            'coordinates': feature.get('center'),
            'bbox': feature.get('bbox')
        } if feature else {}

    def get_place_data_from_name(self, place_name: str) -> Dict:
        feature = self._get_feature_from_place_name(place_name)
        return self._extract_place_data(feature) if feature else {}

    def _get_feature_from_coordinates(
            self, longitude: str, latitude: str
    ) -> Optional[Dict]:

        location_data = self.geocode(longitude, latitude)
        return location_data.get('features', [{}])[0] if location_data else None

    def _get_feature_from_place_name(self, place_name: str) -> Optional[Dict]:
        geocoding_data = self.forward_geocode(place_name)
        return geocoding_data.get('features', [{}])[0] if geocoding_data else None

    def geocode(self, longitude: str, latitude: str) -> Optional[Dict]:
        if not self._validate_coordinates(longitude, latitude):
            self._log_error(
                'Invalid Coordinates',
                'Longitude and Latitude are out of valid range.',
                400
            )
            return None

        url = self._build_geocode_url(longitude, latitude)
        return self._perform_request(url)

    def forward_geocode(self, place_name: str) -> Optional[Dict]:
        url = self._build_forward_geocode_url(place_name)
        return self._perform_request(url)

    def _perform_request(self, url: str) -> Optional[Dict]:
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self._log_error('Geocode Request Error', str(e), 500)
            return None

    def _build_geocode_url(self, longitude: str, latitude: str) -> str:
        return (
            f"""https://api.mapbox.com/geocoding/v5/mapbox.places/
            {longitude},{latitude}.json?access_token=
            {settings.APPLICATION_SETTINGS['MAPBOX_API_KEY']}
            &language={self.language}"""
        )

    def _build_forward_geocode_url(self, place_name: str) -> str:
        return (
            f"""https://api.mapbox.com/geocoding/v5/mapbox.places/
            {place_name}.json?access_token=
            {settings.APPLICATION_SETTINGS['MAPBOX_API_KEY']}
            &language={self.language}"""
        )

    def _validate_coordinates(self, longitude: str, latitude: str) -> bool:
        return -180 <= float(longitude) <= 180 and -90 <= float(latitude) <= 90

    def _get_context_value(self, feature: dict, context_type: str) -> Optional[str]:
        for context in feature.get('context', []):
            if context_type in context.get('id', ''):
                return context.get('text')
        return None

    def _extract_place_data(self, feature: dict) -> Dict:
        return {
            'place_name': feature.get('place_name'),
            'country': self._get_context_value(feature, 'country'),
            'region': self._get_context_value(feature, 'region'),
            'city': self._get_context_value(feature, 'place'),
            'postal_code': self._get_context_value(feature, 'postcode'),
            'coordinates': feature.get('center'),
            'bbox': feature.get('bbox')
        }

    # For Elevation
    def get_elevation(self, longitude: str, latitude: str, zoom=15) -> float:
        x_tile, y_tile = self._lat_lon_to_tile(latitude, longitude, zoom)
        url = (
            f"""https://api.mapbox.com/v4/mapbox.terrain-rgb/
            {zoom}/{x_tile}/{y_tile}@2x.pngraw?access_token=
            {settings.APPLICATION_SETTINGS['MAPBOX_API_KEY']}"""
        )

        response = requests.get(url, timeout=60)
        if response.status_code != 200:
            raise Exception(
                f"Failed to retrieve elevation data: {response.status_code}"
            )

        # Extract the RGB values from the image
        rgb = self._extract_rgb_from_image(response.content)
        return self._rgb_to_elevation(rgb)

    def _lat_lon_to_tile(self, lat: float, lon: float, zoom: int):
        lat_rad = math.radians(lat)
        n = 2.0 ** zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int(
            (
                1.0 - math.log(
                    math.tan(lat_rad) + (1 / math.cos(lat_rad))
                ) / math.pi
            ) / 2.0 * n
        )
        return x_tile, y_tile

    def _extract_rgb_from_image(self, image_data: bytes) -> Dict[str, int]:
        from PIL import Image
        from io import BytesIO

        image = Image.open(BytesIO(image_data))
        rgb = image.getpixel((0, 0))
        return {'r': rgb[0], 'g': rgb[1], 'b': rgb[2]}

    def _rgb_to_elevation(self, rgb: Dict[str, int]) -> float:
        r, g, b = rgb['r'], rgb['g'], rgb['b']
        elevation = -10000 + ((r * 256 * 256 + g * 256 + b) * 0.1)
        return elevation

    def _log_error(self, field_error: str, for_developer: str, status_code: int):
        logging.error(f'{field_error}: {for_developer}')
        error_response.errors(
            field_error=field_error,
            for_developer=for_developer,
            code="INTERNAL_SERVER_ERROR",
            status_code=status_code,
            main_thread=False,
            param=self.user_id
        )


class GeospatialBoundaryManager:
    def __init__(self, user_id: int,
                 model_instance: models.Model = None,
                 polygon_field: str = None, save_to_db: bool = True):

        self.user_id = user_id
        self.model_instance = model_instance
        self.polygon_field = polygon_field
        self.save_to_db = save_to_db

    def calculate_centroid(self, polygon: Polygon) -> Point:
        return polygon.centroid

    def create_polygon(self, coordinates: List[Dict[str, float]]) -> Polygon:
        if len(coordinates) < 3:
            self._log_error(
                "At least three points are required to create a polygon.",
                "Insufficient points to form a polygon.",
                'BAD_REQUEST',
                400
            )

            return None

        try:
            points = [
                Point(coord["longitude"], coord["latitude"])
                for coord in coordinates
            ]
        except KeyError as e:
            self._log_error(
                "Missing Location Info",
                f"Missing Coordinate Key(s): {e}",
                'BAD_REQUEST',
                400
            )

            return None

        points.append(points[0])  # Close the polygon
        polygon = Polygon(points)

        if self.save_to_db:
            self._save_polygon_to_db(polygon)

        return polygon

    def _save_polygon_to_db(self, polygon: Polygon):
        if not (self.model_instance and self.polygon_field):
            self._log_error(
                "Model and polygon field must be provided if save_to_db is True.",
                "Missing model or field for database save.",
                "BAD_REQUEST",
                400
            )

            return

        try:
            setattr(self.model_instance, self.polygon_field, polygon)
            geocoding_service = Nominatim(user_id=self.user_id)
            location_name = geocoding_service.get_location_name(
                longitude=self.calculate_centroid(polygon).x,
                latitude=self.calculate_centroid(polygon).y
            )
            setattr(self.model_instance, "location_name", location_name)
            self.model_instance.save()
        except Exception as e:
            self._log_error(
                "Unable to Save Location Info",
                str(e),
                "INTERNAL_SERVER_ERROR",
                500
            )

    def _log_error(self, field_error: str,
                   for_developer: str, code: str,
                   status_code: int):

        logging.error(f'{for_developer}')
        error_response.errors(
            field_error=field_error,
            for_developer=for_developer,
            code=code,
            status_code=status_code,
            main_thread=False,
            param=self.user_id
        )
