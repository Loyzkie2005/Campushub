import 'package:flutter/material.dart';

const _navy = Color(0xFF1A1851);
const _gold = Color(0xFFFCB316);

Future<bool> showCampusLegalDialog(BuildContext context) async {
  return await showDialog<bool>(
        context: context,
        barrierDismissible: false,
        builder: (_) => const _CampusLegalDialog(),
      ) ??
      false;
}

class _CampusLegalDialog extends StatelessWidget {
  const _CampusLegalDialog();

  @override
  Widget build(BuildContext context) {
    final isLight = Theme.of(context).brightness == Brightness.light;
    final foreground = isLight ? _navy : Colors.white;
    final muted = isLight ? const Color(0xFF64748B) : Colors.white70;
    final surface = isLight ? Colors.white : const Color(0xFF24215E);

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 20),
      backgroundColor: surface,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 620, maxHeight: 760),
        child: SizedBox(
          height: MediaQuery.sizeOf(context).height * 0.86,
          child: DefaultTabController(
            length: 2,
            child: Column(
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(18, 14, 8, 8),
                  child: Row(
                    children: [
                      Container(
                        width: 34,
                        height: 34,
                        decoration: BoxDecoration(
                          color: _gold.withValues(alpha: 0.16),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Icon(
                          Icons.policy_outlined,
                          color: _gold,
                          size: 20,
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Terms and Conditions & Privacy Policy',
                          maxLines: 2,
                          style: TextStyle(
                            color: foreground,
                            fontSize: 16,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                      ),
                      IconButton(
                        tooltip: 'Close',
                        onPressed: () => Navigator.pop(context, false),
                        icon: Icon(Icons.close, color: muted),
                      ),
                    ],
                  ),
                ),
                TabBar(
                  labelColor: isLight ? _navy : _gold,
                  unselectedLabelColor: muted,
                  indicatorColor: _gold,
                  indicatorWeight: 3,
                  tabs: const [
                    Tab(text: 'Terms and Conditions'),
                    Tab(text: 'Privacy Policy'),
                  ],
                ),
                Divider(height: 1, color: muted.withValues(alpha: 0.22)),
                Expanded(
                  child: TabBarView(
                    children: [
                      _LegalDocument(
                        title: 'Terms and Conditions',
                        introduction:
                            'Welcome to CampusHub. By creating an account, accessing, or using CampusHub, you agree to these Terms and Conditions.',
                        sections: _termsSections,
                        closing:
                            'By selecting “I Agree,” registering an account, or continuing to use CampusHub, you acknowledge that you have read, understood, and agreed to these Terms and Conditions.',
                        foreground: foreground,
                        muted: muted,
                      ),
                      _LegalDocument(
                        title: 'Privacy Policy',
                        introduction:
                            'CampusHub respects the privacy of its users. This Privacy Policy explains what information CampusHub may collect, why the information is collected, and how it may be used and protected.',
                        sections: _privacySections,
                        closing:
                            'By creating an account or using CampusHub, you acknowledge that you have read and understood this Privacy Policy.',
                        foreground: foreground,
                        muted: muted,
                      ),
                    ],
                  ),
                ),
                Divider(height: 1, color: muted.withValues(alpha: 0.22)),
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Align(
                    alignment: Alignment.centerRight,
                    child: SizedBox(
                      width: 120,
                      child: FilledButton(
                        onPressed: () => Navigator.pop(context, true),
                        style: FilledButton.styleFrom(
                          backgroundColor: isLight ? _navy : _gold,
                          foregroundColor: isLight ? Colors.white : _navy,
                          minimumSize: const Size.fromHeight(45),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: const Text('I Agree'),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _LegalDocument extends StatelessWidget {
  const _LegalDocument({
    required this.title,
    required this.introduction,
    required this.sections,
    required this.closing,
    required this.foreground,
    required this.muted,
  });

  final String title;
  final String introduction;
  final List<_LegalSectionData> sections;
  final String closing;
  final Color foreground;
  final Color muted;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(18, 18, 18, 24),
      child: SelectionArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: TextStyle(
                color: foreground,
                fontSize: 20,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'Last Updated: August 11, 2026',
              style: TextStyle(
                color: muted,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 14),
            Text(
              introduction,
              style: TextStyle(color: foreground, fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 16),
            for (final section in sections)
              _LegalSection(data: section, foreground: foreground),
            const SizedBox(height: 4),
            Text(
              closing,
              style: TextStyle(
                color: foreground,
                fontSize: 13,
                height: 1.5,
                fontWeight: FontWeight.w600,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LegalSection extends StatelessWidget {
  const _LegalSection({required this.data, required this.foreground});

  final _LegalSectionData data;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            data.heading,
            style: TextStyle(
              color: foreground,
              fontSize: 14,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          for (final paragraph in data.paragraphs) ...[
            Text(
              paragraph,
              style: TextStyle(color: foreground, fontSize: 13, height: 1.5),
            ),
            const SizedBox(height: 7),
          ],
          for (final item in data.bullets)
            Padding(
              padding: const EdgeInsets.only(left: 4, bottom: 5),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('•  ', style: TextStyle(color: foreground, height: 1.5)),
                  Expanded(
                    child: Text(
                      item,
                      style: TextStyle(
                        color: foreground,
                        fontSize: 13,
                        height: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _LegalSectionData {
  const _LegalSectionData({
    required this.heading,
    this.paragraphs = const [],
    this.bullets = const [],
  });

  final String heading;
  final List<String> paragraphs;
  final List<String> bullets;
}

const _termsSections = [
  _LegalSectionData(
    heading: '1. Purpose',
    paragraphs: [
      'CampusHub is a campus-focused platform designed to help students and authorized users access and manage campus-related information, services, activities, announcements, events, and other available features.',
    ],
  ),
  _LegalSectionData(
    heading: '2. User Accounts',
    paragraphs: [
      'Users must provide accurate and complete information when registering.',
      'Users are responsible for keeping their usernames, passwords, and other account credentials secure. Accounts should not be shared with other individuals.',
    ],
  ),
  _LegalSectionData(
    heading: '3. Acceptable Use',
    paragraphs: [
      'Users agree to use CampusHub responsibly and only for legitimate campus-related purposes.',
      'Users must not:',
    ],
    bullets: [
      'Provide false or misleading information.',
      'Impersonate another student or user.',
      "Access another user's account without permission.",
      'Upload harmful, offensive, illegal, or inappropriate content.',
      'Attempt to hack, damage, disrupt, or bypass CampusHub security.',
      'Use CampusHub for fraudulent or unauthorized activities.',
      'Spam, harass, threaten, or intentionally harm other users.',
    ],
  ),
  _LegalSectionData(
    heading: '4. Campus Content',
    paragraphs: [
      'Announcements, events, posts, schedules, and other campus information available through CampusHub may be created or submitted by authorized users.',
      'CampusHub administrators may review, update, restrict, or remove content that violates platform rules or applicable campus policies.',
    ],
  ),
  _LegalSectionData(
    heading: '5. User-Generated Content',
    paragraphs: [
      'Users may be allowed to submit posts, comments, feedback, images, or other information.',
      'Users remain responsible for the content they submit and must ensure that they have the right to share it.',
      'Content that is abusive, misleading, illegal, discriminatory, harmful, or otherwise inappropriate may be removed.',
    ],
  ),
  _LegalSectionData(
    heading: '6. Privacy',
    paragraphs: [
      'CampusHub may collect and process information necessary to provide its services. Personal information will be handled according to the CampusHub Privacy Policy and applicable privacy requirements.',
    ],
  ),
  _LegalSectionData(
    heading: '7. System Availability',
    paragraphs: [
      "CampusHub aims to provide reliable access to its services. However, the platform may occasionally become unavailable because of maintenance, updates, network problems, server issues, or circumstances outside the administrators' control.",
      'Continuous availability is not guaranteed.',
    ],
  ),
  _LegalSectionData(
    heading: '8. Account Suspension or Termination',
    paragraphs: [
      'CampusHub administrators may restrict, suspend, or terminate accounts when there is reasonable evidence of:',
    ],
    bullets: [
      'Violation of these Terms and Conditions.',
      'Fraudulent activity.',
      'Unauthorized system access.',
      'Harassment or abusive behavior.',
      'Attempts to compromise CampusHub security.',
      'Serious violations of applicable campus policies.',
    ],
  ),
  _LegalSectionData(
    heading: '9. Limitation of Responsibility',
    paragraphs: [
      'CampusHub provides campus-related information and digital services for convenience. Users should verify important academic, administrative, financial, or emergency information through the appropriate official campus office when necessary.',
      'CampusHub is not responsible for problems resulting from incorrect information submitted by users or unauthorized third parties.',
    ],
  ),
  _LegalSectionData(
    heading: '10. Changes to These Terms',
    paragraphs: [
      'These Terms and Conditions may be updated as CampusHub develops or when legal, security, technical, or campus requirements change.',
      'Users may be notified when significant changes are made.',
    ],
  ),
  _LegalSectionData(
    heading: '11. Contact',
    paragraphs: [
      'Questions or concerns regarding these Terms and Conditions may be submitted to the CampusHub administrator or designated campus representative.',
    ],
  ),
];

const _privacySections = [
  _LegalSectionData(
    heading: '1. Information We May Collect',
    paragraphs: [
      'Depending on the CampusHub features available to you, we may collect information such as:',
    ],
    bullets: [
      'Full name',
      'Student ID or identification number',
      'Email address',
      'Course or academic program',
      'Year level and section',
      'Profile information',
      'Account credentials',
      'Campus activity and event information',
      'Posts, comments, feedback, or reports submitted by users',
      'Other information voluntarily provided through CampusHub',
      'Limited technical information necessary for security, troubleshooting, and maintaining the platform',
    ],
  ),
  _LegalSectionData(
    heading: '2. How We Use Your Information',
    paragraphs: ['Information may be used to:'],
    bullets: [
      'Create and manage CampusHub accounts.',
      'Authenticate users.',
      'Provide CampusHub features and services.',
      'Display relevant campus announcements and events.',
      'Manage campus-related activities.',
      'Communicate important platform information.',
      'Respond to feedback and reports.',
      'Prevent unauthorized access and misuse.',
      'Maintain platform security.',
      'Improve CampusHub functionality and user experience.',
    ],
  ),
  _LegalSectionData(
    heading: '3. How We Protect Your Information',
    paragraphs: [
      'CampusHub should use reasonable technical and administrative safeguards to protect personal information against unauthorized access, alteration, disclosure, misuse, or loss.',
      'Passwords should be securely stored using appropriate password-hashing techniques rather than being stored as plain text.',
      'No internet-based system can guarantee absolute security.',
    ],
  ),
  _LegalSectionData(
    heading: '4. Sharing of Information',
    paragraphs: [
      "CampusHub does not sell users' personal information.",
      'Information may only be shared when reasonably necessary with authorized campus personnel, system administrators, service providers supporting CampusHub, or authorities when disclosure is required by applicable law.',
    ],
  ),
  _LegalSectionData(
    heading: '5. Data Retention',
    paragraphs: [
      'Personal information should only be retained for as long as necessary to operate CampusHub, satisfy legitimate campus requirements, maintain necessary records, or comply with applicable legal obligations.',
      'Information that is no longer required should be securely deleted or anonymized when appropriate.',
    ],
  ),
  _LegalSectionData(
    heading: '6. User Rights',
    paragraphs: [
      'Subject to applicable law and campus policies, users may have the right to:',
    ],
    bullets: [
      'Request access to their personal information.',
      'Request correction of inaccurate information.',
      'Request deletion of certain personal information.',
      'Raise concerns regarding the processing of their information.',
      'Withdraw consent where processing is based on consent.',
      'Certain information may need to be retained when required for legitimate academic, administrative, security, or legal purposes.',
    ],
  ),
  _LegalSectionData(
    heading: '7. Cookies and Sessions',
    paragraphs: [
      'The CampusHub website may use cookies, session storage, or similar technologies to maintain login sessions, remember preferences, improve security, and provide essential platform functionality.',
    ],
  ),
  _LegalSectionData(
    heading: '8. Third-Party Services',
    paragraphs: [
      'CampusHub may use third-party technologies or services for functions such as hosting, authentication, notifications, analytics, or data storage.',
      'When third-party services are used, information should only be shared to the extent necessary to provide the relevant service.',
    ],
  ),
  _LegalSectionData(
    heading: '9. Changes to This Privacy Policy',
    paragraphs: [
      'This Privacy Policy may be updated when CampusHub introduces new functionality or when legal, security, or campus requirements change.',
      'Users may be notified of significant changes.',
    ],
  ),
  _LegalSectionData(
    heading: '10. Contact',
    paragraphs: [
      'For privacy-related questions, requests, or concerns, users may contact the CampusHub administrator or the appropriate campus representative.',
    ],
  ),
];
