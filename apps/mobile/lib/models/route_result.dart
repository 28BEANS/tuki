library;

class RouteSegment {
  final String mode; // 'jeep' | 'walk' | 'tricycle'
  final String? route;
  final String? routeColor;
  final String? boardAt;
  final double? boardLat;
  final double? boardLon;
  final String? alightAt;
  final double? alightLat;
  final double? alightLon;
  final double? distanceM;
  final double? durationMin;
  final double? fare;
  final List<List<double>>? waypoints;

  const RouteSegment({
    required this.mode,
    this.route,
    this.routeColor,
    this.boardAt,
    this.boardLat,
    this.boardLon,
    this.alightAt,
    this.alightLat,
    this.alightLon,
    this.distanceM,
    this.durationMin,
    this.fare,
    this.waypoints,
  });

  factory RouteSegment.fromJson(Map<String, dynamic> json) {
    return RouteSegment(
      mode: json['mode'] as String,
      route: json['route'] as String?,
      routeColor: json['route_color'] as String?,
      boardAt: json['board_at'] as String?,
      boardLat: (json['board_lat'] as num?)?.toDouble(),
      boardLon: (json['board_lon'] as num?)?.toDouble(),
      alightAt: json['alight_at'] as String?,
      alightLat: (json['alight_lat'] as num?)?.toDouble(),
      alightLon: (json['alight_lon'] as num?)?.toDouble(),
      distanceM: (json['distance_m'] as num?)?.toDouble(),
      durationMin: (json['duration_min'] as num?)?.toDouble(),
      fare: (json['fare'] as num?)?.toDouble(),
      waypoints: (json['waypoints'] as List<dynamic>?)
          ?.map((wp) =>
              (wp as List<dynamic>).map((v) => (v as num).toDouble()).toList())
          .toList(),
    );
  }
}

class NavigationInstruction {
  final int step;
  final String instruction;
  final String mode;

  const NavigationInstruction({
    required this.step,
    required this.instruction,
    required this.mode,
  });

  factory NavigationInstruction.fromJson(Map<String, dynamic> json) {
    return NavigationInstruction(
      step: json['step'] as int,
      instruction: json['instruction'] as String,
      mode: json['mode'] as String,
    );
  }
}

class RouteResult {
  final double totalFare;
  final double totalDistanceM;
  final double travelTimeMin;
  final List<RouteSegment> segments;
  final List<NavigationInstruction> instructions;
  final int transfers;

  const RouteResult({
    required this.totalFare,
    required this.totalDistanceM,
    required this.travelTimeMin,
    required this.segments,
    required this.instructions,
    required this.transfers,
  });

  factory RouteResult.fromJson(Map<String, dynamic> json) {
    return RouteResult(
      totalFare: (json['total_fare'] as num).toDouble(),
      totalDistanceM: (json['total_distance_m'] as num).toDouble(),
      travelTimeMin: (json['travel_time_min'] as num).toDouble(),
      segments: (json['segments'] as List<dynamic>)
          .map((e) => RouteSegment.fromJson(e as Map<String, dynamic>))
          .toList(),
      instructions: (json['instructions'] as List<dynamic>)
          .map((e) => NavigationInstruction.fromJson(e as Map<String, dynamic>))
          .toList(),
      transfers: json['transfers'] as int,
    );
  }
}
