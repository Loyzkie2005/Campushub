import 'dart:async';
import 'dart:convert';

import 'package:campushub/module_app/config/api_config.dart';
import 'package:campushub/module_app/screens/profile_page.dart';
import 'package:campushub/module_app/services/auth_service.dart';
import 'package:campushub/module_app/services/profile_photo_service.dart';
import 'package:campushub/module_app/session/session_service.dart';
import 'package:campushub/module_app/widgets/profile/profile_widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image_picker_platform_interface/image_picker_platform_interface.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'profile_page_test.dart' show user;

class TestPhotoPicker extends ImagePickerPlatform {
  XFile? file;
  PlatformException? error;
  int picks = 0;
  LostDataResponse? recovered;

  @override
  Future<XFile?> getImageFromSource({
    required ImageSource source,
    ImagePickerOptions options = const ImagePickerOptions(),
  }) async {
    picks++;
    expect(source, ImageSource.gallery);
    expect(options.maxWidth, 1024);
    expect(options.requestFullMetadata, isFalse);
    if (error != null) throw error!;
    return file;
  }

  @override
  Future<LostDataResponse> getLostData() async =>
      recovered ?? LostDataResponse.empty();
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  late ImagePickerPlatform previous;
  late TestPhotoPicker picker;
  final png = base64Decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==',
  );
  const photoUrl = '/media/profile-photos/1/test.jpg';

  setUp(() {
    previous = ImagePickerPlatform.instance;
    picker = TestPhotoPicker();
    ImagePickerPlatform.instance = picker;
    SharedPreferences.setMockInitialValues({
      'campushub_logged_user': jsonEncode(user),
      'campushub_chat_token': 'test-token',
    });
    ApiConfig.recordWorkingBaseUrl('http://localhost:8000');
  });
  tearDown(() => ImagePickerPlatform.instance = previous);

  http.Response getResponse(http.Request request) => http.Response(
    jsonEncode(
      request.url.path.endsWith('/profile/photo/')
          ? {'user': user}
          : {'status': 'none', 'is_approved_seller': false},
    ),
    200,
  );

  Future<void> open(WidgetTester tester) async {
    await tester.pumpWidget(
      const MaterialApp(home: Scaffold(body: ProfilePage())),
    );
    await tester.pumpAndSettle();
  }

  Future<void> change(WidgetTester tester) async {
    await tester.tap(find.byTooltip('Change profile picture'));
    await tester.pumpAndSettle();
  }

  testWidgets('cancel leaves account and photo unchanged without a POST', (
    tester,
  ) async {
    var posts = 0;
    await http.runWithClient(
      () async {
        await open(tester);
        expect(find.text('Edit Profile'), findsNothing);
        expect(
          tester.getSize(find.byKey(const ValueKey('profile-change-photo'))),
          const Size(48, 48),
        );
        await change(tester);
        expect(picker.picks, 1);
        expect(posts, 0);
        expect((await SessionService.loadUser())!.profilePhotoUrl, isEmpty);
        expect(await SessionService.loadChatToken(), 'test-token');
        expect(find.byTooltip('Change profile picture'), findsOneWidget);
      },
      () => MockClient((request) async {
        if (request.method == 'POST') posts++;
        return getResponse(request);
      }),
    );
  });

  testWidgets(
    'selected photo sends one owner-authenticated multipart upload and persists returned URL',
    (tester) async {
      picker.file = XFile.fromData(png, name: 'test.png');
      var posts = 0;
      await http.runWithClient(
        () async {
          await open(tester);
          await change(tester);
          expect(posts, 1);
          expect(find.text('Profile picture updated.'), findsOneWidget);
          final saved = (await SessionService.loadUser())!;
          expect(saved.profilePhotoUrl, photoUrl);
          expect(
            saved.resolvedProfilePhotoUrl,
            'http://localhost:8000$photoUrl',
          );
          expect(await SessionService.loadChatToken(), 'test-token');
          expect(
            tester
                .widget<ProfileIdentityHeader>(
                  find.byType(ProfileIdentityHeader),
                )
                .user
                .profilePhotoUrl,
            photoUrl,
          );
          expect(tester.takeException(), isNull);
        },
        () => MockClient((request) async {
          if (request.method != 'POST') return getResponse(request);
          posts++;
          expect(request.url.path, '/api/mobile/profile/photo/');
          expect(request.headers['Authorization'], 'Bearer test-token');
          expect(
            request.headers['content-type'],
            startsWith('multipart/form-data;'),
          );
          expect(latin1.decode(request.bodyBytes), contains('name="photo"'));
          return http.Response(
            jsonEncode({
              'user': {...user, 'profile_photo_url': photoUrl},
            }),
            200,
          );
        }),
      );
    },
  );

  testWidgets(
    'server rejection and picker permission failure leave saved identity intact and allow retry',
    (tester) async {
      picker.file = XFile.fromData(png, name: 'test.png');
      var posts = 0;
      await http.runWithClient(
        () async {
          await open(tester);
          await change(tester);
          expect(posts, 1);
          expect(
            find.text('Choose a JPEG, PNG, or WebP picture.'),
            findsOneWidget,
          );
          expect((await SessionService.loadUser())!.profilePhotoUrl, isEmpty);
          picker.error = PlatformException(code: 'photo_access_denied');
          await change(tester);
          expect(posts, 1);
          expect(find.byTooltip('Change profile picture'), findsOneWidget);
          expect(tester.takeException(), isNull);
        },
        () => MockClient((request) async {
          if (request.method != 'POST') return getResponse(request);
          posts++;
          return http.Response(
            jsonEncode({'error': 'Choose a JPEG, PNG, or WebP picture.'}),
            400,
          );
        }),
      );
    },
  );

  testWidgets('oversize photo is rejected before any upload', (tester) async {
    picker.file = XFile.fromData(Uint8List(ProfilePhotoService.maxBytes + 1));
    var posts = 0;
    await http.runWithClient(
      () async {
        await open(tester);
        await change(tester);
        expect(posts, 0);
        expect(
          find.text('Choose a picture smaller than 5 MB.'),
          findsOneWidget,
        );
      },
      () => MockClient((request) async {
        if (request.method == 'POST') posts++;
        return getResponse(request);
      }),
    );
  });

  testWidgets(
    'in-flight upload disables repeated taps and persists returned photo',
    (tester) async {
      picker.file = XFile.fromData(png, name: 'test.png');
      final response = Completer<http.Response>();
      var posts = 0;
      await http.runWithClient(
        () async {
          await open(tester);
          await tester.tap(find.byTooltip('Change profile picture'));
          for (var i = 0; i < 10; i++) {
            await tester.pump(const Duration(milliseconds: 10));
          }
          expect(find.byTooltip('Updating profile picture'), findsOneWidget);
          expect(
            tester
                .widget<IconButton>(
                  find.byKey(const ValueKey('profile-change-photo')),
                )
                .onPressed,
            isNull,
          );
          response.complete(
            http.Response(
              jsonEncode({
                'user': {...user, 'profile_photo_url': photoUrl},
              }),
              200,
            ),
          );
          await tester.pumpAndSettle();
          expect(posts, 1);
          expect((await SessionService.loadUser())!.profilePhotoUrl, photoUrl);
        },
        () => MockClient((request) async {
          if (request.method != 'POST') return getResponse(request);
          posts++;
          return response.future;
        }),
      );
    },
  );

  testWidgets(
    'Android restores a pending picker result only for the original account',
    (tester) async {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt('campushub_pending_profile_photo_owner', 1);
      picker.recovered = LostDataResponse(
        files: [XFile.fromData(png, name: 'restored.png')],
        type: RetrieveType.image,
      );
      var posts = 0;
      await http.runWithClient(
        () async {
          await open(tester);
          expect(posts, 1);
          expect((await SessionService.loadUser())!.profilePhotoUrl, photoUrl);
          expect(prefs.getInt('campushub_pending_profile_photo_owner'), isNull);
        },
        () => MockClient((request) async {
          if (request.method != 'POST') return getResponse(request);
          posts++;
          return http.Response(
            jsonEncode({
              'user': {...user, 'profile_photo_url': photoUrl},
            }),
            200,
          );
        }),
      );
    },
  );

  testWidgets('Android discards a pending photo from a different account', (
    tester,
  ) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('campushub_pending_profile_photo_owner', 99);
    picker.recovered = LostDataResponse(
      files: [XFile.fromData(png, name: 'other-account.png')],
      type: RetrieveType.image,
    );
    var posts = 0;
    await http.runWithClient(
      () async {
        await open(tester);
        expect(posts, 0);
        expect(prefs.getInt('campushub_pending_profile_photo_owner'), isNull);
      },
      () => MockClient((request) async {
        if (request.method == 'POST') posts++;
        return getResponse(request);
      }),
    );
  });

  test('legacy sessions have no invented photo', () {
    expect(AuthUser.fromJson(user).profilePhotoUrl, isEmpty);
  });
}
