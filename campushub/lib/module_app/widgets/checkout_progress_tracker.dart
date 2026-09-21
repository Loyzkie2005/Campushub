import 'package:flutter/material.dart';

enum CheckoutFlowStep { productCheckout, checkout, review }

class CheckoutProgressTracker extends StatelessWidget {
  const CheckoutProgressTracker({
    super.key,
    required this.currentStep,
    this.markProductCheckoutComplete = false,
    this.allStepsComplete = false,
  });

  final CheckoutFlowStep currentStep;
  final bool markProductCheckoutComplete;
  final bool allStepsComplete;

  static const labels = ['Product', 'Checkout', 'Review'];
  static const navy = Color(0xFF1A1851);
  static const muted = Color(0xFF94A3B8);
  static const line = Color(0xFFE2E8F0);

  int get _activeIndex =>
      allStepsComplete ? labels.length : currentStep.index;

  bool _isCompleted(int index) {
    if (allStepsComplete) return true;
    if (index < _activeIndex) return true;
    if (index == 0 && markProductCheckoutComplete && _activeIndex >= 1) {
      return true;
    }
    return false;
  }

  bool _isActive(int index) {
    if (allStepsComplete) return false;
    return index == _activeIndex;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      color: Colors.white,
      padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
      child: Row(
        children: [
          for (var i = 0; i < labels.length; i++) ...[
            Expanded(
              child: _StepItem(
                label: labels[i],
                stepNumber: i + 1,
                isActive: _isActive(i),
                isCompleted: _isCompleted(i),
              ),
            ),
            if (i < labels.length - 1)
              Expanded(
                child: _StepConnector(isCompleted: _isCompleted(i)),
              ),
          ],
        ],
      ),
    );
  }
}

class _StepItem extends StatelessWidget {
  const _StepItem({
    required this.label,
    required this.stepNumber,
    required this.isActive,
    required this.isCompleted,
  });

  final String label;
  final int stepNumber;
  final bool isActive;
  final bool isCompleted;

  @override
  Widget build(BuildContext context) {
    final accent = CheckoutProgressTracker.navy;
    final circleColor = isCompleted || isActive ? accent : Colors.white;
    final borderColor =
        isCompleted || isActive ? accent : CheckoutProgressTracker.line;
    final labelColor = isActive || isCompleted
        ? CheckoutProgressTracker.navy
        : CheckoutProgressTracker.muted;

    return Column(
      mainAxisSize: MainAxisSize.min,
      children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 220),
          width: 28,
          height: 28,
          decoration: BoxDecoration(
            color: circleColor,
            shape: BoxShape.circle,
            border: Border.all(color: borderColor, width: 2),
          ),
          child: Center(
            child: isCompleted
                ? const Icon(Icons.check_rounded, size: 16, color: Colors.white)
                : Text(
                    '$stepNumber',
                    style: TextStyle(
                      color: isActive
                          ? Colors.white
                          : CheckoutProgressTracker.muted,
                      fontSize: 12,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          textAlign: TextAlign.center,
          maxLines: 2,
          overflow: TextOverflow.ellipsis,
          style: TextStyle(
            color: labelColor,
            fontSize: 10,
            height: 1.2,
            fontWeight:
                isActive || isCompleted ? FontWeight.w800 : FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

class _StepConnector extends StatelessWidget {
  const _StepConnector({required this.isCompleted});

  final bool isCompleted;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 22),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 220),
        height: 2,
        margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: BoxDecoration(
          color: isCompleted
              ? CheckoutProgressTracker.navy
              : CheckoutProgressTracker.line,
          borderRadius: BorderRadius.circular(999),
        ),
      ),
    );
  }
}
