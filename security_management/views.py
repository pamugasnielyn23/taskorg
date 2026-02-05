from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm, LoginForm, ProfileEditForm
from .models import Profile, PasswordResetCode

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create profile for the new user
            Profile.objects.get_or_create(user=user)
            messages.success(request, 'Registration successful! You can now log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'security_management/pages/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']
            
            # Try to authenticate with username first
            user = authenticate(request, username=username_or_email, password=password)
            
            # If username authentication fails, try finding user by email
            if user is None:
                try:
                    user_obj = User.objects.get(email=username_or_email)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                # Check if this is the first login ever (last_login is None until first login)
                if user.last_login is None:
                    request.session['is_first_login'] = True
                else:
                    request.session['is_first_login'] = False
                    
                login(request, user)
                return redirect('organizer_dashboard')
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = LoginForm()
    return render(request, 'security_management/pages/login.html', {'form': form})

@login_required
def profile_view(request):
    # Get or create profile for current user
    profile, created = Profile.objects.get_or_create(user=request.user)
    return render(request, 'security_management/pages/profile.html', {
        'user': request.user,
        'profile': profile
    })

@login_required
def profile_edit_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=profile, user=request.user)
    
    return render(request, 'security_management/pages/profile_edit.html', {
        'form': form,
        'profile': profile
    })

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')


# ============================================
# Password Reset with 6-Digit Code (Facebook-style)
# ============================================

def request_reset_code_view(request):
    """Step 1: User enters email to receive 6-digit code"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        
        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'security_management/pages/password_reset_code.html')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate 6-digit code
            reset_code = PasswordResetCode.generate_code(user)
            
            # Send email with code
            subject = 'TASK.IO - Your Password Reset Code'
            message = f'''Hello {user.username},

You requested to reset your password. Use this 6-digit code to verify your identity:

    🔐  {reset_code.code}

This code will expire in 15 minutes.

If you didn't request this, please ignore this email.

Best regards,
The TASK.IO Team
'''
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@taskio.com',
                    [email],
                    fail_silently=False,
                )
                # Store email in session for next step
                request.session['reset_email'] = email
                messages.success(request, f'A 6-digit code has been sent to {email}')
                return redirect('verify_reset_code')
            except Exception as e:
                messages.error(request, f'Failed to send email. Please try again. Error: {str(e)}')
                
        except User.DoesNotExist:
            # Don't reveal if email exists - show same message
            messages.success(request, f'If an account exists with this email, a code has been sent.')
            return redirect('verify_reset_code')
    
    return render(request, 'security_management/pages/password_reset_code.html')


def verify_reset_code_view(request):
    """Step 2: User enters the 6-digit code they received"""
    email = request.session.get('reset_email')
    
    if not email:
        messages.error(request, 'Please start the password reset process again.')
        return redirect('request_reset_code')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code or len(code) != 6:
            messages.error(request, 'Please enter a valid 6-digit code.')
            return render(request, 'security_management/pages/password_reset_verify.html', {'email': email})
        
        try:
            user = User.objects.get(email=email)
            reset_code = PasswordResetCode.objects.filter(
                user=user, 
                code=code, 
                is_used=False
            ).first()
            
            if reset_code and reset_code.is_valid():
                # Code is valid - store user id for password change
                request.session['reset_user_id'] = user.id
                request.session['reset_code_id'] = reset_code.id
                return redirect('set_new_password')
            else:
                messages.error(request, 'Invalid or expired code. Please try again.')
                
        except User.DoesNotExist:
            messages.error(request, 'Invalid code. Please try again.')
    
    return render(request, 'security_management/pages/password_reset_verify.html', {'email': email})


def set_new_password_view(request):
    """Step 3: User sets their new password"""
    user_id = request.session.get('reset_user_id')
    code_id = request.session.get('reset_code_id')
    
    if not user_id or not code_id:
        messages.error(request, 'Please start the password reset process again.')
        return redirect('request_reset_code')
    
    try:
        user = User.objects.get(id=user_id)
        reset_code = PasswordResetCode.objects.get(id=code_id)
        
        if not reset_code.is_valid():
            messages.error(request, 'Your reset session has expired. Please start again.')
            return redirect('request_reset_code')
        
    except (User.DoesNotExist, PasswordResetCode.DoesNotExist):
        messages.error(request, 'Invalid session. Please start again.')
        return redirect('request_reset_code')
    
    if request.method == 'POST':
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        
        if not password1 or not password2:
            messages.error(request, 'Please fill in both password fields.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif len(password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
        else:
            # Set new password
            user.set_password(password1)
            user.save()
            
            # Mark code as used
            reset_code.is_used = True
            reset_code.save()
            
            # Clear session
            del request.session['reset_email']
            del request.session['reset_user_id']
            del request.session['reset_code_id']
            
            messages.success(request, 'Your password has been reset successfully! You can now log in.')
            return redirect('login')
    
    return render(request, 'security_management/pages/password_reset_new.html')

