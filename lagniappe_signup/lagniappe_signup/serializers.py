from rest_framework import serializers
from events.models import Users, Event, Category, Feedback, Registration
from django.contrib.auth import authenticate

class EventSerializer(serializers.Serializer):
    EventID = serializers.IntegerField(read_only="True")
    OrganizerID = serializers.PrimaryKeyRelatedField(queryset=Users.objects.all())
    CategoryID = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    Title = serializers.CharField(max_length=100)
    Description = serializers.CharField(max_length=500)
    Location = serializers.CharField(max_length=100)
    DateTime = serializers.DateTimeField(required=False, allow_null=True)
    EventStatus = serializers.BooleanField(default=True)

class EventApiSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            "EventID",
            "OrganizerID",
            "CategoryID",
            "Title",
            "Description",
            "Location",
            "DateTime",
            "EventStatus",
        ]
        read_only_fields = [
            "EventID",
            "OrganizerID",
        ]

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True,min_length=8, required=True, style={'input_type': 'password'})
    class Meta:
        model = Users
        fields = ["UserID", "email", "password","first_name", "last_name"]
        extra_kwargs = {'password': {'write_only': True}}
        read_only_fields = ['UserID']

    def validate_email(self, value):
        email = value.strip().lower()
        if Users.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return email

    def create(self, validated_data):
        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "").strip()
        last_name = validated_data.get("last_name", "").strip()
        return Users.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
    )

    def validate(self, attributes):
        email = attributes["email"].strip().lower()
        password = attributes["password"]

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid email or password."
            )

        if not user.is_active:
            raise serializers.ValidationError(
                "This account is inactive."
            )

        attributes["user"] = user
        return attributes