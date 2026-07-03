import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../models/landmark.dart';

/// Service to communicate with the backend Landmarks API.
class LandmarkService {
  /// Search landmarks by text query.
  Future<List<Landmark>> searchLandmarks({
    required String query,
    int pageSize = 10,
  }) async {
    final uri = Uri.parse('${AppConfig.backendUrl}/api/v1/landmarks').replace(
      queryParameters: {
        'q': query,
        'page_size': pageSize.toString(),
      },
    );

    final response = await http.get(uri, headers: {
      'Content-Type': 'application/json',
    });

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      final items = json['items'] as List<dynamic>;
      return items.map((e) => Landmark.fromJson(e as Map<String, dynamic>)).toList();
    } else {
      throw Exception('Failed to search landmarks: ${response.statusCode}');
    }
  }

  /// Get nearby landmarks based on latitude/longitude.
  Future<List<Landmark>> getNearbyLandmarks({
    required double latitude,
    required double longitude,
    double radiusM = 1000,
  }) async {
    final uri = Uri.parse('${AppConfig.backendUrl}/api/v1/landmarks').replace(
      queryParameters: {
        'latitude': latitude.toString(),
        'longitude': longitude.toString(),
        'radius_m': radiusM.toString(),
      },
    );

    final response = await http.get(uri, headers: {
      'Content-Type': 'application/json',
    });

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      final items = json['items'] as List<dynamic>;
      return items.map((e) => Landmark.fromJson(e as Map<String, dynamic>)).toList();
    } else {
      throw Exception('Failed to get nearby landmarks: ${response.statusCode}');
    }
  }
}
