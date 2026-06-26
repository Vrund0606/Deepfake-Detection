import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await Firebase.initializeApp();
  } catch (e) {
    debugPrint("Firebase not configured. Please add google-services.json later.");
  }
  runApp(const DeepfakeApp());
}

class DeepfakeApp extends StatelessWidget {
  const DeepfakeApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Deepfake Detector',
      theme: ThemeData(
        brightness: Brightness.dark,
        primaryColor: const Color(0xFF06B6D4),
        scaffoldBackgroundColor: const Color(0xFF0B0F19),
        cardColor: const Color(0xFF101728),
        elevatedButtonTheme: ElevatedButtonThemeData(
          style: ElevatedButton.styleFrom(
            backgroundColor: const Color(0xFF06B6D4),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(vertical: 16),
          ),
        ),
      ),
      home: const AuthWrapper(),
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});
  @override
  Widget build(BuildContext context) {
    try {
      return StreamBuilder<User?>(
        stream: FirebaseAuth.instance.authStateChanges(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return const HomeScreen();
          }
          return const LoginScreen();
        },
      );
    } catch (_) {
      // Fallback if Firebase not fully initialized
      return const LoginScreen();
    }
  }
}
