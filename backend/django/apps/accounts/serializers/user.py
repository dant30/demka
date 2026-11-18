from django.contrib.auth import get_user_model
from rest_framework import serializers

from core.authentication.passwords import validate_password_strength
from core.utils.validators import validate_kenyan_phone


User = get_user_model()


def _phone_taken(value: str, exclude_pk=None) -> bool:
    qs = User.objects.filter(phone=value)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "full_name", "phone", "role", "is_active",
            "created_at", "last_login",
        )
        read_only_fields = ("id", "created_at", "last_login")

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username", "email", "first_name", "last_name",
            "phone", "role", "password", "confirm_password", "is_active",
        )

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_phone(self, value):
        validate_kenyan_phone(value)
        if _phone_taken(value):
            raise serializers.ValidationError("A user with this phone already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        ok, msg = validate_password_strength(attrs["password"])
        if not ok:
            raise serializers.ValidationError({"password": msg})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "phone", "role", "is_active")

    def validate_phone(self, value):
        validate_kenyan_phone(value)
        if _phone_taken(value, exclude_pk=getattr(self.instance, "pk", None)):
            raise serializers.ValidationError("A user with this phone already exists.")
        return value


class MeSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "first_name", "last_name",
            "full_name", "phone", "role", "is_active",
            "created_at", "last_login",
        )
        read_only_fields = ("id", "username", "role", "created_at", "last_login")

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def validate_phone(self, value):
        validate_kenyan_phone(value)
        if _phone_taken(value, exclude_pk=self.instance.pk if self.instance else None):
            raise serializers.ValidationError("A user with this phone already exists.")
        return value