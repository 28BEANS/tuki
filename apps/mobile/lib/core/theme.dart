import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

/// Centralized theme parameters for the Tuki application.
class TukiTheme {
  // Brand Colors
  static const Color primaryOrange = Color(0xFFF05A28);
  static const Color secondaryYellow = Color(0xFFF2C94C); // Doodle card header yellow
  static const Color darkText = Color(0xFF2D2D2D);
  static const Color lightText = Color(0xFF7F7F7F);
  static const Color fieldBackground = Color(0xFFF6F6F6);
  static const Color dividerColor = Color(0xFFE0E0E0);
  
  /// Returns the customized ThemeData for the application.
  static ThemeData get lightTheme {
    final baseTheme = ThemeData.light();
    
    return baseTheme.copyWith(
      colorScheme: baseTheme.colorScheme.copyWith(
        primary: primaryOrange,
        secondary: secondaryYellow,
        surface: Colors.white,
        error: const Color(0xFFEB5757),
      ),
      scaffoldBackgroundColor: Colors.white,
      
      // Text Theme matching Outfit/Poppins fonts
      textTheme: GoogleFonts.outfitTextTheme(baseTheme.textTheme).copyWith(
        displayLarge: GoogleFonts.outfit(
          color: darkText,
          fontSize: 32,
          fontWeight: FontWeight.bold,
        ),
        titleLarge: GoogleFonts.outfit(
          color: darkText,
          fontSize: 24,
          fontWeight: FontWeight.w600,
        ),
        bodyLarge: GoogleFonts.outfit(
          color: darkText,
          fontSize: 16,
          fontWeight: FontWeight.normal,
        ),
        bodyMedium: GoogleFonts.outfit(
          color: lightText,
          fontSize: 14,
          fontWeight: FontWeight.normal,
        ),
      ),
      
      // Text Field InputDecoration Theme
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: fieldBackground,
        contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
        prefixIconColor: lightText,
        suffixIconColor: lightText,
        hintStyle: GoogleFonts.outfit(
          color: lightText.withValues(alpha: 0.6),
          fontSize: 14,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: BorderSide.none,
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: const BorderSide(color: primaryOrange, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: const BorderSide(color: Color(0xFFEB5757), width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(30),
          borderSide: const BorderSide(color: Color(0xFFEB5757), width: 1.5),
        ),
      ),
      
      // Custom Elevated Button Theme
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          backgroundColor: primaryOrange,
          foregroundColor: Colors.white,
          elevation: 2,
          shadowColor: primaryOrange.withValues(alpha: 0.3),
          minimumSize: const Size(double.infinity, 54),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(30),
          ),
          textStyle: GoogleFonts.outfit(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
      ),
    );
  }
}
