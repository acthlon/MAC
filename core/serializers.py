from rest_framework import serializers

from core.models import Category


class CategorySerializer(serializers.ModelSerializer):
    slug = serializers.SlugField(read_only=True)

    class Meta:
        model = Category
        fields = (
            "target_model",
            "name",
            "icon",
            "image",
            "status",
            "description",
            "slug",
        )

        extra_kwargs = {
            "target_model": {"write_only": True},
            "image": {"write_only": True},
            "status": {"write_only": True},
            "description": {"write_only": True},
        }
