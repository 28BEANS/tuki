import 'dart:convert';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../models/user_profile.dart';

/// Service class to communicate with the FastAPI backend auth endpoints.
class BackendAuthService {
  /// Sync user profile with FastAPI backend database after Supabase signup/login.
  /// This endpoint is idempotent.
  Future<UserProfile> syncProfile({
    required String id,
    required String email,
    String? fullName,
  }) async {
    final url = Uri.parse('${AppConfig.backendUrl}/api/v1/auth/signup');
    
    final response = await http.post(
      url,
      headers: {
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'id': id,
        'email': email,
        'full_name': fullName,
      }),
    );

    if (response.statusCode >= 200 && response.statusCode < 300) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return UserProfile.fromJson(json);
    } else {
      throw Exception('Failed to sync profile: ${response.statusCode} - ${response.body}');
    }
  }

  /// Fetch authenticated user profile details from the backend using the JWT token.
  Future<UserProfile> getProfile({required String jwtToken}) async {
    final url = Uri.parse('${AppConfig.backendUrl}/api/v1/auth/me');

    final response = await http.get(
      url,
      headers: {
        'Authorization': 'Bearer $jwtToken',
        'Content-Type': 'application/json',
      },
    );

    if (response.statusCode == 200) {
      final json = jsonDecode(response.body) as Map<String, dynamic>;
      return UserProfile.fromJson(json);
    } else {
      throw Exception('Failed to fetch profile: ${response.statusCode} - ${response.body}');
    }
  }
}
