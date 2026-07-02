import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:supabase_flutter/supabase_flutter.dart';
import 'controllers/auth_controller.dart';
import 'core/config.dart';
import 'core/theme.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'services/backend_auth_service.dart';
import 'services/supabase_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Supabase client
  await Supabase.initialize(
    url: AppConfig.supabaseUrl,
    publishableKey: AppConfig.supabaseAnonKey,
  );

  runApp(
    MultiProvider(
      providers: [
        Provider<SupabaseService>(
          create: (_) => SupabaseService(),
        ),
        Provider<BackendAuthService>(
          create: (_) => BackendAuthService(),
        ),
        ChangeNotifierProvider<AuthController>(
          create: (context) => AuthController(
            context.read<SupabaseService>(),
            context.read<BackendAuthService>(),
          ),
        ),
      ],
      child: const MainApp(),
    ),
  );
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Tuki',
      theme: TukiTheme.lightTheme,
      debugShowCheckedModeBanner: false,
      home: const AuthGate(),
    );
  }
}

/// A widget that listens to the [AuthController] and routes the user to
/// either the [HomeScreen] or the [LoginScreen] based on their auth status.
class AuthGate extends StatelessWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context) {
    final authController = Provider.of<AuthController>(context);

    // Show loading indicator when the app is initializing auth state
    if (authController.isLoading && authController.currentUserProfile == null) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(
            color: TukiTheme.primaryOrange,
          ),
        ),
      );
    }

    if (authController.isAuthenticated) {
      return const HomeScreen();
    } else {
      return const LoginScreen();
    }
  }
}
