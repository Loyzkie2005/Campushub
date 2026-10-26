import 'package:flutter/material.dart';

/// Preserve visited tab state (search, scroll and loaded records) in PageView.
class RetainedTab extends StatefulWidget {
  const RetainedTab({super.key, required this.child});
  final Widget child;
  @override
  State<RetainedTab> createState() => _RetainedTabState();
}

class _RetainedTabState extends State<RetainedTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true;
  @override
  Widget build(BuildContext context) {
    super.build(context);
    return widget.child;
  }
}
