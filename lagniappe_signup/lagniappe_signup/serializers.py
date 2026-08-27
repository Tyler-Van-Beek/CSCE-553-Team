from rest_framework import serializers
from events.models import Users, Event, Category, Feedback, Registration

class EventSerializer(serializers.Serializer):
    EventID = serializers.IntegerField(read_only="True")
    OrganizerID = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())
    CategoryID = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    Title = serializers.CharField(max_length=100)
    Description = serializers.CharField(max_length=500)
    Location = serializers.CharField(max_length=100)
    DateTime = serializers.DateTimeField(required=False, allow_null=True)
    EventStatus = serializers.BooleanField(default=True)