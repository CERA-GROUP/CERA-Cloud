from django.db import models
from cera_data.adcircrun.models import UserProfile
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from localflavor.us.us_states import STATE_CHOICES
from localflavor.us.forms import USStateField
from localflavor.us.forms import USPhoneNumberField

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = {'email', 'first_name', 'last_name'}

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('organization', 'job_title', 'city', 'state', 'phone')

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['organization'].required = True
        self.fields['job_title'].required = False
        self.fields['city'].required = True
        self.fields['state'].required = True
        self.fields['phone'].required = False

class SignupForm(forms.Form):
    contact_firstname = forms.CharField(required=True)
    contact_lastname = forms.CharField(required=True)
    contact_email = forms.EmailField(required=True)
    contact_organization = forms.CharField(required=True)
    contact_jobtitle = forms.CharField(required=False)
    contact_city = forms.CharField(required=True)
    MY_STATE_CHOICES = list(STATE_CHOICES)
    MY_STATE_CHOICES.insert(0, ('', '---------'))
    contact_state = USStateField(required=True, widget=forms.Select(choices=MY_STATE_CHOICES))
    contact_phone = USPhoneNumberField(required=False)
    content = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        self.fields['contact_firstname'].label = "*First name:"
        self.fields['contact_lastname'].label = "*Last name:"
        self.fields['contact_email'].label = "*Email address:"
        self.fields['contact_organization'].label = "*Organization:"
        self.fields['contact_jobtitle'].label = "Job Title:"
        self.fields['contact_city'].label = "*City:"
        self.fields['contact_state'].label = "*State/Province:"
        self.fields['contact_phone'].label = "Phone:"
        self.fields['content'].label = "Message:"

class ContactForm(forms.Form):
    contact_name = forms.CharField(required=True)
    contact_email = forms.EmailField(required=True)
    contact_phone = USPhoneNumberField(required=False)
    content = forms.CharField(required=False, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['contact_name'].label = "*Your name:"
        self.fields['contact_email'].label = "*Email address:"
        self.fields['contact_phone'].label = "Phone:"
        self.fields['content'].label = "*Message:"