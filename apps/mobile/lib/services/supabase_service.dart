import 'package:supabase_flutter/supabase_flutter.dart';

/// Service class to handle client-side Supabase Authentication operations.
class SupabaseService {
  final SupabaseClient _client = Supabase.instance.client;

  /// Get the currently authenticated Supabase user.
  User? get currentUser => _client.auth.currentUser;

  /// Get the current Supabase session.
  Session? get currentSession => _client.auth.currentSession;

  /// Stream of authentication state changes.
  Stream<AuthState> get authStateChanges => _client.auth.onAuthStateChange;

  /// Sign up a user with email and password.
  Future<AuthResponse> signUp({
    required String email,
    required String password,
  }) async {
    return await _client.auth.signUp(
      email: email,
      password: password,
    );
  }

  /// Sign in a user with email and password.
  Future<AuthResponse> signIn({
    required String email,
    required String password,
  }) async {
    return await _client.auth.signInWithPassword(
      email: email,
      password: password,
    );
  }

  /// Sign out the current user.
  Future<void> signOut() async {
    await _client.auth.signOut();
  }
}
