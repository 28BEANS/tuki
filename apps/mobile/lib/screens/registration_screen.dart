import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../controllers/auth_controller.dart';
import '../core/theme.dart';

class RegistrationScreen extends StatefulWidget {
  const RegistrationScreen({super.key});

  @override
  State<RegistrationScreen> createState() => _RegistrationScreenState();
}

class _RegistrationScreenState extends State<RegistrationScreen> {
  final _formKey = GlobalKey<FormState>();
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;

  @override
  void dispose() {
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _handleSignUp() async {
    if (_formKey.currentState!.validate()) {
      final authController = Provider.of<AuthController>(context, listen: false);
      final email = _emailController.text.trim();
      final password = _passwordController.text;
      final firstName = _firstNameController.text.trim();
      final lastName = _lastNameController.text.trim();

      final success = await authController.signUp(
        email: email,
        password: password,
        firstName: firstName,
        lastName: lastName,
      );

      if (mounted) {
        if (success) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Account created successfully!'),
              backgroundColor: Colors.green,
            ),
          );
          // Pop back to login screen, or main.dart will handle state change
          Navigator.of(context).pop();
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(authController.errorMessage ?? 'Registration failed'),
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
          );
        }
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenHeight = MediaQuery.of(context).size.height;
    final authController = Provider.of<AuthController>(context);

