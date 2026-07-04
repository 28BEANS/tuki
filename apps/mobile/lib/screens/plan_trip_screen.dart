import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/theme.dart';
import '../models/landmark.dart';
import '../models/route_result.dart';
import '../services/landmark_service.dart';
import '../services/route_service.dart';

// ── Hard-coded origin fallback coords (HAU, Angeles City) ───────────────────
const double _kDefaultLat = 15.1450;
const double _kDefaultLon = 120.5887;

/// The three phases of the Plan Trip user flow.
enum _TripPhase { input, preview, details }

class PlanTripScreen extends StatefulWidget {
  const PlanTripScreen({super.key});

  @override
  State<PlanTripScreen> createState() => _PlanTripScreenState();
}

class _PlanTripScreenState extends State<PlanTripScreen> {
  final _landmarkService = LandmarkService();
  final _routeService = RouteService();

  _TripPhase _phase = _TripPhase.input;

  // ── Input state ─────────────────────────────────────────────────────────
  final _originController = TextEditingController(text: 'Current Location');
  final _destController = TextEditingController();

  Landmark? _selectedDest;
  List<Landmark> _suggestions = [];
  bool _isSearching = false;
  Timer? _debounce;

  // ── Route result state ──────────────────────────────────────────────────
  RouteResult? _routeResult;
  bool _isCalculating = false;
  String? _routeError;

  // ── Origin coords (would come from GPS in production) ───────────────────
  final double _originLat = _kDefaultLat;
  final double _originLon = _kDefaultLon;

  @override
  void dispose() {
    _originController.dispose();
    _destController.dispose();
    _debounce?.cancel();
    super.dispose();
  }

  // ── Search ───────────────────────────────────────────────────────────────
  void _onDestChanged(String query) {
    _debounce?.cancel();
    if (query.trim().isEmpty) {
      setState(() {
        _suggestions = [];
        _isSearching = false;
        _selectedDest = null;
      });
      return;
    }
    setState(() => _isSearching = true);
    _debounce = Timer(const Duration(milliseconds: 400), () async {
      try {
        final results =
            await _landmarkService.searchLandmarks(query: query, pageSize: 6);
        if (mounted) setState(() => _suggestions = results);
      } catch (_) {
        // keep old suggestions
      } finally {
        if (mounted) setState(() => _isSearching = false);
      }
    });
  }

  void _selectDestination(Landmark landmark) {
    setState(() {
      _selectedDest = landmark;
      _destController.text = landmark.name;
      _suggestions = [];
    });
  }

  // ── Route calculation ────────────────────────────────────────────────────
  Future<void> _findRoute() async {
    if (_selectedDest == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a destination first.')),
      );
      return;
    }

    setState(() {
      _isCalculating = true;
      _routeError = null;
    });

