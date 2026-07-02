/// Model representing the User Profile synchronized with the backend database.
class UserProfile {
  final String id;
  final String email;
  final String? fullName;
  final DateTime createdAt;

  UserProfile({
    required this.id,
    required this.email,
    this.fullName,
    required this.createdAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      email: json['email'] as String,
      fullName: json['full_name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'full_name': fullName,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
