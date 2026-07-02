import 'dart:io';
import 'package:flutter/foundation.dart';

/// Centralized application configuration.
/// Can be customized using --dart-define arguments during build or run.
class AppConfig {
  /// Supabase project URL
  static const String supabaseUrl = String.fromEnvironment(
    'SUPABASE_URL',
    defaultValue: 'https://helmnwygpbrshdbyjfpq.supabase.co',
  );

  /// Supabase anonymous/publishable key
  static const String supabaseAnonKey = String.fromEnvironment(
    'SUPABASE_ANON_KEY',
    defaultValue: 'sb_publishable_3vFIQvVAa6h0FMMi0ihYlw_2qXcPQj6',
  );

  /// FastAPI Backend base API URL
  static String get backendUrl {
    const fromEnv = String.fromEnvironment('BACKEND_URL');
    if (fromEnv.isNotEmpty) {
      return fromEnv;
    }
    
    if (kIsWeb) {
      return 'http://localhost:8000';
    }
    
    // Fallback based on platform for local emulator/simulator testing
    try {
      if (Platform.isAndroid) {
        return 'http://10.0.2.2:8000';
      }
    } catch (_) {
      // Platform check may throw on unsupported web/platforms
    }
    
    return 'http://localhost:8000';
  }
}
