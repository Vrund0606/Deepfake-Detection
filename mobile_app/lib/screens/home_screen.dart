import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/api_service.dart';
import 'result_screen.dart';
import 'login_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isUploading = false;
  String _loadingMessage = '';

  Future<void> _pickAndUploadFile() async {
    try {
      FilePickerResult? result = await FilePicker.platform.pickFiles(
        type: FileType.video,
        allowMultiple: false,
      );

      if (result != null && result.files.single.path != null) {
        String filePath = result.files.single.path!;
        
        setState(() {
          _isUploading = true;
          _loadingMessage = 'Uploading & Analyzing (This takes time)...';
        });

        // Call the Python Deepfake Flask API
        final analysisData = await ApiService.analyzeMedia(filePath);
        
        setState(() => _isUploading = false);

        if (!mounted) return;
        Navigator.of(context).push(MaterialPageRoute(
          builder: (_) => ResultScreen(data: analysisData)
        ));
      }
    } catch (e) {
      setState(() => _isUploading = false);
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    }
  }

  Future<void> _logout() async {
    try {
      await FirebaseAuth.instance.signOut();
    } catch(e){}
    if (!mounted) return;
    Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen()));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Deepfake Scanner', style: TextStyle(fontFamily: 'Orbitron')),
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(icon: const Icon(Icons.logout), onPressed: _logout)
        ],
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              if (_isUploading) ...[
                const CircularProgressIndicator(color: Color(0xFF06B6D4)),
                const SizedBox(height: 24),
                Text(_loadingMessage, style: const TextStyle(fontSize: 16)),
              ] else ...[
                Container(
                  padding: const EdgeInsets.all(40),
                  decoration: BoxDecoration(
                    color: Theme.of(context).cardColor,
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: const Color(0xFF06B6D4).withOpacity(0.3)),
                    boxShadow: [
                      BoxShadow(color: const Color(0xFF06B6D4).withOpacity(0.1), blurRadius: 20, spreadRadius: 5)
                    ]
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.cloud_upload_outlined, size: 60, color: Colors.grey),
                      const SizedBox(height: 16),
                      const Text('Upload Media File', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
                      const SizedBox(height: 8),
                      const Text('Supports MP4, MOV. Video will be analyzed via Ensemble ViT AI.', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
                      const SizedBox(height: 32),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.folder),
                        label: const Text('BROWSE DEVICE'),
                        style: ElevatedButton.styleFrom(minimumSize: const Size(double.infinity, 50)),
                        onPressed: _pickAndUploadFile,
                      )
                    ],
                  ),
                )
              ]
            ],
          ),
        ),
      ),
    );
  }
}
