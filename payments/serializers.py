from rest_framework import serializers
from payments.models import Payment

class PaymentSerializers(serializers.ModelSerializer):
    
    class Meta:
        model = Payment
        fields = ('id', 'payment_method', 'amount', 'currency', 'status', 'reference', 'created_at', 'updated_at')



class InitiatePaymentSerializer(serializers.Serializer):

    method_code = serializers.CharField()
    