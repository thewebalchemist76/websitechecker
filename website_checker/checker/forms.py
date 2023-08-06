# website_checker/checker/forms.py

from django import forms

class WebsiteForm(forms.Form):
    website_urls = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter website URLs'}),
        label='Website URLs',
        max_length=1000,
        help_text='Enter the URLs of the websites you want to check (one URL per line).'
    )
