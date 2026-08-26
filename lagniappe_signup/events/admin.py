from django.contrib import admin
from events.models import Users, Event, Category, Feedback, Registration

# Register your models here.
admin.site.register(Users)
admin.site.register(Event)
admin.site.register(Category)
admin.site.register(Feedback)
admin.site.register(Registration)

