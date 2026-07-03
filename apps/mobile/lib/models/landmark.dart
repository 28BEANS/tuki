/// Model for a Landmark from the backend.
class Landmark {
  final String id;
  final String name;
  final List<String> aliases;
  final String category;
  final double latitude;
  final double longitude;
  final String? barangayName;

  const Landmark({
    required this.id,
    required this.name,
    required this.aliases,
    required this.category,
    required this.latitude,
    required this.longitude,
    this.barangayName,
  });

  factory Landmark.fromJson(Map<String, dynamic> json) {
    return Landmark(
      id: json['id'] as String,
      name: json['name'] as String,
      aliases: (json['aliases'] as List<dynamic>?)
              ?.map((e) => e as String)
              .toList() ??
          [],
      category: json['category'] as String,
      latitude: (json['latitude'] as num).toDouble(),
      longitude: (json['longitude'] as num).toDouble(),
      barangayName: json['barangay_name'] as String?,
    );
  }
}
