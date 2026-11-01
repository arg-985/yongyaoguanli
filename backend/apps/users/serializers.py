from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserRegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True, min_length=6)
    phone = serializers.CharField(max_length=20)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='patient', required=False)

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({'password': '两次输入的密码不一致'})
        username = attrs.get('username')
        phone = attrs.get('phone')
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': '该用户名已被注册'})
        if User.objects.filter(phone=phone).exists():
            raise serializers.ValidationError({'phone': '该手机号已被注册'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'password', 'phone', 'email', 'real_name',
            'gender', 'birth_date', 'address', 'emergency_contact',
            'emergency_phone', 'role', 'department', 'title', 'allergies',
            'avatar', 'is_active', 'date_joined',
            'first_name', 'last_name', 'is_staff', 'is_superuser',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password', '') or ''
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', '')
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret.pop('password', None)
        return ret


class UserLoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user = UserSerializer()
