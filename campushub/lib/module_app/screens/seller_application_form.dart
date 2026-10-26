import 'seller_application_page.dart';
import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/seller_application_service.dart';
import '../widgets/home/home_preview_cards.dart';
import 'seller_dashboard_page.dart';
import '../routes/app_routes.dart';

class SellerApplicationForm extends StatefulWidget {
  const SellerApplicationForm({
    super.key,
    required this.user,
    this.service = const SellerApplicationService(),
    this.onMarketplace,
    this.onBackToCampusHub,
    this.onMessages,
    this.onNotifications,
    this.onSellerApproved,
  });
  final AuthUser user;
  final SellerApplicationService service;
  final VoidCallback? onMarketplace;
  final VoidCallback? onBackToCampusHub, onMessages, onNotifications;
  final VoidCallback? onSellerApproved;
  @override
  State<SellerApplicationForm> createState() => _SellerApplicationFormState();
}

class _SellerApplicationFormState extends State<SellerApplicationForm>
    with WidgetsBindingObserver {
  final _form = GlobalKey<FormState>();
  late final TextEditingController _contact;
  final _section = TextEditingController(),
      _intended = TextEditingController(),
      _reason = TextEditingController();
  final _terms = <String, bool>{
    'accuracy': false,
    'rules': false,
    'approval': false,
  };
  Map<String, dynamic> _profile = {}, _application = {};
  List<Map<String, dynamic>> _programs = [], _majors = [];
  List<String> _categories = [];
  int? _programId, _majorId;
  String? _category, _status, _error;
  int _step = 0;
  bool _loading = true,
      _sending = false,
      _editing = false,
      _submitted = false,
      _view = false;
  static const _headings = [
    'Applicant Information',
    'Selling Information',
    'Seller Terms',
    'Review Application',
  ];
  static const _termLabels = {
    'accuracy': 'I confirm that the information provided is accurate.',
    'rules':
        'I agree to follow the CampusHub marketplace rules and seller policies.',
    'approval':
        'I understand that my application is subject to Marketplace Administrator approval.',
  };
  Map<String, dynamic> _map(dynamic value) =>
      value is Map ? Map<String, dynamic>.from(value) : {};
  List<Map<String, dynamic>> _rows(dynamic value) => value is List
      ? value
            .whereType<Map>()
            .map((row) => Map<String, dynamic>.from(row))
            .toList()
      : [];

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _contact = TextEditingController(text: widget.user.contactNumber);
    _load();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _contact.dispose();
    _section.dispose();
    _intended.dispose();
    _reason.dispose();
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed && !_loading) _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await widget.service.status();
      if (![
        'none',
        'pending',
        'approved',
        'rejected',
        'needs_revision',
        'suspended',
      ].contains(result['status'])) {
        throw const SellerApplicationException(
          'Unable to read your application status. Retry.',
        );
      }
      if (!mounted) return;
      setState(() {
        _status = result['status'] as String;
        _profile = _map(result['applicant']);
        _application = _map(result['seller_request']);
        _programs = _rows(result['programs']);
        _majors = _rows(result['majors']);
        _categories = (result['categories'] as List? ?? [])
            .whereType<String>()
            .toList();
        _programId ??= _profile['program_id'] as int?;
        _majorId ??= _profile['major_id'] as int?;
        if (_application.isNotEmpty) {
          final saved = _map(_application['application_data']);
          _category = _application['category'] as String?;
          _intended.text = saved['products_intended'] as String? ?? '';
          _section.text = _application['course_section'] as String? ?? '';
          _contact.text =
              _application['contact_number'] as String? ??
              widget.user.contactNumber;
          _reason.text = _application['message'] as String? ?? '';
        }
      });
    } on SellerApplicationException catch (e) {
      if (mounted) setState(() => _error = e.message);
    } catch (_) {
      if (mounted) {
        setState(
          () => _error =
              'Unable to load your application. Check your connection and retry.',
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
    if (mounted && _error == null && _status == 'approved') {
      widget.onSellerApproved?.call();
    }
  }

  bool get _majorApplies =>
      _majors.any((row) => row['program_id'] == _programId);
  bool get _draft =>
      _status == 'none' || (_status == 'needs_revision' && _editing);
  String get _programName =>
      _programs
          .where((row) => row['id'] == _programId)
          .map((row) => '${row['code']}')
          .firstOrNull ??
      '${_profile['program'] ?? 'Unassigned'}';
  String get _majorName =>
      _majors
          .where((row) => row['id'] == _majorId)
          .map((row) => '${row['name']}')
          .firstOrNull ??
      '${_profile['major'] ?? ''}';

  void _continue() {
    if (!_form.currentState!.validate()) return;
    if (_step == 2 && _terms.values.any((agreed) => !agreed)) {
      setState(
        () => _error =
            'Check all three confirmations before reviewing your application.',
      );
      return;
    }
    FocusScope.of(context).unfocus();
    setState(() {
      _error = null;
      _step++;
    });
  }

  Future<void> _submit() async {
    if (_sending ||
        !_draft ||
        _step != 3 ||
        _terms.values.any((value) => !value)) {
      return;
    }
    setState(() {
      _sending = true;
      _error = null;
    });
    try {
      final result = await widget.service.submit({
        'category': _category,
        'products_intended': _intended.text.trim(),
        'course_section': _section.text.trim(),
        'contact_number': _contact.text.trim(),
        'program_id': _programId,
        'major_id': _majorApplies ? _majorId : null,
        'message': _reason.text.trim(),
        'confirmations': _terms,
      });
      final application = _map(result['seller_request']);
      if (application['status'] != 'pending') {
        throw const SellerApplicationException(
          'Unable to confirm submission. Check your application status.',
        );
      }
      if (mounted) {
        setState(() {
          _application = application;
          _status = 'pending';
          _submitted = true;
          _editing = false;
        });
      }
    } on SellerApplicationException catch (e) {
      if (mounted) {
        setState(() {
          _error = e.message;
          _status = null;
        });
      }
    } finally {
      if (mounted) setState(() => _sending = false);
    }
  }

  void _marketplace() {
    Navigator.of(context).popUntil((route) => route.isFirst);
    widget.onMarketplace?.call();
  }

  @override
  Widget build(BuildContext context) => SellerApplicationTheme(
    child: Scaffold(
      backgroundColor: const Color(0xFFF7F8FC),
      appBar: AppBar(
        title: const Text('Seller Application'),
        backgroundColor: HomeAppColors.white,
        foregroundColor: HomeAppColors.navy,
        surfaceTintColor: HomeAppColors.white,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: _loading
              ? const Center(
                  child: CircularProgressIndicator(color: HomeAppColors.navy),
                )
              : Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    if (_error != null) ...[
                      Text(
                        _error!,
                        style: const TextStyle(
                          color: HomeAppColors.navy,
                          height: 1.5,
                        ),
                      ),
                      if (_status == null)
                        TextButton(
                          onPressed: _load,
                          child: const Text('Check Application Status'),
                        ),
                      const SizedBox(height: 16),
                    ],
                    if (_draft)
                      _wizard()
                    else if (_status != null)
                      _statusPanel(),
                  ],
                ),
        ),
      ),
    ),
  );

  Widget _wizard() => Form(
    key: _form,
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          'Step ${_step + 1} of 4',
          style: const TextStyle(color: HomeAppColors.secondaryText),
        ),
        const SizedBox(height: 8),
        Text(
          _headings[_step],
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w700,
            color: HomeAppColors.navy,
          ),
        ),
        const SizedBox(height: 20),
        if (_step == 0) ...[
          _field(
            'Full Name *',
            initial: '${_profile['full_name'] ?? widget.user.fullName}',
            readOnly: true,
          ),
          _field(
            'Student ID / User ID *',
            initial: '${_profile['student_id'] ?? widget.user.studentId}',
            readOnly: true,
          ),
          if (_profile['program_id'] != null)
            _field('Program *', initial: _programName, readOnly: true)
          else
            _select<int>(
              'Program *',
              'Select program',
              _programId,
              _programs
                  .map(
                    (row) => DropdownMenuItem(
                      value: row['id'] as int,
                      child: Text('${row['code']}'),
                    ),
                  )
                  .toList(),
              (value) => setState(() {
                _programId = value;
                _majorId = null;
              }),
            ),
          if (_majorApplies)
            if (_profile['major_id'] != null)
              _field('Major', initial: _majorName, readOnly: true)
            else
              _select<int>(
                'Major *',
                'Select major',
                _majorId,
                _majors
                    .where((row) => row['program_id'] == _programId)
                    .map(
                      (row) => DropdownMenuItem(
                        value: row['id'] as int,
                        child: Text('${row['name']}'),
                      ),
                    )
                    .toList(),
                (value) => setState(() => _majorId = value),
              ),
          _field(
            'Year Level / Section',
            controller: _section,
            hint: 'Enter year level and section',
          ),
          _field(
            'Email Address *',
            initial: '${_profile['email'] ?? widget.user.email}',
            readOnly: true,
          ),
          _field(
            'Contact Number *',
            controller: _contact,
            required: true,
            hint: 'Enter contact number',
            keyboard: TextInputType.phone,
          ),
        ],
        if (_step == 1) ...[
          if (_categories.isEmpty)
            const Text(
              'No marketplace categories are configured. Contact the Marketplace Administrator.',
            ),
          _select<String>(
            'Product Category *',
            'Select category',
            _categories.contains(_category) ? _category : null,
            _categories
                .map((name) => DropdownMenuItem(value: name, child: Text(name)))
                .toList(),
            (value) => setState(() => _category = value),
          ),
          _field(
            'Products Intended to Sell *',
            controller: _intended,
            required: true,
            lines: 4,
            hint: 'Example: baked products, snacks, school supplies',
          ),
          _field(
            'Short Description / Reason for Selling',
            controller: _reason,
            lines: 4,
            hint: 'Describe why you want to sell',
          ),
        ],
        if (_step == 2)
          ..._termLabels.entries.map(
            (term) => CheckboxListTile(
              key: ValueKey('seller-term-${term.key}'),
              contentPadding: EdgeInsets.zero,
              controlAffinity: ListTileControlAffinity.leading,
              activeColor: HomeAppColors.navy,
              title: Text(term.value),
              value: _terms[term.key],
              onChanged: (value) =>
                  setState(() => _terms[term.key] = value ?? false),
            ),
          ),
        if (_step == 3) _review(false),
        const SizedBox(height: 20),
        if (_step == 3) ...[
          OutlinedButton(
            onPressed: _sending ? null : () => setState(() => _step = 0),
            child: const Text('Edit Application'),
          ),
          const SizedBox(height: 8),
          _button(
            _sending
                ? 'Submitting Application?'
                : _status == 'needs_revision'
                ? 'Resubmit Application'
                : 'Submit Application',
            _sending ? null : _submit,
          ),
        ] else ...[
          if (_step > 0)
            OutlinedButton(
              onPressed: () => setState(() {
                _step--;
                _error = null;
              }),
              child: const Text('Back'),
            )
          else
            OutlinedButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Back'),
            ),
          const SizedBox(height: 8),
          _button(_step == 2 ? 'Review Application' : 'Continue', _continue),
        ],
      ],
    ),
  );

  Widget _statusPanel() {
    if (_view) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _review(true),
          const SizedBox(height: 16),
          OutlinedButton(
            onPressed: () => setState(() => _view = false),
            child: const Text('Back'),
          ),
        ],
      );
    }
    final heading = _submitted
        ? 'Application Submitted'
        : switch (_status) {
            'pending' => 'Pending Review',
            'needs_revision' => 'Needs Revision',
            'approved' => 'Approved',
            'rejected' => 'Rejected',
            _ => 'Seller access suspended',
          };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          heading,
          style: const TextStyle(
            fontSize: 22,
            fontWeight: FontWeight.w700,
            color: HomeAppColors.navy,
          ),
        ),
        const SizedBox(height: 12),
        Text(
          _submitted
              ? 'Your application to sell products on CampusHub has been submitted for review.'
              : switch (_status) {
                  'pending' => 'Your application is currently being reviewed.',
                  'needs_revision' =>
                    'Your seller application requires changes before it can be reviewed again.',
                  'approved' =>
                    'Your seller application has been approved. Seller access is now active.',
                  'rejected' => 'Your seller application was not approved.',
                  _ => 'Contact the Marketplace Administrator for assistance.',
                },
          style: const TextStyle(
            color: HomeAppColors.secondaryText,
            height: 1.5,
          ),
        ),
        if (_submitted)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Text('Status: Pending Review'),
          ),
        if (_status == 'needs_revision' &&
            '${_application['revision_notes'] ?? ''}'.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Text('${_application['revision_notes']}'),
          ),
        if (_status == 'rejected' &&
            '${_application['rejection_reason'] ?? ''}'.isNotEmpty)
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Text('${_application['rejection_reason']}'),
          ),
        const SizedBox(height: 20),
        OutlinedButton(
          onPressed: () => setState(() => _view = true),
          child: const Text('View Application'),
        ),
        if (_status == 'needs_revision')
          _button(
            'Edit Application',
            () => setState(() {
              _editing = true;
              _step = 0;
            }),
          ),
        if (_status == 'approved')
          _button(
            'Open Seller Dashboard',
            widget.onSellerApproved ??
                () => Navigator.push(
                  context,
                  MaterialPageRoute<void>(
                    settings: const RouteSettings(
                      name: AppRoutes.sellerDashboard,
                    ),
                    builder: (_) => SellerDashboardPage(
                      user: widget.user,
                      service: widget.service,
                      onBackToCampusHub: widget.onBackToCampusHub,
                      onMessages: widget.onMessages,
                      onNotifications: widget.onNotifications,
                    ),
                  ),
                ),
          ),
        const SizedBox(height: 8),
        _button('Back to Marketplace', _marketplace),
      ],
    );
  }

  Widget _review(bool saved) {
    final data = saved ? _map(_application['application_data']) : _profile;
    final values = <String, String>{
      'Full Name': '${data['full_name'] ?? widget.user.fullName}',
      'Student ID / User ID': '${data['student_id'] ?? widget.user.studentId}',
      'Program': saved ? '${data['program'] ?? 'Unassigned'}' : _programName,
      if (saved ? '${data['major'] ?? ''}'.isNotEmpty : _majorApplies)
        'Major': saved ? '${data['major']}' : _majorName,
      'Year Level / Section': saved
          ? '${_application['course_section'] ?? ''}'
          : _section.text,
      'Email Address': '${data['email'] ?? widget.user.email}',
      'Contact Number': saved
          ? '${_application['contact_number'] ?? ''}'
          : _contact.text,
      'Product Category': saved
          ? '${_application['category'] ?? ''}'
          : _category ?? '',
      'Products Intended to Sell': saved
          ? '${data['products_intended'] ?? ''}'
          : _intended.text,
      'Short Description': saved
          ? '${_application['message'] ?? ''}'
          : _reason.text,
    };
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        for (final entry in values.entries)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (entry.key == 'Full Name' ||
                    entry.key == 'Product Category') ...[
                  Text(
                    entry.key == 'Full Name'
                        ? 'Applicant Information'
                        : 'Selling Information',
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 12),
                ],
                Text(
                  entry.key,
                  style: const TextStyle(
                    color: HomeAppColors.secondaryText,
                    fontSize: 12,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  entry.value.isEmpty ? 'Not provided' : entry.value,
                  style: const TextStyle(
                    color: HomeAppColors.navy,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        const Text(
          'Supporting Requirement',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        const Text('Supporting Document: Not required'),
        const SizedBox(height: 16),
        const Text(
          'Seller Terms',
          style: TextStyle(fontWeight: FontWeight.w700),
        ),
        for (final entry in {
          'accuracy': 'Information Accuracy',
          'rules': 'Marketplace Rules',
          'approval': 'Approval Requirement',
        }.entries)
          Text(
            '${entry.value}: ${(saved ? _map(data['confirmations'])[entry.key] == true : _terms[entry.key] == true) ? 'Agreed' : 'Not recorded'}',
          ),
      ],
    );
  }

  Widget _button(String text, VoidCallback? action) => FilledButton(
    onPressed: action,
    style: FilledButton.styleFrom(
      backgroundColor: HomeAppColors.navy,
      foregroundColor: HomeAppColors.white,
      minimumSize: const Size.fromHeight(52),
      padding: const EdgeInsets.all(16),
    ),
    child: Text(text),
  );
  Widget _select<T>(
    String label,
    String hint,
    T? value,
    List<DropdownMenuItem<T>> items,
    ValueChanged<T?> changed,
  ) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: DropdownButtonFormField<T>(
      key: ValueKey('$label-$_step'),
      initialValue: value,
      isExpanded: true,
      decoration: _decoration(label, hint),
      items: items,
      validator: (value) => value == null
          ? 'Select ${label.replaceAll(' *', '').toLowerCase()}.'
          : null,
      onChanged: changed,
    ),
  );
  InputDecoration _decoration(String label, String? hint) => InputDecoration(
    labelText: label,
    hintText: hint,
    filled: true,
    fillColor: HomeAppColors.white,
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
  );
  Widget _field(
    String label, {
    String? initial,
    TextEditingController? controller,
    bool readOnly = false,
    bool required = false,
    String? hint,
    int lines = 1,
    TextInputType? keyboard,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 20),
    child: TextFormField(
      key: ValueKey('seller-$label'),
      initialValue: initial,
      controller: controller,
      readOnly: readOnly,
      maxLines: lines,
      keyboardType: keyboard,
      maxLength: label.contains('Contact')
          ? 30
          : lines > 1
          ? 3000
          : label.contains('Section')
          ? 120
          : null,
      decoration: _decoration(label, hint),
      validator: (value) =>
          (required || readOnly) && (value?.trim().isEmpty ?? true)
          ? 'Complete ${label.replaceAll(' *', '').toLowerCase()}.'
          : null,
    ),
  );
}
