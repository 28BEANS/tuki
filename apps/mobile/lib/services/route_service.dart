import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../models/route_result.dart';

/// Service that calls POST /api/v1/calculate-route on the Tuki backend.
class RouteService {
  Future<RouteResult> calculateRoute({
    required double originLat,
    required double originLon,
    required double destinationLat,
    required double destinationLon,
    String prefer = 'fastest',
    bool isStudent = false,
  }) async {
    final url = Uri.parse('${AppConfig.backendUrl}/api/v1/calculate-route');

    final response = await http.post(
      url,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'origin_lat': originLat,
        'origin_lon': originLon,
        'destination_lat': destinationLat,
        'destination_lon': destinationLon,
        'prefer': prefer,
        'is_student': isStudent,
      }),
    );

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return RouteResult.fromJson(json);
    } else {
      throw Exception(
          'Failed to calculate route: ${response.statusCode} — ${response.body}');
    }
  }
}
