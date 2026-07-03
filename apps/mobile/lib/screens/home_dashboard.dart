import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:provider/provider.dart';
import '../controllers/auth_controller.dart';
import '../core/theme.dart';
import '../models/landmark.dart';
import '../services/landmark_service.dart';

/// Represents a single recent trip entry (client-side mock for now).
class _RecentTrip {
  final String from;
  final String to;
  final String transport;
  final int durationMinutes;
  final Color iconBg;
  final IconData icon;
  final Color iconColor;

  const _RecentTrip({
    required this.from,
    required this.to,
    required this.transport,
    required this.durationMinutes,
    required this.iconBg,
    required this.icon,
    required this.iconColor,
  });
}

class HomeDashboard extends StatefulWidget {
  const HomeDashboard({super.key});

  @override
  State<HomeDashboard> createState() => _HomeDashboardState();
}

class _HomeDashboardState extends State<HomeDashboard> {
  final TextEditingController _searchController = TextEditingController();
  final LandmarkService _landmarkService = LandmarkService();
  List<Landmark> _searchResults = [];
  bool _isSearching = false;
  Timer? _debounce;

  // Mock recent trips — in a real app, fetch from backend history
  final List<_RecentTrip> _recentTrips = const [
    _RecentTrip(
      from: 'HAU',
      to: 'SM Clark',
      transport: 'Jeepney',
      durationMinutes: 15,
      iconBg: Color(0xFFDFF0E8),
      icon: Icons.directions_bus_rounded,
      iconColor: Color(0xFF34A853),
    ),
    _RecentTrip(
      from: 'Marquee Mall',
      to: 'City Hall',
      transport: 'Tricycle',
      durationMinutes: 10,
      iconBg: Color(0xFFFDE8E0),
      icon: Icons.electric_rickshaw_rounded,
      iconColor: Color(0xFFF05A28),
    ),
    _RecentTrip(
      from: 'SM Clark',
      to: 'Nepo Mall',
      transport: 'Jeepney',
      durationMinutes: 20,
      iconBg: Color(0xFFDFF0E8),
      icon: Icons.directions_bus_rounded,
      iconColor: Color(0xFF34A853),
    ),
  ];

