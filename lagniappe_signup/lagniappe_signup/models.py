from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator

# Create your models here.
class Users(AbstractUser): # AbstractUser comes with a whole bunch of attributes
    UserID = models.AutoField(("userID"), primary_key=True) # autofield automatically increments an int as a new row is created

    # email

    # password

    # first_name

    # last_name

    # required attributes for AbstractUser. I Set them to blank so they don't get in the way.
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='event_users',  # Custom related_name for reverse accessor
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='event_user_permissions',  # Custom related_name for reverse accessor
        blank=True
    )

class Category(models.Model):
    CategoryID = models.AutoField(("eventID"), primary_key=True)
    Name = models.CharField(("name"), unique=True, max_length=200)

class Event(models.Model):
    EventID = models.AutoField(("eventID"), primary_key=True)
    OrganizerID = models.ForeignKey(Users, on_delete=models.CASCADE)
    CategoryID = models.ForeignKey(Category, on_delete=models.CASCADE)
    Title = models.CharField(("title"), max_length=100)
    Description = models.CharField(("description"), max_length=500)
    Location = models.CharField(("location"), max_length=100)
    DateTime = models.DateTimeField(("datetime"), null=True)
    EventStatus = models.BooleanField(("eventstatus"), default=True)

class Feedback(models.Model):
    FeedbackID = models.AutoField(("feedbackID"), primary_key=True)
    UserID = models.ForeignKey(Users, on_delete=models.CASCADE)
    EventID = models.ForeignKey(Event, on_delete=models.CASCADE)
    Rating = models.IntegerField(("rating"), default=1, validators=[MaxValueValidator(5)])
    Comments = models.CharField(("comments"), max_length=500)
    Date = models.DateTimeField(("date"), auto_now_add=True)

class Registration(models.Model):
    RegistrationID = models.AutoField(("registrationID"), primary_key=True)
    UserID = models.ForeignKey(Users, on_delete=models.CASCADE)
    EventID = models.ForeignKey(Event, on_delete=models.CASCADE)
    RegistrationStatus = models.BooleanField(("registrationstatus"), default=True)
    RegistrationDate = models.DateTimeField(("registrationdate"), auto_now_add=True)

    