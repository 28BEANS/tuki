import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/config.dart';
import '../models/landmark.dart';
import '../models/place_suggestion.dart';

/// Google-like autocomplete and exact place resolution through Tuki's backend.
class PlaceService {
  final http.Client _client;

  PlaceService({http.Client? client}) : _client = client ?? http.Client();

  Future<List<PlaceSuggestion>> autocomplete(String query) async {
    final uri = Uri.parse(
      '${AppConfig.backendUrl}/api/v1/places/autocomplete',
    ).replace(queryParameters: {'query': query});
    final response = await _client.get(uri);
    if (response.statusCode != 200) {
      throw Exception('Could not search places (${response.statusCode}).');
    }

    final json = jsonDecode(response.body) as Map<String, dynamic>;
    final predictions = json['predictions'] as List<dynamic>? ?? const [];
    return predictions
        .map(
          (prediction) => PlaceSuggestion.fromGooglePrediction(
            prediction as Map<String, dynamic>,
          ),
        )
        .toList();
  }

  Future<Landmark> resolve(PlaceSuggestion suggestion) async {
    if (!suggestion.requiresResolution) {
      return suggestion.toLandmark();
    }

    final uri = Uri.parse(
      '${AppConfig.backendUrl}/api/v1/places/details',
    ).replace(queryParameters: {'place_id': suggestion.id});
    final response = await _client.get(uri);
    if (response.statusCode != 200) {
      throw Exception('Could not resolve this place (${response.statusCode}).');
    }

    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return Landmark(
      id: json['place_id'] as String,
      name: json['name'] as String,
      aliases: const [],
      category: 'place',
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      barangayName: json['formatted_address'] as String?,
    );
  }
}
