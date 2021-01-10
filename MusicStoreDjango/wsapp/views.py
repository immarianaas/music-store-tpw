from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from rest_framework import status
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_jwt.authentication import JSONWebTokenAuthentication

from wsapp.serializers import *
from django.contrib.auth import models
from django.core.exceptions import ObjectDoesNotExist

import json
# Create your views here.

@api_view(['GET'])
def get_manufacturers(request):
    manus = Manufacturer.objects.all()
    ''' # para o caso de haver argumentos:
        # (este exemplo é para apenas buscar um x 
        # numero de elementos
        
    if 'num' in request.GET:
        num = int(request.GET['num'])
        authors = authors[:num]
    '''
    ser = ManufacturerSerializer(manus, many=True)
    return Response(ser.data)

@api_view(['GET'])
def get_manufacturer_by_id(request, id):
    manu = Manufacturer.objects.get(pk=id)
    return Response(ManufacturerSerializer(manu).data)

# -> apenas permite acederes se estiveres autenticado
# @permission_classes((IsAuthenticated, ))
@api_view(['GET'])
def get_items(request):
    # na página dos instrumentos são 'items' que vão aparecer
    # porque os instrumentos em si não tem conhecimento, por exemplo, do preço
    items = Item.objects.all()
    ser = ItemSerializer(items, many=True)
    if request.user.is_authenticated:
        print('authenticated!!')
    else:
        print(request.user)
        # print(request.META['HTTP_AUTHORIZATION'])
        # print(len(request.META['HTTP_AUTHORIZATION']))
        print('not authenticated!')
    return Response(ser.data)

@api_view(['GET'])
def get_item_by_id(request, id):
    item = Item.objects.get(pk=id)
    print(request.user.is_authenticated)
    return Response(ItemSerializer(item).data)

@api_view(['GET'])
def get_instruments_by_manufacturer(request, id):
    items = Item.objects.filter(instrument__manufacturer__pk=id)
    return Response(ItemSerializer(items, many=True).data)

