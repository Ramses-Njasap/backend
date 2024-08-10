from django.db import models
from django.conf import settings
from django.http import HttpRequest

from accounts.models.devices import DeviceLoginHistory
from utilities.analysis.ip_analysis import IPAddressAnalyzer

from difflib import SequenceMatcher
import numpy as np


class MatchDeviceAnalysis:
    def __init__(self, devices: models.QuerySet, request: HttpRequest):
        """
        Initialize with the user's devices and the current request containing device metadata.
        """
        self.devices = devices
        self.request = request

    def get_device_ip_list(self, device_instance: models.Model) -> np.ndarray:
        """
        Retrieve and return a NumPy array of IP addresses for a given device.

        Args:
            device_instance (models.Model): The device instance to retrieve IP addresses for.

        Returns:
            np.ndarray: Array of IP addresses associated with the device.
        """
        # Fetch IP addresses from the login history for the given device
        ip_addresses = DeviceLoginHistory.objects.filter(
            device=device_instance
        ).values_list('ip_address', flat=True)
        return np.array(list(ip_addresses))

    def compute_ip_similarity(self) -> list:
        """
        Match the current device against the user's existing devices based on IP analysis.

        Returns:
            list: List of matched devices with their similarity scores.
        """
        current_ip = self.request.device_meta_info["ip"]

        # Initialize the IP address analyzer with the current IP
        analyzer = IPAddressAnalyzer(
            base_ip=current_ip, octet_count=2, n_clusters=2, similarity_threshold=100
        )
        
        matched_devices = []

        for device in self.devices:
            # Get the list of IP addresses associated with the device
            device_ip_list = self.get_device_ip_list(device)
            if device_ip_list.size == 0:
                continue

            # Perform IP analysis and get the similarity score
            ip_analysis_results = analyzer.analyze(device_ip_list.tolist())
            ip_analysis_score = ip_analysis_results['total_probability_score']

            # Check if the similarity score meets the threshold
            if ip_analysis_score >= settings.APPLICATION_SETTINGS["IP_MATCH_PROBABILITY_PASS_SCORE"]:
                matched_devices.append({
                    "device": device,
                    "score": ip_analysis_score
                })

        return matched_devices

    def compute_device_data_similarity(self) -> list:
        """
        Match the current device against the user's existing devices based on device data analysis.

        Returns:
            list: List of matched devices with their similarity scores.
        """
        meta_info = self.request.device_meta_info
        matched_devices = []

        for device in self.devices:
            score = 0  # Initialize similarity score
            condition_count = 0  # Initialize condition count

            # Check client version
            if meta_info["client_clientversion"] == device.client_type:
                score += 1
                condition_count += 1

            # Check OS version
            if meta_info["os_osversion"] == device.client_type:
                score += 1
                condition_count += 1

            # Check device type
            if meta_info["device_type"] == device.device_type:
                score += 1
                condition_count += 1

            # Calculate user agent similarity
            user_agent_similarity = SequenceMatcher(
                None, str(meta_info["user_agent"]), device.user_agent
            ).ratio()
            score += user_agent_similarity
            condition_count += 1

            # Calculate total similarity score
            if condition_count > 0:
                total_similarity_score = (score / condition_count) * condition_count
            else:
                total_similarity_score = 0

            # Check if the similarity score meets the threshold
            if total_similarity_score >= settings.APPLICATION_SETTINGS["DEVICE_DATA_SIMILARITY_MATCH_SCORE"]:
                matched_devices.append({
                    "device": device,
                    "score": total_similarity_score
                })

        return matched_devices

    def most_similar(self):
        """
        Find the device with the highest average similarity score based on both IP and device data analysis.

        Returns:
            dict: The most similar device with its average score.
        """
        # Get similarity results from both methods
        ip_analysis = self.compute_ip_similarity()
        device_data_analysis = self.compute_device_data_similarity()

        # Create dictionaries to map device IDs to their scores for quick lookup
        ip_scores = {item['device'].id: item['score'] for item in ip_analysis}
        data_scores = {item['device'].id: item['score'] for item in device_data_analysis}

        # Find common devices and calculate their average scores
        common_devices = []
        for device_id in ip_scores:
            if device_id in data_scores:
                # Calculate the average score
                average_score = (ip_scores[device_id] + data_scores[device_id]) / 2
                
                # Find the device instance with the matching device_id
                matching_device = next(device for device in self.devices if device.id == device_id)
                
                # Append the device and its average score to the common devices list
                common_devices.append({
                    'device': matching_device,
                    'score': average_score
                })

        # Return the device with the highest average score
        if common_devices:
            most_similar_device = max(common_devices, key=lambda x: x['score'])
            return most_similar_device
        
        return None