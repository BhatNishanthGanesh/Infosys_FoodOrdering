import json
from django.shortcuts import render, redirect
from django.views import View
from django.db.models import Q
from django.core.mail import send_mail
from .models import MenuItem, Category, OrderModel


class Landing(View):
    def get(self, request, *args, **kwargs):
       return render(request, 'customer/LandingPage.html', {'is_index': True})

class Home(View):
    def get(self, request, *args, **kwargs):
        menu_items = MenuItem.objects.all()
        carousel_items = [
            {"image": "bur.jpg", "alt": "Burger", "title": "Welcome to Online Food Delivery", "description": "Explore your favorite restaurants and dishes!"},
            {"image": "pas.jpg", "alt": "Pasta", "title": "Delicious Pasta", "description": "Try our freshly made pasta dishes!"},
            {"image": "pizz.jpg", "alt": "Pizza", "title": "Authentic Pizza", "description": "Enjoy the best pizza in town!"},
        ]
        context = {
            'menu_items': menu_items,
            'carousel_items': carousel_items,
        }
        return render(request, 'customer/homePage.html', context)



class About(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'customer/about.html')


class Order(View):
    def get(self, request, *args, **kwargs):
        # get every item from each category
        appetizers = MenuItem.objects.filter(
            category__name__contains='Appetizer')
        entres = MenuItem.objects.filter(category__name__contains='Entre')
        desserts = MenuItem.objects.filter(category__name__contains='Dessert')
        drinks = MenuItem.objects.filter(category__name__contains='Drink')

        # pass into context
        context = {
            'appetizers': appetizers,
            'entres': entres,
            'desserts': desserts,
            'drinks': drinks,
        }

        # render the template
        return render(request, 'customer/order.html', context)

    def post(self, request, *args, **kwargs):
        name = request.POST.get('name')
        email = request.POST.get('email')
        street = request.POST.get('street')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip')

        order_items = {'items': []}
        items = request.POST.getlist('items[]')

        price = 0
        item_ids = []

        for item in items:
            try:
                menu_item = MenuItem.objects.get(pk=int(item))
                item_data = {
                    'id': menu_item.pk,
                    'name': menu_item.name,
                    'price': menu_item.price
                }
                order_items['items'].append(item_data)
                price += menu_item.price
                item_ids.append(menu_item.pk)
            except MenuItem.DoesNotExist:
                continue  # You can handle this case differently if needed
            except MenuItem.MultipleObjectsReturned:
                continue  # Handle the case where multiple items are found

        order = OrderModel.objects.create(
            price=price,
            name=name,
            email=email,
            street=street,
            city=city,
            state=state,
            zip_code=zip_code
        )
        order.items.add(*item_ids)

        # After everything is done, send confirmation email to the user
        body = ('Thank you for your order! Your food is being made and will be delivered soon!\n'
                f'Your total: {price}\n'
                'Thank you again for your order!')

        send_mail(
            'Thank You For Your Order!',
            body,
            'example@example.com',
            [email],
            fail_silently=False
        )

        context = {
            'items': order_items['items'],
            'price': price
        }

        return redirect('order-confirmation', pk=order.pk)



class OrderConfirmation(View):
    def get(self, request, pk, *args, **kwargs):
        order = OrderModel.objects.get(pk=pk)

        context = {
            'pk': order.pk,
            'items': order.items,
            'price': order.price,
        }

        return render(request, 'customer/order_confirmation.html', context)

    def post(self, request, pk, *args, **kwargs):
        data = json.loads(request.body)

        if data['isPaid']:
            order = OrderModel.objects.get(pk=pk)
            order.is_paid = True
            order.save()

        return redirect('payment-confirmation')


class OrderPayConfirmation(View):
    def get(self, request, *args, **kwargs):
        return render(request, 'customer/order_pay_confirmation.html')


class Menu(View):
    def get(self, request, *args, **kwargs):
        menu_items = MenuItem.objects.all()

        context = {
            'menu_items': menu_items
        }

        return render(request, 'customer/menu.html', context)


class MenuSearch(View):
    def get(self, request, *args, **kwargs):
        query = self.request.GET.get("q")

        menu_items = MenuItem.objects.filter(
            Q(name__icontains=query) |
            Q(price__icontains=query) |
            Q(description__icontains=query)
        )

        context = {
            'menu_items': menu_items
        }

        return render(request, 'customer/menu.html', context)
