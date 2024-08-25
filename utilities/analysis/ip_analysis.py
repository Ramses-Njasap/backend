import numpy as np
import ipaddress
from sklearn.cluster import KMeans

class IPPatternMatcher:
    def __init__(self, base_ip, octet_count=2):
        self.base_ip = base_ip
        self.octet_count = octet_count
        self.base_ip_parts = base_ip.split('.')[:octet_count]

    def find_pattern_based_ips(self, ip_list):
        matching_ips = []
        for ip in ip_list:
            ip_parts = ip.split('.')[:self.octet_count]
            if ip_parts == self.base_ip_parts:
                matching_ips.append(ip)
        return matching_ips

class IPClusterer:
    def __init__(self, n_clusters=2):
        self.n_clusters = n_clusters

    def ip_to_int(self, ip):
        return int(ipaddress.ip_address(ip))

    def cluster_ips(self, ip_list):
        ip_ints = np.array([self.ip_to_int(ip) for ip in ip_list]).reshape(-1, 1)
        kmeans = KMeans(n_clusters=self.n_clusters)
        kmeans.fit(ip_ints)
        labels = kmeans.labels_
        
        clusters = [[] for _ in range(self.n_clusters)]
        for ip, label in zip(ip_list, labels):
            clusters[label].append(ip)
        
        return clusters, labels

class IPSimilarityChecker:
    def __init__(self, base_ip, threshold=100):
        self.base_ip = base_ip
        self.threshold = threshold
        self.base_ip_int = int(ipaddress.ip_address(base_ip))

    def find_similar_ips(self, ip_list):
        similar_ips = []
        for ip in ip_list:
            ip_int = int(ipaddress.ip_address(ip))
            if abs(self.base_ip_int - ip_int) <= self.threshold:
                similar_ips.append(ip)
        return similar_ips

class IPAddressAnalyzer:
    def __init__(self, base_ip, octet_count=2, n_clusters=2, similarity_threshold=100):
        self.pattern_matcher = IPPatternMatcher(base_ip, octet_count)
        self.clusterer = IPClusterer(n_clusters)
        self.similarity_checker = IPSimilarityChecker(base_ip, similarity_threshold)

    def analyze(self, ip_list):
        pattern_based_ips = self.pattern_matcher.find_pattern_based_ips(ip_list)
        clusters, labels = self.clusterer.cluster_ips(ip_list)
        similar_ips = self.similarity_checker.find_similar_ips(ip_list)
        
        # Calculate probability scores
        ip_scores = {}
        for ip in ip_list:
            # Pattern match score
            pattern_score = 1 if ip in pattern_based_ips else 0
            
            # Similarity score
            similarity_score = 1 if ip in similar_ips else 0
            
            # Cluster score
            cluster_index = labels[ip_list.index(ip)]
            cluster_size = len(clusters[cluster_index])
            cluster_score = cluster_size / len(ip_list)
            
            # Combined score
            combined_score = (pattern_score * 0.4) + (similarity_score * 0.4) + (cluster_score * 0.2)
            ip_scores[ip] = combined_score
        
        # Calculate total probability check
        total_score = sum(ip_scores.values()) / len(ip_scores) if ip_scores else 0
        
        return {
            'pattern_based_ips': pattern_based_ips,
            'clusters': clusters,
            'similar_ips': similar_ips,
            'ip_scores': ip_scores,
            'total_probability_score': total_score
        }

# # Example usage
# base_ip = '127.0.0.1'
# ip_list = ['192.168.1.20', '192.168.1.30', '192.168.2.10', '192.168.1.40', '192.168.1.40']

# analyzer = IPAddressAnalyzer(base_ip, octet_count=2, n_clusters=2, similarity_threshold=100)
# analysis_results = analyzer.analyze(ip_list)

# print(f"Analysis results: {analysis_results}")