    return Scaffold(
      body: Stack(
        children: [
          // Yellow Doodle Header Background
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            height: screenHeight * 0.30, // Slightly smaller header to fit more fields without scrolling too much
            child: Container(
              color: TukiTheme.secondaryYellow,
              child: Stack(
                children: [
                  Positioned.fill(
                    child: Image.asset(
                      'lib/assets/doodle_pattern.png',
                      fit: BoxFit.cover,
                      errorBuilder: (context, error, stackTrace) {
                        return Container(color: TukiTheme.secondaryYellow);
                      },
                    ),
                  ),
                  Center(
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Image.asset(
                        'lib/assets/tuki_logo_nobg.png',
                        height: 65,
                        errorBuilder: (context, error, stackTrace) {
                          return Text(
                            'tuki',
                            style: GoogleFonts.outfit(
                              color: TukiTheme.primaryOrange,
                              fontSize: 38,
                              fontWeight: FontWeight.bold,
                              letterSpacing: 2,
                            ),
                          );
                        },
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Scrollable White Form Card Overlapping the Header
          Positioned.fill(
            child: SafeArea(
              top: false,
              bottom: false,
              child: SingleChildScrollView(
                physics: const ClampingScrollPhysics(),
                child: Column(
                  children: [
                    SizedBox(height: screenHeight * 0.25), // Control the overlap height
                    Container(
                      width: double.infinity,
                      constraints: BoxConstraints(
                        minHeight: screenHeight * 0.75,
                      ),
                      decoration: const BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.vertical(
                          top: Radius.circular(40),
                        ),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black12,
                            blurRadius: 10,
                            offset: Offset(0, -5),
                          )
                        ],
                      ),
                      padding: const EdgeInsets.fromLTRB(28, 36, 28, 24),
                      child: Form(
                        key: _formKey,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Create Account',
                              style: Theme.of(context).textTheme.displayLarge?.copyWith(
                                fontSize: 28,
                                fontWeight: FontWeight.bold,
                                color: TukiTheme.darkText,
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              'Sign up to start your journey.',
                              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                color: TukiTheme.lightText,
                                fontSize: 15,
                              ),
                            ),
                            const SizedBox(height: 24),
                            
                            // First Name & Last Name side-by-side
                            Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'First Name',
                                        style: GoogleFonts.outfit(
                                          fontWeight: FontWeight.w600,
                                          color: TukiTheme.darkText,
                                          fontSize: 14,
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      TextFormField(
                                        controller: _firstNameController,
                                        keyboardType: TextInputType.name,
                                        style: GoogleFonts.outfit(color: TukiTheme.darkText, fontSize: 15),
                                        decoration: const InputDecoration(
                                          prefixIcon: Icon(Icons.person_outline, size: 22),
                                          hintText: 'John',
                                        ),
                                        validator: (value) {
                                          if (value == null || value.trim().isEmpty) {
                                            return 'Required';
                                          }
                                          return null;
                                        },
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: 16),
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        'Last Name',
                                        style: GoogleFonts.outfit(
                                          fontWeight: FontWeight.w600,
                                          color: TukiTheme.darkText,
                                          fontSize: 14,
                                        ),
                                      ),
                                      const SizedBox(height: 8),
                                      TextFormField(
                                        controller: _lastNameController,
                                        keyboardType: TextInputType.name,
                                        style: GoogleFonts.outfit(color: TukiTheme.darkText, fontSize: 15),
                                        decoration: const InputDecoration(
                                          prefixIcon: Icon(Icons.person_outline, size: 22),
                                          hintText: 'Doe',
                                        ),
                                        validator: (value) {
                                          if (value == null || value.trim().isEmpty) {
                                            return 'Required';
                                          }
                                          return null;
                                        },
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            
                            // Email label & input
                            Text(
                              'Email Address',
                              style: GoogleFonts.outfit(
                                fontWeight: FontWeight.w600,
                                color: TukiTheme.darkText,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextFormField(
                              controller: _emailController,
                              keyboardType: TextInputType.emailAddress,
                              style: GoogleFonts.outfit(color: TukiTheme.darkText, fontSize: 15),
                              decoration: const InputDecoration(
                                prefixIcon: Icon(Icons.email_outlined, size: 22),
                                hintText: 'name@example.com',
                              ),
                              validator: (value) {
                                if (value == null || value.trim().isEmpty) {
                                  return 'Please enter your email';
                                }
                                if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(value.trim())) {
                                  return 'Please enter a valid email';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            
                            // Password label & input
                            Text(
                              'Password',
                              style: GoogleFonts.outfit(
                                fontWeight: FontWeight.w600,
                                color: TukiTheme.darkText,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextFormField(
                              controller: _passwordController,
                              obscureText: _obscurePassword,
                              style: GoogleFonts.outfit(color: TukiTheme.darkText, fontSize: 15),
                              decoration: InputDecoration(
                                prefixIcon: const Icon(Icons.lock_outline, size: 22),
                                hintText: '••••••••',
                                suffixIcon: IconButton(
                                  icon: Icon(
                                    _obscurePassword 
                                        ? Icons.visibility_off_outlined 
                                        : Icons.visibility_outlined,
                                    size: 22,
                                  ),
                                  onPressed: () {
                                    setState(() {
                                      _obscurePassword = !_obscurePassword;
                                    });
                                  },
                                ),
                              ),
                              validator: (value) {
                                if (value == null || value.isEmpty) {
                                  return 'Please enter a password';
                                }
                                if (value.length < 6) {
                                  return 'Password must be at least 6 characters';
                                }
                                return null;
                              },
                            ),
                            const SizedBox(height: 16),
                            
                            // Confirm Password label & input
                            Text(
                              'Confirm Password',
                              style: GoogleFonts.outfit(
                                fontWeight: FontWeight.w600,
                                color: TukiTheme.darkText,
                                fontSize: 14,
                              ),
                            ),
                            const SizedBox(height: 8),
                            TextFormField(
                              controller: _confirmPasswordController,
                              obscureText: _obscureConfirmPassword,
                              style: GoogleFonts.outfit(color: TukiTheme.darkText, fontSize: 15),
                              decoration: InputDecoration(
                                prefixIcon: const Icon(Icons.lock_outline, size: 22),
                                hintText: '••••••••',
                                suffixIcon: IconButton(
                                  icon: Icon(
                                    _obscureConfirmPassword 
                                        ? Icons.visibility_off_outlined 
                                        : Icons.visibility_outlined,
                                    size: 22,
                                  ),
                                  onPressed: () {
                                    setState(() {
                                      _obscureConfirmPassword = !_obscureConfirmPassword;
                                    });
                                  },
                                ),
                              ),
                              validator: (value) {
                                if (value == null || value.isEmpty) {
                                  return 'Please confirm your password';
                                }
                                if (value != _passwordController.text) {
                                  return 'Passwords do not match';
                                }
                                return null;
                              },
                            ),
                            
                            // Sign Up Button
                            const SizedBox(height: 28),
                            authController.isLoading
                                ? const Center(
                                    child: Padding(
                                      padding: EdgeInsets.all(8.0),
                                      child: CircularProgressIndicator(
                                        color: TukiTheme.primaryOrange,
                                      ),
                                    ),
                                  )
                                : ElevatedButton(
                                    onPressed: _handleSignUp,
                                    child: const Text('Sign Up'),
                                  ),
                            
                            // Navigation to Login Page
                            const SizedBox(height: 24),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Text(
                                  "Already have an account? ",
                                  style: GoogleFonts.outfit(
                                    color: TukiTheme.lightText,
                                    fontSize: 14,
                                  ),
                                ),
                                GestureDetector(
                                  onTap: () {
                                    Navigator.of(context).pop();
                                  },
                                  child: Text(
                                    'Sign In',
                                    style: GoogleFonts.outfit(
                                      color: TukiTheme.primaryOrange,
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
