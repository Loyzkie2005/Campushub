import 'package:flutter/material.dart';

/// A horizontal step timeline like:
///   ●─────●─────────●
///   1     2         3
///
/// [currentStep] is 0-indexed. Steps at or before currentStep are marked active.
class StepTimeline extends StatelessWidget {
  const StepTimeline({
    super.key,
    required this.steps,
    required this.currentStep,
    this.activeColor = const Color(0xFF142B47),
    this.inactiveColor = const Color(0xFFD4DAE3),
    this.circleSize = 28,
    this.lineHeight = 3,
  });

  final List<String> steps;
  final int currentStep;
  final Color activeColor;
  final Color inactiveColor;
  final double circleSize;
  final double lineHeight;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: List.generate(steps.length * 2 - 1, (index) {
        // Even = circle step, Odd = line
        if (index.isEven) {
          final stepIndex = index ~/ 2;
          final isActive = stepIndex <= currentStep;
          return _StepCircle(
            label: steps[stepIndex],
            number: stepIndex + 1,
            isActive: isActive,
            activeColor: activeColor,
            inactiveColor: inactiveColor,
            size: circleSize,
          );
        } else {
          final beforeStep = index ~/ 2;
          final isActive = beforeStep < currentStep;
          return Expanded(
            child: Container(
              height: lineHeight,
              color: isActive ? activeColor : inactiveColor,
            ),
          );
        }
      }),
    );
  }
}

class _StepCircle extends StatelessWidget {
  const _StepCircle({
    required this.label,
    required this.number,
    required this.isActive,
    required this.activeColor,
    required this.inactiveColor,
    required this.size,
  });

  final String label;
  final int number;
  final bool isActive;
  final Color activeColor;
  final Color inactiveColor;
  final double size;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: size,
          height: size,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            color: isActive ? activeColor : Colors.white,
            border: Border.all(
              color: isActive ? activeColor : inactiveColor,
              width: 2.5,
            ),
          ),
          child: Center(
            child: isActive
                ? const Icon(Icons.check, color: Colors.white, size: 16)
                : Text(
                    '$number',
                    style: TextStyle(
                      color: inactiveColor,
                      fontWeight: FontWeight.w700,
                      fontSize: 12,
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isActive ? FontWeight.w700 : FontWeight.w500,
            color: isActive ? activeColor : inactiveColor,
          ),
          textAlign: TextAlign.center,
        ),
      ],
    );
  }
}
