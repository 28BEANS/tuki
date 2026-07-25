import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:tuki/models/place_suggestion.dart';
import 'package:tuki/services/place_service.dart';

void main() {
  test('autocomplete parses exact Google place identifiers', () async {
    final client = MockClient((request) async {
      expect(request.url.path, '/api/v1/places/autocomplete');
      expect(request.url.queryParameters['query'], 'Holy Angel');
      return http.Response('''
        {
          "predictions": [
            {
              "place_id": "hau-place-id",
              "description": "Holy Angel University, Angeles",
              "structured_formatting": {
                "main_text": "Holy Angel University",
                "secondary_text": "Angeles, Pampanga"
              }
            }
          ]
        }
        ''', 200);
    });
    final service = PlaceService(client: client);

    final results = await service.autocomplete('Holy Angel');

    expect(results, hasLength(1));
    expect(results.single.id, 'hau-place-id');
    expect(results.single.name, 'Holy Angel University');
    expect(results.single.requiresResolution, isTrue);
  });

  test(
    'place details preserve backend latitude and longitude ordering',
    () async {
      final client = MockClient((request) async {
        expect(request.url.path, '/api/v1/places/details');
        expect(request.url.queryParameters['place_id'], 'hau-place-id');
        return http.Response('''
        {
          "place_id": "hau-place-id",
          "name": "Holy Angel University",
          "formatted_address": "Holy Angel Street, Angeles",
          "latitude": 15.133078,
          "longitude": 120.590011
        }
        ''', 200);
      });
      final service = PlaceService(client: client);
      const suggestion = PlaceSuggestion(
        id: 'hau-place-id',
        name: 'Holy Angel University',
        requiresResolution: true,
      );

      final location = await service.resolve(suggestion);

      expect(location.latitude, 15.133078);
      expect(location.longitude, 120.590011);
    },
  );
}
