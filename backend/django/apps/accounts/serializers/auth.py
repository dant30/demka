from rest_framework import serializers

from core.authentication.passwords import validate_password_strength


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField(
        help_text="Username or phone number.",
    )
    password = serializers.CharField(write_only=True)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    user = serializers.DictField(read_only=True)


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        ok, msg = validate_password_strength(attrs["new_password"])
        if not ok:
            raise serializers.ValidationError({"new_password": msg})
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    phone = serializers.CharField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField(max_length=10)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        ok, msg = validate_password_strength(attrs["new_password"])
        if not ok:
            raise serializers.ValidationError({"new_password": msg})
        return attrs