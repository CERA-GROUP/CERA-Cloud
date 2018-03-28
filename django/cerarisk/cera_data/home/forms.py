# contains all hidden input fields that need to be sent back from the server to the client
from django import forms
from django.forms.widgets import HiddenInput

# fields without an initial value or specific values per site are defined in the form dictionary in views.py when defining the form (tz, ne, sw)
class CeraProForm(forms.Form):

    zoom = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    ne = forms.CharField(required=False, widget=forms.HiddenInput())
    sw = forms.CharField(required=False, widget=forms.HiddenInput())
    maptools = forms.CharField(required=False, max_length=5, widget=forms.HiddenInput(), initial='1')
    anilayer = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    # marks the webpage as very first page; after that it is always 0
    isdefault = forms.CharField(required=False, max_length=1, widget=forms.HiddenInput(), initial='1')
    is_storm = forms.CharField(required=False, max_length=1, widget=forms.HiddenInput(), initial='0')
    has_invest_or_subtrack = forms.CharField(required=False, max_length=1, widget=forms.HiddenInput(), initial='0')
    day = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    time = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    com = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    year = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    storm = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    advisory = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    track = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    tz = forms.CharField(required=False, max_length=4, widget=forms.HiddenInput(), initial='')
    panel = forms.CharField(required=False, max_length=1, widget=forms.HiddenInput(), initial='!1')
    # disclaimer accept button (to not show the disclaimer when accept has been pressed without cookies)
    accept = forms.CharField(required=False, max_length=1, widget=forms.HiddenInput(), initial='0')
    unit = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    query_coord = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    queryonoff = forms.CharField(required=False, widget=forms.HiddenInput(), initial='0')
    stationid = forms.CharField(required=False, widget=forms.HiddenInput(), initial='')
    track_labels = forms.CharField(required=False, widget=forms.HiddenInput(), initial='!1')
    cera = forms.CharField(required=False, widget=forms.HiddenInput(), initial='!pub')
    scrollpos = forms.CharField(required=False, widget=forms.HiddenInput(), initial='0')

    def clean(self, initial = {}):
        cleaned_data = super(CeraProForm, self).clean()

        # if data is not provided for some fields and those fields have an
        # initial value, then set the values to the initial values (clean deletes the initial values by default)
        for name in self.fields:
            if not self[name].html_name in self.data and initial.has_key(name):
                cleaned_data[name] = initial[name]
            elif not self[name].html_name in self.data and self.fields[name].initial is not None:
                cleaned_data[name] = self.fields[name].initial
        return cleaned_data

