from .models import *
from django.forms import ModelForm, forms
from django import forms
from .models import Comments
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignupForm(UserCreationForm):
    email = forms.EmailField(max_length=200, help_text='Required')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        username = self.cleaned_data.get('username')
        if email and User.objects.filter(email=email).exclude(username=username).exists():
            raise forms.ValidationError(u'Email addresses must be unique.')
        return email


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ('text', 'picture')


class NewPost(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title', 'text', 'picture')


class UpdateProfile(forms.ModelForm):
    username = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    email_confirmation = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_email(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')

        db_email = User.objects.filter(email=email).exclude(username=username).exclude(username=self.instance.username)

        if db_email:
            raise forms.ValidationError(
                'This email address is already in use. Please supply a different emails.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        db_username = User.objects.filter(username=username).exclude(email=self.instance.email)
        if db_username:
            raise forms.ValidationError(
                'This username is already in use. Please supply a different usernames.')
        return username

    def clean_email_confirmation(self):
        email_confirmation = self.cleaned_data['email_confirmation']
        email = self.cleaned_data.get('email')
        if email != email_confirmation:
            raise forms.ValidationError(
                "The two e-mails fields didn't match.")

    def save(self, commit=True):
        user = super(UpdateProfile, self).save(commit=False)
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user
