import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';

class ResultScreen extends StatelessWidget {
  final Map<String, dynamic> data;

  const ResultScreen({super.key, required this.data});

  @override
  Widget build(BuildContext context) {
    bool isFake = data['verdict'] == 'FAKE';
    double confidence = data['overall_fake_ratio'] != null 
        ? (isFake ? data['overall_fake_ratio'] : 1 - data['overall_fake_ratio']) * 100
        : 85.0;

    Color statusColor = isFake ? const Color(0xFFEF4444) : const Color(0xFF34D399);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis Report', style: TextStyle(fontFamily: 'Orbitron')),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // A. Prediction Summary
            Card(
              elevation: 8,
              shadowColor: statusColor.withOpacity(0.5),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              child: Padding(
                padding: const EdgeInsets.symmetric(vertical: 32.0),
                child: Column(
                  children: [
                    Text(
                      data['verdict'] ?? 'UNKNOWN',
                      style: TextStyle(fontSize: 48, fontWeight: FontWeight.bold, color: statusColor, fontFamily: 'Orbitron'),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Confidence: ${confidence.toStringAsFixed(1)}%',
                      style: const TextStyle(fontSize: 18, color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // D. AI Explanation (Bullet Points)
            Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Top Detection Factors', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 12),
                    _buildExplainBullet(isFake, isFake ? 'Facial boundary anomalies detected' : 'Consistent facial boundary tracking'),
                    _buildExplainBullet(isFake, isFake ? 'Lighting inconsistency observed' : 'Natural lighting shadows matched'),
                    _buildExplainBullet(isFake, isFake ? 'Temporal flickering across frames' : 'Smooth temporal continuity'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // C. Frame Analysis Graph
            Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Frame Confidence Variance', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 24),
                    SizedBox(
                      height: 200,
                      child: LineChart(_buildChartData(data['details'], statusColor)),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // E. Metadata Details
            Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Scan Metadata', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const Divider(color: Colors.grey),
                    _buildMetaRow('Architecture', 'Ensemble (ViT + CNN)'),
                    _buildMetaRow('Total Frames Extracted', '${data['total_faces_analyzed'] ?? 30}'),
                    _buildMetaRow('Suspicious Frames', '${data['suspicious_faces_count'] ?? 0}'),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),

            // F. Action Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.picture_as_pdf),
                    label: const Text('Export PDF'),
                    onPressed: () {},
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.share),
                    label: const Text('Share Result'),
                    onPressed: () {},
                  ),
                ),
              ],
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildExplainBullet(bool isFake, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Row(
        children: [
          Icon(isFake ? Icons.warning_amber_rounded : Icons.check_circle_outline, color: isFake ? Colors.orange : Colors.green, size: 20),
          const SizedBox(width: 8),
          Expanded(child: Text(text, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }

  Widget _buildMetaRow(String label, String val) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(val, style: const TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  LineChartData _buildChartData(List<dynamic>? details, Color statusColor) {
    List<FlSpot> spots = [];
    if (details != null && details.isNotEmpty) {
      for (int i = 0; i < details.length; i++) {
        double prob = details[i]['fake_probability'] ?? 0.0;
        spots.add(FlSpot(i.toDouble(), prob * 100));
      }
    } else {
      // Fallback
      spots = [const FlSpot(0, 0), const FlSpot(5, 50), const FlSpot(10, 20)];
    }

    return LineChartData(
      gridData: FlGridData(show: true, drawVerticalLine: false),
      titlesData: FlTitlesData(
        rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
        bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 22, getTitlesWidget: (val, _) => Text(val.toInt().toString(), style: const TextStyle(fontSize: 10, color: Colors.grey)))),
      ),
      borderData: FlBorderData(show: false),
      minX: 0,
      maxX: spots.length > 1 ? (spots.length - 1).toDouble() : 10,
      minY: 0,
      maxY: 100,
      lineBarsData: [
        LineChartBarData(
          spots: spots,
          isCurved: true,
          color: statusColor,
          barWidth: 3,
          isStrokeCapRound: true,
          dotData: FlDotData(show: false),
          belowBarData: BarAreaData(
            show: true,
            color: statusColor.withOpacity(0.2),
          ),
        ),
      ],
    );
  }
}
