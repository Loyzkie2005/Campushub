import bcrypt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import CampushubLogin


def _user_payload(user, role='Student'):
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': f'{user.first_name} {user.last_name}',
        'role': role,
    }


@api_view(['POST'])
def signup(request):
    data = request.data
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip()
    password = data.get('password') or ''
    confirm_password = data.get('confirm_password') or ''

    # Validation
    if not all([first_name, last_name, username, email, password]):
        return Response({'error': 'All fields are required.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if password != confirm_password:
        return Response({'error': 'Passwords do not match.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 6:
        return Response({'error': 'Password must be at least 6 characters.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if len(username) < 3:
        return Response({'error': 'Username must be at least 3 characters.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if CampushubLogin.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists.'},
                        status=status.HTTP_400_BAD_REQUEST)

    if CampushubLogin.objects.filter(email=email).exists():
        return Response({'error': 'Email already exists.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Hash password
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    # Create user
    user = CampushubLogin.objects.create(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        password_hash=hashed,
    )

    return Response({
        'message': 'Account created successfully.',
        'user': _user_payload(user),
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login(request):
    data = request.data
    username_or_email = (data.get('username_or_email') or '').strip()
    password = data.get('password') or ''

    if not username_or_email or not password:
        return Response({'error': 'Please enter your credentials.'},
                        status=status.HTTP_400_BAD_REQUEST)

    user = CampushubLogin.objects.filter(username=username_or_email).first() \
        or CampushubLogin.objects.filter(email=username_or_email).first()

    if not user:
        return Response({'error': 'Account not found. Please sign up first.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    if not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        return Response({'error': 'Incorrect password.'},
                        status=status.HTTP_401_UNAUTHORIZED)

    return Response({
        'message': 'Login successful.',
        'user': _user_payload(user),
    }, status=status.HTTP_200_OK)
