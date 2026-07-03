import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../models/jeep_route.dart';

/// Service to communicate with the backend Jeep Routes API.
class JeepRouteService {
  /// Fetch all available jeep routes.
  Future<List<JeepRoute>> listRoutes() async {
    final uri = Uri.parse('${AppConfig.backendUrl}/api/v1/jeep-routes');

    final response = await http.get(uri, headers: {
      'Content-Type': 'application/json',
    });

    if (response.statusCode == 200) {
      final items = jsonDecode(response.body) as List<dynamic>;
      return items.map((e) => JeepRoute.fromJson(e as Map<String, dynamic>)).toList();
    } else {
      throw Exception('Failed to fetch routes: ${response.statusCode}');
    }
  }
}
