/// Model for a Jeep Route from the backend.
class JeepRoute {
  final String id;
  final String routeName;
  final String? routeColor;
  final String? description;
  final String? operatingDirection;

  const JeepRoute({
    required this.id,
    required this.routeName,
    this.routeColor,
    this.description,
    this.operatingDirection,
  });

  factory JeepRoute.fromJson(Map<String, dynamic> json) {
    return JeepRoute(
      id: json['id'] as String,
      routeName: json['route_name'] as String,
      routeColor: json['route_color'] as String?,
      description: json['description'] as String?,
      operatingDirection: json['operating_direction'] as String?,
    );
  }
}
