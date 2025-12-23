from rest_framework import serializers
from materials.models import Materials

class MaterialSerializer(serializers.ModelSerializer):

    slug = serializers.SlugField(read_only=True)
    class Meta:
        model = Materials
        fields = ('name','description','price','image','category','color','slug')