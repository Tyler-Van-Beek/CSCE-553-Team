from django import forms 
from events.models import Event, Registration, Users, Feedback

class EventForm(forms.ModelForm):
    class Meta:
        model = Event

        fields = [
            'OrganizerID',
            'CategoryID',
            'Title',
            'Description',
            'Location',
            'DateTime',
            'EventStatus',
        ]

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['UserID', 'EventID']

        def __init__(self, *args, **kwargs):
            # Extract the event from kwargs
            self.event = kwargs.pop('event', None)  
            super().__init__(*args, **kwargs)  

            # If the event is provided, set the initial value for the 'EventID' field
            if self.event:
                self.fields['EventID'].initial = self.event  # Pre-set the EventID field with the event

class SignUpForm(forms.ModelForm):

    class Meta:
        model = Users
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password',
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"]) 
        if commit:
            user.save()
        return user

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = [
            'UserID',
            'EventID',
            'Rating',
            'Comments',
        ]