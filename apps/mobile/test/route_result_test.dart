import 'package:flutter_test/flutter_test.dart';
import 'package:tuki/models/route_result.dart';

void main() {
  test('route waypoints preserve exact origin and destination coordinates', () {
    final result = RouteResult.fromJson({
      'total_fare': 13,
      'total_distance_m': 2500,
      'travel_time_min': 15,
      'transfers': 0,
      'segments': [
        {
          'mode': 'jeep',
          'waypoints': [
            [15.133078, 120.590011],
            [15.167271, 120.580113],
          ],
        },
      ],
      'instructions': [],
    });

    final waypoints = result.segments.single.waypoints!;
    expect(waypoints.first, [15.133078, 120.590011]);
    expect(waypoints.last, [15.167271, 120.580113]);
  });
}
