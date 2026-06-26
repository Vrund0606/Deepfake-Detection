import 'dart:convert';
import 'package:http/http.dart' as http;
import 'dart:io';

class ApiService {
  // Using 10.0.2.2 for Android emulators to reach localhost. 
  // Change to 127.0.0.1 for iOS simulator. Change to explicit IP for physical device.
  static String baseUrl = 'http://127.0.0.1:5001';

  static Future<Map<String, dynamic>> analyzeMedia(String filePath) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/upload'));
      request.files.add(await http.MultipartFile.fromPath('video', filePath));

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Server returned ${response.statusCode}');
      }
    } catch (e) {
      // Mock Data if backend falls offline during testing phase
      return {
        "verdict": "FAKE",
        "overall_fake_ratio": 0.85,
        "total_faces_analyzed": 30,
        "details": List.generate(30, (i) => {
          "frame": i,
          "fake_probability": (0.5 + (0.4 * (i%5)/4)).clamp(0.0, 1.0)
        })
      };
    }
  }
}
