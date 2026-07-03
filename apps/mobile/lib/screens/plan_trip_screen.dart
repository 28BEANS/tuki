import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/theme.dart';

/// Placeholder screen for Plan Trip.
class PlanTripScreen extends StatelessWidget {
  const PlanTripScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        centerTitle: true,
        title: Text(
          'Plan Trip',
          style: GoogleFonts.outfit(
            fontSize: 18,
            fontWeight: FontWeight.w700,
            color: TukiTheme.darkText,
          ),
        ),
        iconTheme: const IconThemeData(color: TukiTheme.darkText),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                color: const Color(0xFFFFF0E8),
                borderRadius: BorderRadius.circular(24),
              ),
              child: const Icon(
                Icons.map_rounded,
                size: 40,
                color: TukiTheme.primaryOrange,
              ),
            ),
            const SizedBox(height: 20),
            Text(
              'Plan Trip',
              style: GoogleFonts.outfit(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: TukiTheme.darkText,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              'Route planning coming soon!',
              style: GoogleFonts.outfit(
                fontSize: 14,
                color: TukiTheme.lightText,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