    try {
      final result = await _routeService.calculateRoute(
        originLat: _originLat,
        originLon: _originLon,
        destinationLat: _selectedDest!.latitude,
        destinationLon: _selectedDest!.longitude,
      );
      if (mounted) {
        setState(() {
          _routeResult = result;
          _phase = _TripPhase.preview;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _routeError = e.toString().replaceAll('Exception: ', ''));
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(_routeError ?? 'Could not calculate route.')),
        );
      }
    } finally {
      if (mounted) setState(() => _isCalculating = false);
    }
  }

  // ── Navigation ────────────────────────────────────────────────────────────
  void _goBack() {
    setState(() {
      if (_phase == _TripPhase.details) {
        _phase = _TripPhase.preview;
      } else {
        _phase = _TripPhase.input;
        _routeResult = null;
      }
    });
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return PopScope(
      canPop: _phase == _TripPhase.input,
      onPopInvokedWithResult: (didPop, _) {
        if (!didPop) _goBack();
      },
      child: Scaffold(
        backgroundColor: const Color(0xFFF5F5F5),
        body: AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          child: _buildPhase(),
        ),
      ),
    );
  }

  Widget _buildPhase() {
    switch (_phase) {
      case _TripPhase.input:
        return _InputPhase(
          key: const ValueKey('input'),
          originController: _originController,
          destController: _destController,
          suggestions: _suggestions,
          isSearching: _isSearching,
          isCalculating: _isCalculating,
          onDestChanged: _onDestChanged,
          onSelectDest: _selectDestination,
          onFindRoute: _findRoute,
          selectedDest: _selectedDest,
        );
      case _TripPhase.preview:
        return _PreviewPhase(
          key: const ValueKey('preview'),
          result: _routeResult!,
          originName: _originController.text,
          destName: _selectedDest?.name ?? _destController.text,
          onBack: _goBack,
          onViewDetails: () => setState(() => _phase = _TripPhase.details),
        );
      case _TripPhase.details:
        return _DetailsPhase(
          key: const ValueKey('details'),
          result: _routeResult!,
          destName: _selectedDest?.name ?? _destController.text,
          onClose: _goBack,
        );
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase 1 — Input
// ─────────────────────────────────────────────────────────────────────────────

class _InputPhase extends StatelessWidget {
  final TextEditingController originController;
  final TextEditingController destController;
  final List<Landmark> suggestions;
  final bool isSearching;
  final bool isCalculating;
  final ValueChanged<String> onDestChanged;
  final ValueChanged<Landmark> onSelectDest;
  final VoidCallback onFindRoute;
  final Landmark? selectedDest;

  const _InputPhase({
    super.key,
    required this.originController,
    required this.destController,
    required this.suggestions,
    required this.isSearching,
    required this.isCalculating,
    required this.onDestChanged,
    required this.onSelectDest,
    required this.onFindRoute,
    required this.selectedDest,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Stack(
        children: [
          // ── Top bar ────────────────────────────────────────────────────────
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: Container(
              color: Colors.white,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  IconButton(
                    icon: const Icon(Icons.menu_rounded,
                        color: Color(0xFF7A4900)),
                    onPressed: () {},
                  ),
                  const SizedBox(width: 40),
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      color: const Color(0xFFF0F0F0),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(Icons.person_rounded,
                        color: Color(0xFF7A4900), size: 20),
                  ),
                ],
              ),
            ),
          ),

          // ── Content ────────────────────────────────────────────────────────
          Positioned(
            top: 64,
            left: 0,
            right: 0,
            bottom: 0,
            child: Column(
              children: [
                // Location inputs card
                Container(
                  margin: const EdgeInsets.all(16),
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.06),
                        blurRadius: 12,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  child: Column(
                    children: [
                      // Origin field
                      _LocationField(
                        controller: originController,
                        icon: Icons.my_location_rounded,
                        iconColor: const Color(0xFFFFC629),
                        readOnly: true,
                        hintText: 'Current Location',
                        onChanged: null,
                      ),
                      const SizedBox(height: 8),
                      const Divider(height: 1),
                      const SizedBox(height: 8),
                      // Destination field
                      _LocationField(
                        controller: destController,
                        icon: Icons.location_on_rounded,
                        iconColor: const Color(0xFFFFC629),
                        readOnly: false,
                        hintText: 'Where to?',
                        onChanged: onDestChanged,
                        trailing: isSearching
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: TukiTheme.primaryOrange,
                                ),
                              )
                            : Icon(Icons.mic_rounded,
                                color: const Color(0xFFFFC629), size: 22),
                      ),
                    ],
                  ),
                ),

                // ── Map placeholder ──────────────────────────────────────────
                Expanded(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      color: const Color(0xFFEEEEEE),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.location_on_rounded,
                              color: const Color(0xFFFFC629), size: 48),
                          const SizedBox(height: 8),
                          Text(
                            'Map View',
                            style: GoogleFonts.outfit(
                              fontSize: 13,
                              fontStyle: FontStyle.italic,
                              color: TukiTheme.lightText,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                const SizedBox(height: 16),
              ],
            ),
          ),

          // ── Suggestions overlay ───────────────────────────────────────────
          if (suggestions.isNotEmpty)
            Positioned(
              top: 184,
              left: 16,
              right: 16,
              child: Material(
                elevation: 8,
                borderRadius: BorderRadius.circular(16),
                child: Container(
                  constraints: const BoxConstraints(maxHeight: 240),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: ListView.separated(
                    shrinkWrap: true,
                    padding: const EdgeInsets.symmetric(vertical: 6),
                    separatorBuilder: (ctx, idx) =>
                        const Divider(height: 1, indent: 56),
                    itemCount: suggestions.length,
                    itemBuilder: (context, i) {
                      final lm = suggestions[i];
                      return ListTile(
                        leading: const Icon(Icons.location_on_rounded,
                            color: TukiTheme.primaryOrange),
                        title: Text(lm.name,
                            style: GoogleFonts.outfit(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: TukiTheme.darkText)),
                        subtitle: lm.barangayName != null
                            ? Text(lm.barangayName!,
                                style: GoogleFonts.outfit(
                                    fontSize: 12,
                                    color: TukiTheme.lightText))
                            : null,
                        onTap: () => onSelectDest(lm),
                      );
                    },
                  ),
                ),
              ),
            ),

          // ── Find Route button ─────────────────────────────────────────────
          Positioned(
            bottom: 24,
            left: 24,
            right: 24,
            child: ElevatedButton.icon(
              onPressed: isCalculating ? null : onFindRoute,
              style: ElevatedButton.styleFrom(
                backgroundColor: TukiTheme.primaryOrange,
                foregroundColor: Colors.white,
                minimumSize: const Size(double.infinity, 54),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(30),
                ),
                elevation: 2,
                shadowColor: TukiTheme.primaryOrange.withValues(alpha: 0.3),
              ),
              icon: isCalculating
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                          strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.directions_rounded),
              label: Text(
                isCalculating ? 'Calculating...' : 'Find Route',
                style: GoogleFonts.outfit(
                    fontSize: 16, fontWeight: FontWeight.w700),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Phase 2 — Route Preview
// ─────────────────────────────────────────────────────────────────────────────

class _PreviewPhase extends StatelessWidget {
  final RouteResult result;
  final String originName;
  final String destName;
  final VoidCallback onBack;
  final VoidCallback onViewDetails;

  const _PreviewPhase({
    super.key,
    required this.result,
    required this.originName,
    required this.destName,
    required this.onBack,
    required this.onViewDetails,
  });

  @override
  Widget build(BuildContext context) {
    final modes = result.segments
        .map((s) => s.mode)
        .where((m) => m != 'walk' || result.segments.length == 1)
        .toSet()
        .toList();

    return SafeArea(
      child: Column(
        children: [
          // ── App bar ────────────────────────────────────────────────────────
          Container(
            color: Colors.white,
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            child: Row(
              children: [
                IconButton(
                  icon: const Icon(Icons.arrow_back_rounded,
                      color: Color(0xFF7A4900)),
                  onPressed: onBack,
                ),
                Text(
                  'Tuki',
                  style: GoogleFonts.outfit(
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    color: const Color(0xFF9B2600),
                  ),
                ),
                const Spacer(),
                Container(
                  width: 38,
                  height: 38,
                  decoration: const BoxDecoration(
                    color: Color(0xFFF0F0F0),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.person_rounded,
                      color: Color(0xFF7A4900), size: 20),
                ),
                const SizedBox(width: 8),
              ],
            ),
          ),

          // ── Origin chip ───────────────────────────────────────────────────
          Container(
            width: double.infinity,
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(30),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.06),
                  blurRadius: 8,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              children: [
                const Icon(Icons.my_location_rounded,
                    color: Color(0xFF9B2600), size: 18),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    originName,
                    style: GoogleFonts.outfit(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: TukiTheme.darkText),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
          ),

          // ── Map placeholder ────────────────────────────────────────────────
          Expanded(
            child: Container(
              margin: const EdgeInsets.fromLTRB(0, 12, 0, 0),
              decoration: const BoxDecoration(
                color: Color(0xFFE8E8E8),
              ),
              child: Center(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(Icons.map_outlined,
                        color: const Color(0xFFFFC629).withValues(alpha: 0.7),
                        size: 52),
                    const SizedBox(height: 8),
                    Text(
                      'Route Map Preview',
                      style: GoogleFonts.outfit(
                        fontSize: 13,
                        fontStyle: FontStyle.italic,
                        color: TukiTheme.lightText,
                      ),
                    ),
                    Text(
                      '$originName → $destName',
                      style: GoogleFonts.outfit(
                        fontSize: 12,
                        color: TukiTheme.lightText,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
            ),
          ),

          // ── Summary card ──────────────────────────────────────────────────
          Container(
            decoration: const BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.only(
                topLeft: Radius.circular(24),
                topRight: Radius.circular(24),
              ),
            ),
            padding: const EdgeInsets.fromLTRB(24, 16, 24, 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Drag handle
                Center(
                  child: Container(
                    width: 36,
                    height: 4,
                    decoration: BoxDecoration(
                      color: const Color(0xFFE0E0E0),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 12),

                // Transport mode chips
                if (modes.isNotEmpty)
                  Wrap(
                    spacing: 8,
                    children: [
                      // Show 'Walk' chip if any walk segments
                      if (result.segments.any((s) => s.mode == 'walk'))
                        _ModeChip(
                          icon: Icons.directions_walk_rounded,
                          label: 'Walk',
                        ),
                      if (result.segments.any((s) => s.mode == 'jeep'))
                        _ModeChip(
                          icon: Icons.directions_bus_rounded,
                          label: result.segments
                                  .firstWhere((s) => s.mode == 'jeep')
                                  .routeColor ??
                              'Jeep',
                        ),
                      if (result.segments.any((s) => s.mode == 'tricycle'))
                        _ModeChip(
                          icon: Icons.electric_rickshaw_rounded,
                          label: 'Tricycle',
                        ),
                    ],
                  ),

                const SizedBox(height: 16),

                // Fare + ETA row
                Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'TOTAL FARE',
                            style: GoogleFonts.outfit(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: TukiTheme.lightText,
                              letterSpacing: 0.8,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            '₱${result.totalFare.toStringAsFixed(2)}',
                            style: GoogleFonts.outfit(
                              fontSize: 24,
                              fontWeight: FontWeight.w800,
                              color: TukiTheme.primaryOrange,
                            ),
                          ),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          'EST. TIME',
                          style: GoogleFonts.outfit(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: TukiTheme.lightText,
                            letterSpacing: 0.8,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Row(
                          children: [
                            const Icon(Icons.access_time_rounded,
                                size: 18,
                                color: TukiTheme.primaryOrange),
                            const SizedBox(width: 4),
                            Text(
                              '${result.travelTimeMin.round()} mins',
                              style: GoogleFonts.outfit(
                                fontSize: 20,
                                fontWeight: FontWeight.w800,
                                color: TukiTheme.darkText,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ],
                ),

                const SizedBox(height: 16),

                // View Route Details button
                ElevatedButton.icon(
                  onPressed: onViewDetails,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: TukiTheme.primaryOrange,
                    foregroundColor: Colors.white,
                    minimumSize: const Size(double.infinity, 52),
                    shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(30)),
                    elevation: 2,
                    shadowColor:
                        TukiTheme.primaryOrange.withValues(alpha: 0.3),
                  ),
                  icon: const Icon(Icons.keyboard_arrow_up_rounded),
                  label: Text(
                    'View Route Details',
                    style: GoogleFonts.outfit(
                        fontSize: 16, fontWeight: FontWeight.w700),
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
// Phase 3 — Route Details
// ─────────────────────────────────────────────────────────────────────────────

class _DetailsPhase extends StatelessWidget {
  final RouteResult result;
  final String destName;
  final VoidCallback onClose;

  const _DetailsPhase({
    super.key,
    required this.result,
    required this.destName,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Column(
        children: [
          // ── Map placeholder (same reserved space as preview) ───────────────
          Expanded(
            flex: 2,
            child: Container(
              color: const Color(0xFFE8E8E8),
              child: Center(
                child: Text(
                  'Route Map Preview',
                  style: GoogleFonts.outfit(
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                    color: TukiTheme.lightText,
                  ),
                ),
              ),
            ),
          ),

          // ── Details bottom sheet ──────────────────────────────────────────
          Expanded(
            flex: 3,
            child: Container(
              decoration: const BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.only(
                  topLeft: Radius.circular(24),
                  topRight: Radius.circular(24),
                ),
              ),
              child: Column(
                children: [
                  // Header
                  Padding(
                    padding: const EdgeInsets.fromLTRB(24, 16, 16, 0),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'FASTEST ROUTE',
                                style: GoogleFonts.outfit(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: TukiTheme.primaryOrange,
                                  letterSpacing: 0.8,
                                ),
                              ),
                              const SizedBox(height: 2),
                              Text(
                                'Route to $destName',
                                style: GoogleFonts.outfit(
                                  fontSize: 18,
                                  fontWeight: FontWeight.w800,
                                  color: TukiTheme.darkText,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Wrap(
                                spacing: 8,
                                children: [
                                  _SummaryChip(
                                      label:
                                          '₱${result.totalFare.round()} Total'),
                                  _SummaryChip(
                                      label:
                                          '${result.travelTimeMin.round()} mins'),
                                ],
                              ),
                            ],
                          ),
                        ),
                        IconButton(
                          icon: Container(
                            width: 34,
                            height: 34,
                            decoration: const BoxDecoration(
                              color: Color(0xFFF0F0F0),
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(Icons.close_rounded,
                                size: 18, color: TukiTheme.darkText),
                          ),
                          onPressed: onClose,
                        ),
                      ],
                    ),
                  ),

                  const Divider(height: 20),

                  // ── Step-by-step timeline ──────────────────────────────────
                  Expanded(
                    child: ListView.builder(
                      padding:
                          const EdgeInsets.fromLTRB(24, 0, 24, 24),
                      itemCount: result.instructions.length,
                      itemBuilder: (context, i) {
                        final instr = result.instructions[i];
                        final isLast =
                            i == result.instructions.length - 1;
                        return _TimelineStep(
                          instruction: instr,
                          isLast: isLast,
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Shared widgets
// ─────────────────────────────────────────────────────────────────────────────

class _LocationField extends StatelessWidget {
  final TextEditingController controller;
  final IconData icon;
  final Color iconColor;
  final bool readOnly;
  final String hintText;
  final ValueChanged<String>? onChanged;
  final Widget? trailing;

  const _LocationField({
    required this.controller,
    required this.icon,
    required this.iconColor,
    required this.readOnly,
    required this.hintText,
    required this.onChanged,
    this.trailing,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: iconColor.withValues(alpha: 0.12),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: iconColor, size: 18),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: TextField(
            controller: controller,
            readOnly: readOnly,
            onChanged: onChanged,
            style: GoogleFonts.outfit(
              fontSize: 15,
              fontWeight: FontWeight.w500,
              color: TukiTheme.darkText,
            ),
            decoration: InputDecoration(
              hintText: hintText,
              hintStyle: GoogleFonts.outfit(
                fontSize: 15,
                color: TukiTheme.lightText,
              ),
              border: InputBorder.none,
              enabledBorder: InputBorder.none,
              focusedBorder: InputBorder.none,
              filled: false,
              contentPadding: EdgeInsets.zero,
            ),
          ),
        ),
        ?trailing,
      ],
    );
  }
}

class _ModeChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _ModeChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFFF0F0F0),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: TukiTheme.darkText),
          const SizedBox(width: 4),
          Text(
            label,
            style: GoogleFonts.outfit(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: TukiTheme.darkText),
          ),
        ],
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  final String label;

  const _SummaryChip({required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        color: const Color(0xFFF0F0F0),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: GoogleFonts.outfit(
            fontSize: 13,
            fontWeight: FontWeight.w600,
            color: TukiTheme.darkText),
      ),
    );
  }
}

class _TimelineStep extends StatelessWidget {
  final NavigationInstruction instruction;
  final bool isLast;

  const _TimelineStep({required this.instruction, required this.isLast});

  @override
  Widget build(BuildContext context) {
    final config = _stepConfig(instruction.mode, isLast);

    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Icon + connector line
          SizedBox(
            width: 48,
            child: Column(
              children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: config.bgColor,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(config.icon,
                      color: config.iconColor, size: 20),
                ),
                if (!isLast)
                  Expanded(
                    child: Container(
                      width: 2,
                      color: const Color(0xFFE0E0E0),
                    ),
                  ),
              ],
            ),
          ),

          const SizedBox(width: 12),

          // Text
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(bottom: 20, top: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    instruction.instruction,
                    style: GoogleFonts.outfit(
                      fontSize: 14,
                      fontWeight: isLast
                          ? FontWeight.w800
                          : FontWeight.w600,
                      color: TukiTheme.darkText,
                    ),
                  ),
                  if (config.subLabel case final subL?) ...[
                    const SizedBox(height: 3),
                    Text(
                      subL,
                      style: GoogleFonts.outfit(
                        fontSize: 12,
                        color: TukiTheme.lightText,
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  _StepConfig _stepConfig(String mode, bool isLast) {
    if (isLast) {
      return _StepConfig(
        icon: Icons.location_on_rounded,
        bgColor: const Color(0xFF9B2600),
        iconColor: Colors.white,
        subLabel: null,
      );
    }
    switch (mode) {
      case 'jeep':
        return _StepConfig(
          icon: Icons.directions_bus_rounded,
          bgColor: const Color(0xFFFFC629),
          iconColor: const Color(0xFF5A3200),
          subLabel: null,
        );
      case 'tricycle':
        return _StepConfig(
          icon: Icons.electric_rickshaw_rounded,
          bgColor: const Color(0xFF34A853),
          iconColor: Colors.white,
          subLabel: null,
        );
      default: // walk / transfer
        return _StepConfig(
          icon: Icons.directions_walk_rounded,
          bgColor: const Color(0xFFFFC629),
          iconColor: const Color(0xFF5A3200),
          subLabel: null,
        );
    }
  }
}

class _StepConfig {
  final IconData icon;
  final Color bgColor;
  final Color iconColor;
  final String? subLabel;

  const _StepConfig({
    required this.icon,
    required this.bgColor,
    required this.iconColor,
    required this.subLabel,
  });
}
