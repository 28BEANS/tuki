import 'landmark.dart';

/// A location suggestion that can be resolved to an exact trip coordinate.
class PlaceSuggestion {
  final String id;
  final String name;
  final String? subtitle;
  final double? latitude;
  final double? longitude;
  final bool requiresResolution;

  const PlaceSuggestion({
    required this.id,
    required this.name,
    required this.requiresResolution,
    this.subtitle,
    this.latitude,
    this.longitude,
  });

  factory PlaceSuggestion.fromGooglePrediction(Map<String, dynamic> json) {
    final formatting =
        json['structured_formatting'] as Map<String, dynamic>? ?? const {};
    return PlaceSuggestion(
      id: json['place_id'] as String,
      name:
          formatting['main_text'] as String? ??
          json['description'] as String? ??
          'Selected place',
      subtitle: formatting['secondary_text'] as String?,
      requiresResolution: true,
    );
  }

  factory PlaceSuggestion.fromLandmark(Landmark landmark) {
    return PlaceSuggestion(
      id: landmark.id,
      name: landmark.name,
      subtitle: landmark.barangayName,
      latitude: landmark.latitude,
      longitude: landmark.longitude,
      requiresResolution: false,
    );
  }

  Landmark toLandmark() {
    final resolvedLatitude = latitude;
    final resolvedLongitude = longitude;
    if (resolvedLatitude == null || resolvedLongitude == null) {
      throw StateError('Place suggestion has not been resolved.');
    }
    return Landmark(
      id: id,
      name: name,
      aliases: const [],
      category: 'place',
      latitude: resolvedLatitude,
      longitude: resolvedLongitude,
      barangayName: subtitle,
    );
  }
}
