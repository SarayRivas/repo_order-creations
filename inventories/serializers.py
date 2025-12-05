from rest_framework import serializers
from . import models


class OrderCreationSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id_order_creation', 'order_number', 'status','quantity', 'creation_date', 'update_date', 'product_name', 'inventories',)
        model = models.OrderCreation

