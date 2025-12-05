
from rest_framework import viewsets
from .models import  OrderCreation
from .serializers import  OrderCreationSerializer
from django.db import transaction, DatabaseError
from django.db.utils import OperationalError

from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from rest_framework.response import Response




class OrderCreationViewSet(viewsets.ModelViewSet):
    queryset = OrderCreation.objects.all()
    serializer_class = OrderCreationSerializer

    
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
            # Validar y crear el pedido usando el serializer
                serializer = self.get_serializer(data=request.data)
                serializer.is_valid(raise_exception=True)
                

                # Si la red está caída, guarda el pedido en caché (usa order_number como clave temporal)
                cache_key = f'order_{serializer.validated_data.get("order_number")}'
                cache.set(cache_key, {
                    'product_name': serializer.validated_data.get('product_name'),
                    'quantity': serializer.validated_data.get('quantity'),
                    'order_number': serializer.validated_data.get('order_number'),
                    'creation_date': serializer.validated_data.get('creation_date'),
                    'update_date': serializer.validated_data.get('update_date'),
                    'inventories': serializer.validated_data.get('inventories'),
                }, timeout=7200)  # Timeout
                
                
                print('Pedido guardado en cache:', cache.get(cache_key))
                order = serializer.save()
                
                #cache.delete(cache_key)
                headers = self.get_success_headers(serializer.data)
                return Response(serializer.data, status=201, headers=headers)
    
        except DatabaseError as e:
            # Si ocurre un error, se elimina el pedido de la caché  
            print('Error al guardar el pedido en la base de datos:', e)
            print('El pedido permanece en caché para reintentar más tarde.')
            pass
        except OperationalError as e:
            print('Error operativo al guardar el pedido en la base de datos:', e)
            print('El pedido permanece en caché para reintentar más tarde.')
            pass
        except Exception as e:
            print('Error inesperado al guardar el pedido en la base de datos:', e)
            print('El pedido permanece en caché para reintentar más tarde.')
            pass
        
        return Response("", status=201)

        
    
    def save_order_to_cache(request):
        order_data = request.data
        cache.set(f'order_{order_data["id"]}', order_data, timeout=600)
        return JsonResponse({"message": "Order saved in cache"})
    
    def sync_cached_orders():
        for key in cache.keys('order_*'):
            order_data = cache.get(key)
            if order_data:
                # Guardar el pedido en la base de datos
                OrderCreation.objects.create(**order_data)
                cache.delete(key)  # Elimina la entrada de la caché después de sincronizarla


@require_http_methods(["GET", "HEAD"])
def health_check(request):

    res = JsonResponse({"status": "ok"})
    return _no_store(res)