  @override
  void dispose() {
    _searchController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  void _onSearchChanged(String query) {
    _debounce?.cancel();
    if (query.trim().isEmpty) {
      setState(() {
        _searchResults = [];
        _isSearching = false;
      });
      return;
    }

    _debounce = Timer(const Duration(milliseconds: 400), () async {
      setState(() => _isSearching = true);
      try {
        final results = await _landmarkService.searchLandmarks(query: query);
        if (mounted) {
          setState(() {
            _searchResults = results;
            _isSearching = false;
          });
        }
      } catch (_) {
        if (mounted) setState(() => _isSearching = false);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final authController = Provider.of<AuthController>(context);
    final user = authController.currentUserProfile;
    final firstName = user?.firstName ?? 'Commuter';

    return Scaffold(
      backgroundColor: const Color(0xFFF5F5F5),
      body: Stack(
        children: [
          CustomScrollView(
            slivers: [
              // ── Hero Header ──
              SliverToBoxAdapter(
                child: _HeroHeader(
                  firstName: firstName,
                  searchController: _searchController,
                  isSearching: _isSearching,
                  searchResults: _searchResults,
                  onSearchChanged: _onSearchChanged,
                  onProfileTap: () {
                    // TODO: navigate to profile
                  },
                  onMenuTap: () {
                    // TODO: open drawer
                  },
                ),
              ),

              // ── Quick Actions ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 24, 24, 0),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      _QuickActionButton(
                        icon: Icons.bookmark_outline_rounded,
                        label: 'Saved',
                        onTap: () {
                          // TODO: navigate to saved
                        },
                      ),
                      const SizedBox(width: 16),
                      _QuickActionButton(
                        icon: Icons.history_rounded,
                        label: 'History',
                        onTap: () {
                          // TODO: navigate to history
                        },
                      ),
                    ],
                  ),
                ),
              ),

              // ── Recent Trips Section ──
              SliverToBoxAdapter(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(24, 28, 24, 12),
                  child: Text(
                    'Recent Trips',
                    style: GoogleFonts.outfit(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: TukiTheme.darkText,
                    ),
                  ),
                ),
              ),

              // ── Recent Trips Cards ──
              SliverToBoxAdapter(
                child: SizedBox(
                  height: 110,
                  child: ListView.separated(
                    padding: const EdgeInsets.symmetric(horizontal: 24),
                    scrollDirection: Axis.horizontal,
                    separatorBuilder: (ctx, idx) => const SizedBox(width: 12),
                    itemCount: _recentTrips.length,
                    itemBuilder: (context, i) =>
                        _RecentTripCard(trip: _recentTrips[i]),
                  ),
                ),
              ),

              // Bottom padding
              const SliverToBoxAdapter(child: SizedBox(height: 120)),
            ],
          ),

          // ── Search Results Overlay ──
          if (_searchResults.isNotEmpty || _isSearching)
            _SearchOverlay(
              isSearching: _isSearching,
              results: _searchResults,
              onClear: () {
                setState(() {
                  _searchResults = [];
                  _searchController.clear();
                });
              },
            ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Hero Header Widget
// ─────────────────────────────────────────────────────────────────────────────

class _HeroHeader extends StatelessWidget {
  final String firstName;
  final TextEditingController searchController;
  final bool isSearching;
  final List<Landmark> searchResults;
  final ValueChanged<String> onSearchChanged;
  final VoidCallback onProfileTap;
  final VoidCallback onMenuTap;

  const _HeroHeader({
    required this.firstName,
    required this.searchController,
    required this.isSearching,
    required this.searchResults,
    required this.onSearchChanged,
    required this.onProfileTap,
    required this.onMenuTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: const BoxDecoration(
        color: Color(0xFFFFC629),
        borderRadius: BorderRadius.only(
          bottomLeft: Radius.circular(28),
          bottomRight: Radius.circular(28),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top bar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    onPressed: onMenuTap,
                    icon: const Icon(Icons.menu_rounded,
                        color: Color(0xFF7A4900), size: 28),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                  Text(
                    'Tuki',
                    style: GoogleFonts.outfit(
                      fontSize: 22,
                      fontWeight: FontWeight.w800,
                      color: const Color(0xFF9B2600),
                    ),
                  ),
                  GestureDetector(
                    onTap: onProfileTap,
                    child: Container(
                      width: 40,
                      height: 40,
                      decoration: BoxDecoration(
                        color: Colors.white.withValues(alpha: 0.85),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.person_rounded,
                          color: Color(0xFF7A4900), size: 22),
                    ),
                  ),
                ],
              ),

              const SizedBox(height: 20),

              // Greeting
              Text(
                'Magandang Araw,\n$firstName!',
                style: GoogleFonts.outfit(
                  fontSize: 30,
                  fontWeight: FontWeight.w800,
                  color: const Color(0xFF5A3200),
                  height: 1.15,
                ),
              ),
              const SizedBox(height: 6),
              Text(
                'Where are we going today?',
                style: GoogleFonts.outfit(
                  fontSize: 15,
                  fontWeight: FontWeight.w400,
                  color: const Color(0xFF7A5200),
                ),
              ),

              const SizedBox(height: 20),

              // Search Bar
              Container(
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(30),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.08),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: Row(
                  children: [
                    const SizedBox(width: 16),
                    Icon(Icons.search_rounded,
                        color: TukiTheme.lightText, size: 22),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: searchController,
                        onChanged: onSearchChanged,
                        style: GoogleFonts.outfit(
                          fontSize: 15,
                          color: TukiTheme.darkText,
                        ),
                        decoration: InputDecoration(
                          hintText: 'Search landmarks, malls...',
                          hintStyle: GoogleFonts.outfit(
                            fontSize: 14,
                            color: TukiTheme.lightText,
                          ),
                          border: InputBorder.none,
                          enabledBorder: InputBorder.none,
                          focusedBorder: InputBorder.none,
                          filled: false,
                          contentPadding:
                              const EdgeInsets.symmetric(vertical: 14),
                        ),
                      ),
                    ),
                    Container(
                      margin: const EdgeInsets.all(6),
                      width: 42,
                      height: 42,
                      decoration: BoxDecoration(
                        color: const Color(0xFF9B2600),
                        borderRadius: BorderRadius.circular(24),
                      ),
                      child: const Icon(Icons.tune_rounded,
                          color: Colors.white, size: 20),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Explore Nearby Card
              _ExploreNearbyCard(),
            ],
          ),
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Explore Nearby Card
// ─────────────────────────────────────────────────────────────────────────────

class _ExploreNearbyCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.06),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Explore Nearby',
                  style: GoogleFonts.outfit(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: TukiTheme.darkText,
                  ),
                ),
                Icon(Icons.map_outlined,
                    color: const Color(0xFF9B2600), size: 22),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              height: 100,
              width: double.infinity,
              decoration: BoxDecoration(
                color: const Color(0xFFF0F0F0),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Center(
                child: Text(
                  'Map Preview: Nearby Transit Stops',
                  style: GoogleFonts.outfit(
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                    color: TukiTheme.lightText,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Quick Action Button
// ─────────────────────────────────────────────────────────────────────────────

class _QuickActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Column(
        children: [
          Container(
            width: 90,
            height: 80,
            decoration: BoxDecoration(
              color: const Color(0xFFEEEEEE),
              borderRadius: BorderRadius.circular(18),
            ),
            child: Icon(
              icon,
              color: const Color(0xFF9B2600),
              size: 30,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            label,
            style: GoogleFonts.outfit(
              fontSize: 13,
              fontWeight: FontWeight.w500,
              color: TukiTheme.darkText,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Recent Trip Card
// ─────────────────────────────────────────────────────────────────────────────

class _RecentTripCard extends StatelessWidget {
  final _RecentTrip trip;

  const _RecentTripCard({required this.trip});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 220,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: trip.iconBg,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(trip.icon, color: trip.iconColor, size: 24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${trip.from} to ${trip.to}',
                  style: GoogleFonts.outfit(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: TukiTheme.darkText,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(
                  '${trip.transport} • ${trip.durationMinutes} mins',
                  style: GoogleFonts.outfit(
                    fontSize: 12,
                    color: TukiTheme.lightText,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Search Results Overlay
// ─────────────────────────────────────────────────────────────────────────────

class _SearchOverlay extends StatelessWidget {
  final bool isSearching;
  final List<Landmark> results;
  final VoidCallback onClear;

  const _SearchOverlay({
    required this.isSearching,
    required this.results,
    required this.onClear,
  });

  @override
  Widget build(BuildContext context) {
    final safeTop = MediaQuery.of(context).padding.top;

    return Positioned(
      top: safeTop + 170,
      left: 20,
      right: 20,
      child: Material(
        elevation: 8,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          constraints: const BoxConstraints(maxHeight: 260),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
          ),
          child: isSearching
              ? const Padding(
                  padding: EdgeInsets.all(20),
                  child: Center(
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: TukiTheme.primaryOrange,
                    ),
                  ),
                )
              : ListView.separated(
                  shrinkWrap: true,
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  separatorBuilder: (ctx, idx) => const Divider(height: 1),
                  itemCount: results.length,
                  itemBuilder: (context, i) {
                    final item = results[i];
                    return ListTile(
                      leading: const Icon(Icons.location_on_rounded,
                          color: TukiTheme.primaryOrange),
                      title: Text(item.name,
                          style: GoogleFonts.outfit(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: TukiTheme.darkText)),
                      subtitle: Text(
                        item.barangayName ?? item.category,
                        style: GoogleFonts.outfit(
                            fontSize: 12, color: TukiTheme.lightText),
                      ),
                      trailing: const Icon(Icons.north_west_rounded,
                          size: 16, color: TukiTheme.lightText),
                      onTap: onClear,
                    );
                  },
                ),
        ),
      ),
    );
  }
}
