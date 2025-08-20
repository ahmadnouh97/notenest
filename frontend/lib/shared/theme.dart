import 'package:flutter/material.dart';

/// App color palette
class AppColors {
  // Primary palette from user specification
  static const Color lightBlue = Color(0xFFA1CCD1); // #A1CCD1 - Light blue/teal
  static const Color cream = Color(0xFFF4F2DE); // #F4F2DE - Cream/off-white
  static const Color peach = Color(0xFFE9B384); // #E9B384 - Warm peach
  static const Color darkTeal = Color(0xFF7C9D96); // #7C9D96 - Dark teal/sage

  // Additional derived colors for better UI
  static const Color lightBlueVariant = Color(
    0xFFB8D8DB,
  ); // Lighter version of lightBlue
  static const Color peachVariant = Color(
    0xFFF0C499,
  ); // Lighter version of peach
  static const Color darkTealVariant = Color(
    0xFF6B8A83,
  ); // Darker version of darkTeal

  // Surface and background colors
  static const Color surface = Color(0xFFFFFFFE);
  static const Color surfaceVariant = Color(0xFFF8F6F0);

  // Text colors
  static const Color onPrimary = Color(0xFF2C3E37);
  static const Color onSecondary = Color(0xFF4A4A4A);
  static const Color onSurface = Color(0xFF2C3E37);

  // Error and warning
  static const Color error = Color(0xFFD32F2F);
  static const Color warning = Color(0xFFF57C00);
  static const Color success = darkTeal;
}

/// Create the main theme for the app
ThemeData createAppTheme() {
  return ThemeData(
    useMaterial3: true,

    // Color scheme based on the provided palette
    colorScheme: const ColorScheme(
      brightness: Brightness.light,
      primary: AppColors.lightBlue,
      onPrimary: AppColors.onPrimary,
      secondary: AppColors.peach,
      onSecondary: AppColors.onSecondary,
      tertiary: AppColors.darkTeal,
      onTertiary: Colors.white,
      error: AppColors.error,
      onError: Colors.white,
      surface: AppColors.surface,
      onSurface: AppColors.onSurface,
      surfaceContainerHighest: AppColors.cream,
      outline: AppColors.darkTealVariant,
      outlineVariant: AppColors.lightBlueVariant,
    ),

    // App bar theme
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.lightBlue,
      foregroundColor: AppColors.onPrimary,
      elevation: 2,
      shadowColor: AppColors.darkTealVariant,
      titleTextStyle: TextStyle(
        color: AppColors.onPrimary,
        fontSize: 20,
        fontWeight: FontWeight.w600,
      ),
      iconTheme: IconThemeData(color: AppColors.onPrimary),
    ),

    // Card theme
    cardTheme: CardThemeData(
      color: AppColors.cream,
      elevation: 3,
      shadowColor: AppColors.darkTealVariant.withValues(alpha: 0.3),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),

    // Button themes
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: AppColors.peach,
        foregroundColor: AppColors.onSecondary,
        elevation: 3,
        shadowColor: AppColors.darkTealVariant.withValues(alpha: 0.3),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),

    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.darkTeal,
        foregroundColor: Colors.white,
        elevation: 2,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
      ),
    ),

    textButtonTheme: TextButtonThemeData(
      style: TextButton.styleFrom(
        foregroundColor: AppColors.darkTeal,
        textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
      ),
    ),

    // Input decoration theme
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: AppColors.cream,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.lightBlueVariant),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.lightBlueVariant),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.darkTeal, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: AppColors.error),
      ),
      labelStyle: const TextStyle(
        color: AppColors.darkTeal,
        fontWeight: FontWeight.w500,
      ),
      hintStyle: TextStyle(color: AppColors.darkTeal.withValues(alpha: 0.6)),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
    ),

    // Floating action button theme
    floatingActionButtonTheme: const FloatingActionButtonThemeData(
      backgroundColor: AppColors.peach,
      foregroundColor: AppColors.onSecondary,
      elevation: 6,
      shape: CircleBorder(),
    ),

    // Bottom navigation bar theme
    bottomNavigationBarTheme: const BottomNavigationBarThemeData(
      backgroundColor: AppColors.cream,
      selectedItemColor: AppColors.darkTeal,
      unselectedItemColor: AppColors.darkTealVariant,
      elevation: 8,
      type: BottomNavigationBarType.fixed,
    ),

    // Chip theme
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.lightBlueVariant,
      labelStyle: const TextStyle(
        color: AppColors.onPrimary,
        fontWeight: FontWeight.w500,
      ),
      selectedColor: AppColors.peach,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      elevation: 2,
      shadowColor: AppColors.darkTealVariant.withValues(alpha: 0.3),
    ),

    // Snack bar theme
    snackBarTheme: SnackBarThemeData(
      backgroundColor: AppColors.darkTeal,
      contentTextStyle: const TextStyle(color: Colors.white, fontSize: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      behavior: SnackBarBehavior.floating,
    ),

    // Icon theme
    iconTheme: const IconThemeData(color: AppColors.darkTeal, size: 24),

    // Text theme
    textTheme: const TextTheme(
      headlineLarge: TextStyle(
        color: AppColors.onSurface,
        fontSize: 32,
        fontWeight: FontWeight.bold,
      ),
      headlineMedium: TextStyle(
        color: AppColors.onSurface,
        fontSize: 28,
        fontWeight: FontWeight.w600,
      ),
      headlineSmall: TextStyle(
        color: AppColors.onSurface,
        fontSize: 24,
        fontWeight: FontWeight.w600,
      ),
      titleLarge: TextStyle(
        color: AppColors.onSurface,
        fontSize: 22,
        fontWeight: FontWeight.w600,
      ),
      titleMedium: TextStyle(
        color: AppColors.onSurface,
        fontSize: 16,
        fontWeight: FontWeight.w500,
      ),
      titleSmall: TextStyle(
        color: AppColors.onSurface,
        fontSize: 14,
        fontWeight: FontWeight.w500,
      ),
      bodyLarge: TextStyle(
        color: AppColors.onSurface,
        fontSize: 16,
        fontWeight: FontWeight.normal,
      ),
      bodyMedium: TextStyle(
        color: AppColors.onSurface,
        fontSize: 14,
        fontWeight: FontWeight.normal,
      ),
      bodySmall: TextStyle(
        color: AppColors.onSecondary,
        fontSize: 12,
        fontWeight: FontWeight.normal,
      ),
    ),

    // Scaffold background
    scaffoldBackgroundColor: AppColors.surfaceVariant,
  );
}
