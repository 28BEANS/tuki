import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:supabase_flutter/supabase_flutter.dart' as supabase;
import '../models/user_profile.dart';
import '../services/backend_auth_service.dart';
import '../services/supabase_service.dart';

/// Controller to manage user authentication state, coordinating between Supabase and the backend.
class AuthController with ChangeNotifier {
  final SupabaseService _supabaseService;
  final BackendAuthService _backendAuthService;

  bool _isLoading = false;
  String? _errorMessage;
  UserProfile? _currentUserProfile;
  StreamSubscription<supabase.AuthState>? _authSubscription;
  Future<void>? _activeLoadFuture;

  AuthController(
    this._supabaseService,
    this._backendAuthService,
  ) {
    _initialize();
  }

  bool get isLoading => _isLoading;
  String? get errorMessage => _errorMessage;
  UserProfile? get currentUserProfile => _currentUserProfile;
  
  /// Check if the user is authenticated with both Supabase and synced with our backend.
  bool get isAuthenticated => _supabaseService.currentUser != null && _currentUserProfile != null;

  /// Clean up subscriptions on dispose
  @override
  void dispose() {
    _authSubscription?.cancel();
    super.dispose();
  }

  /// Initialize and listen to Supabase Auth changes.
  void _initialize() {
    // If a session is already present, try to fetch the backend profile.
    final session = _supabaseService.currentSession;
    if (session != null) {
      _loadProfile(session.accessToken);
    }

    _authSubscription = _supabaseService.authStateChanges.listen((data) async {
      final session = data.session;
      if (session != null) {
        // If we don't have the profile loaded, load it.
        if (_currentUserProfile == null) {
          await _loadProfile(session.accessToken);
        }
      } else {
        // User logged out or session expired.
        _currentUserProfile = null;
        notifyListeners();
      }
    });
  }

  /// Load user profile from the FastAPI backend.
  Future<void> _loadProfile(String token) async {
    if (_activeLoadFuture != null) {
      return _activeLoadFuture;
    }

    final future = () async {
      _setLoading(true);
      _clearError();
      try {
        final profile = await _backendAuthService.getProfile(jwtToken: token);
        _currentUserProfile = profile;
      } catch (e) {
        _errorMessage = 'Failed to load backend user profile: ${e.toString()}';
        // If we fail to load profile, we might still have a Supabase user, but backend sync is broken.
        _currentUserProfile = null;
      } finally {
        _setLoading(false);
        _activeLoadFuture = null;
      }
    }();

    _activeLoadFuture = future;
    return future;
  }

  /// Sign up a user with email and password, then sync profile to backend.
  Future<bool> signUp({
    required String email,
    required String password,
    required String firstName,
    required String lastName,
  }) async {
    _setLoading(true);
    _clearError();
    try {
      // 1. Supabase Signup
      final response = await _supabaseService.signUp(
        email: email,
        password: password,
      );

      final user = response.user;
      if (user == null) {
        throw Exception('Signup failed: Supabase user is null.');
      }

      // 2. Sync Profile with Backend
      final profile = await _backendAuthService.syncProfile(
        id: user.id,
        email: email,
        firstName: firstName.isEmpty ? null : firstName,
        lastName: lastName.isEmpty ? null : lastName,
      );

      _currentUserProfile = profile;
      return true;
    } on supabase.AuthApiException catch (e) {
      if (e.code == 'over_email_send_rate_limit') {
        _errorMessage = 'Registration limit reached. Please disable "Confirm email" in your Supabase Dashboard (Authentication -> Providers -> Email) to test registration locally without limits.';
      } else {
        _errorMessage = e.message;
      }
      return false;
    } catch (e) {
      _errorMessage = e.toString().replaceAll('Exception:', '').trim();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Sign in a user with email and password, then fetch profile from backend.
  Future<bool> signIn({
    required String email,
    required String password,
  }) async {
    _setLoading(true);
    _clearError();
    try {
      // 1. Supabase Sign In
      final response = await _supabaseService.signIn(
        email: email,
        password: password,
      );

      final session = response.session;
      if (session == null) {
        throw Exception('Login failed: Session is null.');
      }

      // 2. Load backend user profile
      await _loadProfile(session.accessToken);
      
      // If loading profile failed, try syncing/creating it as fallback
      if (_currentUserProfile == null && response.user != null) {
        final user = response.user!;
        final profile = await _backendAuthService.syncProfile(
          id: user.id,
          email: user.email ?? email,
        );
        _currentUserProfile = profile;
      }

      return _currentUserProfile != null;
    } catch (e) {
      _errorMessage = e.toString().replaceAll('Exception:', '').trim();
      return false;
    } finally {
      _setLoading(false);
    }
  }

  /// Sign out the current user from Supabase and clear local session state.
  Future<void> signOut() async {
    _setLoading(true);
    try {
      await _supabaseService.signOut();
      _currentUserProfile = null;
    } catch (e) {
      _errorMessage = e.toString();
    } finally {
      _setLoading(false);
    }
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void _clearError() {
    _errorMessage = null;
    notifyListeners();
  }
}
