// Data models shared across features.

class Note {
  final String id;
  final String url;
  final String title;
  final String description;
  final List<String> tags;
  final DateTime createdAt;
  final DateTime updatedAt;

  const Note({
    required this.id,
    required this.url,
    required this.title,
    required this.description,
    required this.tags,
    required this.createdAt,
    required this.updatedAt,
  });

  factory Note.fromJson(Map<String, dynamic> json) => Note(
        id: json['id'] as String,
        url: json['url'] as String? ?? '',
        title: json['title'] as String? ?? '',
        description: json['description'] as String? ?? '',
        tags: (json['tags'] as List?)?.map((e) => e.toString()).toList() ?? const [],
        createdAt: DateTime.parse(json['created_at'] as String),
        updatedAt: DateTime.parse(json['updated_at'] as String),
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'url': url,
        'title': title,
        'description': description,
        'tags': tags,
        'created_at': createdAt.toIso8601String(),
        'updated_at': updatedAt.toIso8601String(),
      };
}

class SearchResultItem {
  final Note note;
  final double score;

  const SearchResultItem({required this.note, required this.score});

  factory SearchResultItem.fromJson(Map<String, dynamic> json) => SearchResultItem(
        note: Note.fromJson(json['note'] as Map<String, dynamic>),
        score: (json['score'] as num).toDouble(),
      );
}

class ChatMessage {
  final String role; // 'user' | 'assistant' | 'system'
  final String content;

  const ChatMessage({required this.role, required this.content});

  Map<String, dynamic> toJson() => {
        'role': role,
        'content': content,
      };
}


