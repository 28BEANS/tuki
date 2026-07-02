/// Model representing the User Profile synchronized with the backend database.
class UserProfile {
  final String id;
  final String email;
  final String? firstName;
  final String? lastName;
  final DateTime createdAt;

  UserProfile({
    required this.id,
    required this.email,
    this.firstName,
    this.lastName,
    required this.createdAt,
  });

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    return UserProfile(
      id: json['id'] as String,
      email: json['email'] as String,
      firstName: json['first_name'] as String?,
      lastName: json['last_name'] as String?,
      createdAt: DateTime.parse(json['created_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'first_name': firstName,
      'last_name': lastName,
      'created_at': createdAt.toIso8601String(),
    };
  }
}
