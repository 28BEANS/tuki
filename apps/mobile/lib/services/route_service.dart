import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../models/route_result.dart';

/// Exception thrown when the routing graph is unavailable (HTTP 503).
class RoutingUnavailableException implements Exception {
  final String message;
  const RoutingUnavailableException(this.message);
  @override
  String toString() => message;
}

/// Exception thrown when no route exists between the locations (HTTP 404).
class NoRouteFoundException implements Exception {
  final String message;
  const NoRouteFoundException(this.message);
  @override
  String toString() => message;
}

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
    } else if (response.statusCode == 503) {
      throw const RoutingUnavailableException(
        'Routing is temporarily unavailable. Please try again later.',
      );
    } else if (response.statusCode == 404) {
      throw const NoRouteFoundException(
        'No route found between the selected locations.',
      );
    } else {
      throw Exception(
          'Failed to calculate route: ${response.statusCode} — ${response.body}');
    }
  }
}
