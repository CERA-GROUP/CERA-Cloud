from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from cera_data.accounts.forms import SignupForm, ContactForm, UserForm, ProfileForm
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.core.mail import send_mail
from django.urls import reverse

###########################################
#redirect CERA default page depending on login

###########################################
#show the profile overview
@login_required
def profile(request):
  return render(request, 'accounts/profile.html', {'user': request.user})
#  return render(request, reverse('profile').lstrip('/'), {'user': request.user})

###########################################
#edit the profile
@login_required
def profile_edit(request):
  if request.method == 'POST':
    user_form = UserForm(request.POST, instance=request.user)
    profile_form = ProfileForm(request.POST, instance=request.user.userprofile)
    if user_form.is_valid() and profile_form.is_valid() and user_form.cleaned_data and profile_form.cleaned_data:
      user_form.save()
      profile_form.save()
      return redirect(reverse('profile'))

    # validation error, re-open the form with error messages embedded
    return render(request, 'accounts/profile_edit.html', {'user_form': user_form, 'profile_form': profile_form, 'user': request.user})

  # GET request, initializing the blank form
  user_form = UserForm(instance=request.user)
  profile_form = ProfileForm(instance=request.user.userprofile)
  return render(request, 'accounts/profile_edit.html', {'user_form': user_form, 'profile_form': profile_form, 'user': request.user})

###########################################
# new users login request (email)
def signup(request):
  form_class = SignupForm

  if request.method == 'POST':
    form = form_class(data=request.POST)

    if form.is_valid():
      # email the profile with the contact information
      template = get_template('accounts/signup_template.txt')
      context = {
                'contact_firstname': request.POST.get('contact_firstname', ''),
                'contact_lastname': request.POST.get('contact_lastname', ''),
                'contact_email': request.POST.get('contact_email', ''),
                'contact_organization': request.POST.get('contact_organization', ''),
                'contact_jobtitle': request.POST.get('contact_jobtitle', ''),
                'contact_city': request.POST.get('contact_city', ''),
                'contact_state': request.POST.get('contact_state', ''),
                'contact_phone': request.POST.get('contact_phone', ''),
                'form_content': request.POST.get('content', '')
            }
      content = template.render(context)

      email = EmailMessage(
                "CERA: new sign-up request",
                content,
                settings.DEFAULT_FROM_EMAIL,
                ['ckaiser@cct.lsu.edu'],
                headers = {'Reply-To': 'contact_email' }
            )
      email.send()
      return redirect(reverse('contact_done'))

    # validation error, re-open the form with error messages embedded
    return render(request, 'accounts/signup.html', {'form': form })

  # GET request, initializing the blank form
  form = form_class()
  return render(request, 'accounts/signup.html', {'form': form })

###########################################
# contact message (email)
def contact(request):
  form_class = ContactForm

  if request.method == 'POST':
    form = form_class(data=request.POST)

    if form.is_valid():
      # email the profile with the contact information
      template = get_template('accounts/contact_template.txt')
      context = {
                'contact_name': request.POST.get('contact_name', ''),
                'contact_email': request.POST.get('contact_email', ''),
                'contact_phone': request.POST.get('contact_phone', ''),
                'form_content': request.POST.get('content', '')
            }
      content = template.render(context)

      email = EmailMessage(
                "CERA: new contact message",
                content,
                settings.DEFAULT_FROM_EMAIL,
                ['ckaiser@cct.lsu.edu'],
                headers = {'Reply-To': 'contact_email' }
            )
      email.send()
      return redirect(reverse('contact_done'))

    # validation error, re-open the form with error messages embedded
    return render(request, 'accounts/contact.html', {'form': form })

  # GET request, initializing the blank form
  form = form_class()
  return render(request, 'accounts/contact.html', {'form': form })

###########################################
# success message for signup + contact form
def contact_done(request):
  return render(request, 'accounts/contact_done.html')

###########################################
@login_required
def password_change(request):
  if request.method == 'POST':
    form = PasswordChangeForm(data=request.POST, user=request.user)
    if form.is_valid():
      form.save()
      update_session_auth_hash(request, form.user)
      return redirect(reverse('password_change_done'))
    else:
      # validation error, re-open the form with error messages embedded
      return render(request, 'accounts/password_change.html', {'form': form })
  else:
    form = PasswordChangeForm(user=request.user)
    return render (request, 'accounts/password_change.html', {'form':form})