@api_view(['POST'])
def purchase(request):
    if not request.user.is_authenticated:
        # retornar um http de erro
        pass

    person = Person.objects.get(user=request.user)
    item = Item.objects.get(pk=request.data)
    add_to_list('shoppingcart', person, item)

    ser = ItemSerializer(item)
    return Response(ser.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes((IsAuthenticated, ))
def add_to_wishlist(request):
    person = Person.objects.get(user=request.user)
    item = Item.objects.get(pk=request.data)
    if is_item_in_list('wishlist', item, person):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    add_to_list('wishlist', person, item)
    ser = ItemSerializer(item)
    return Response(ser.data, status=status.HTTP_201_CREATED)


def is_item_in_list(list_type, item, user):
    try:
        il = ItemList.objects.get(type=list_type, person=user, items__item=item)
    except ObjectDoesNotExist:
        return False
    return il.items

def add_to_list(list_type, person, item):
    try:
        il = ItemList.objects.get(type=list_type, person=person)
    except ObjectDoesNotExist:
        il = ItemList.objects.create(type=list_type, person=person)

    #print("is item in list?? ", is_item_in_list(list_type, item, person))
    ans = is_item_in_list(list_type, item, person)
    if not ans:
        item_qty = ItemQuantity.objects.create(item=item, quantity=1)
        il.items.add(item_qty)
    else:
        item = ans.get(item__exact=item)
        item.quantity = item.quantity+1
        item.save()

    return
  
def get_curr_person_object(request):    #     person = Person.objects.get(user=request.user)
    u = models.User.objects.get(pk=request.user.id)
    return Person.objects.get(user=u)

@api_view(['PUT'])
def rem_from_wishlist(request):
    # id (request.data) -> item_qty_id
    try:
        item_qty = ItemQuantity.objects.get(pk=request.data)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    item_qty.delete()
    return Response(status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_users_account(request):
    p = get_curr_person_object(request)
    return Response(PersonSerializer(p).data)

@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def update_account(request):
    id = request.data['id']
    try:
        person = Person.objects.get(id=id)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    ser = PersonUpdateSerializer(data=request.data)
    if ser.is_valid():
        person.name = ser.validated_data['name']
        person.contact = ser.validated_data['contact']
        person.gender = ser.validated_data['gender']
        person.save()
        return Response(ser.data)

    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_shopping_cart(request):
    person = Person.objects.get(user=request.user)

    item_lt = ItemList.objects.get(person=person, type='shoppingcart')
    return Response(ItemListSerializer(item_lt).data)

@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def increment_item_at_cart(request):
    try:
        itemqt = ItemQuantity.objects.get(id=request.data)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    itemqt.quantity +=1
    itemqt.save()

    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def decrement_item_at_cart(request):
    try:
        itemqt = ItemQuantity.objects.get(id=request.data)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    itemqt.quantity -= 1;
    if itemqt.quantity > 0:
        itemqt.save()
    else:
        itemqt.delete()

    return Response(status=status.HTTP_202_ACCEPTED)

@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def remove_item_at_cart(request):

    try:
        itemqt = ItemQuantity.objects.get(id=request.data)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    itemqt.delete()

    return Response(status=status.HTTP_202_ACCEPTED)
  
@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_wishlist(request):
    # try:
    lista = ItemList.objects.get(person=Person.objects.get(user=request.user), type='wishlist')
    # except ObjectDoesNotExist:
        # lista = []

    return Response(ItemListSerializer(lista).data)

@api_view(['POST'])
def create_account(request):
    recv = request.data

    try:
        print('here')

        personser = PersonSerializer(data=request.data)
        if personser.is_valid():
            u = models.User.objects.create_user(recv['user']['username'], password=recv['user']['password'])

            name = personser.validated_data['name']
            gen = personser.validated_data['gender']
            cont = personser.validated_data['contact']
            role = personser.validated_data['role']
            Person.objects.create(name=name, gender=gen, contact=cont, user=u, role=role)
            return Response(personser.data, status=status.HTTP_201_CREATED)

    except Exception as err:
        print(err.args)
        return Response(err.__str__(), status=status.HTTP_400_BAD_REQUEST)

    return Response(personser.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def get_my_addresses(request):
    acc = Person.objects.get(user=request.user)
    try:
        addrs = Address.objects.filter(person=acc).all()
    except ObjectDoesNotExist :
        addrs = []
        #return []
    return Response(AddressSerializer(addrs, many=True).data)

@api_view(['DELETE'])
@permission_classes((IsAuthenticated, ))
def delete_address(request, id):
    try:
        address = Address.objects.get(id=id);
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    address.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
@api_view(['PUT'])
@permission_classes((IsAuthenticated, ))
def update_address(request):
    id = request.data['id']
    try:
        address = Address.objects.get(id=id)
    except ObjectDoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    ser = AddressSerializer(data=request.data)
    if ser.is_valid():
        address.street = ser.validated_data['street']
        address.city = ser.validated_data['city']
        address.code = ser.validated_data['code']
        address.country = ser.validated_data['country']
        address.door = ser.validated_data['door']
        address.save()
        return Response(ser.data, status=status.HTTP_202_ACCEPTED)
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def add_address(request): # yet TODO
    recv = request.data
    ser = AddressSerializer(data=recv)
    print(recv)
    print(ser)
    if ser.is_valid():
        street = ser.validated_data['street']
        city = ser.validated_data['city']
        code = ser.validated_data['code']
        country = ser.validated_data['country']
        door = ser.validated_data['door']
        a = Address.objects.create(street=street, city=city, code=code, country=country, door=door, person=Person.objects.get(user = request.user))
        return Response(AddressSerializer(a).data, status=status.HTTP_201_CREATED)

    '''
    if 'POST' in request.method:
        form = AddressForm(request.POST)
        if form.is_valid():
            addr = form.save()
            if temp_addr:
                addr.person = None
                addr.save()
                #if 'temp_addr' not in request.session: #here
                request.session['temp_addr'] = []
                request.session['temp_addr'].append(addr.id)
                print(request.session['temp_addr'])
                return redirect('/account/placeorder')
            return redirect('/account/')

    form = AddressForm()
    '''
    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


