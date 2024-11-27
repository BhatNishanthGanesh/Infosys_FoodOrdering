from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth.models import Group,User
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm,UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.timezone import datetime
from django.http import HttpResponseRedirect
from django.contrib import messages  
from customer.models import OrderModel

# Login View
def custom_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)  # Log the user in

            # Check if there's a "next" URL to redirect to
            next_url = request.POST.get('next', None)
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                return redirect('dashboard')  # Redirect to your desired page

        else:
            # Invalid login, show an error
            form = AuthenticationForm()
            return render(request, 'account/login.html', {'form': form, 'error': 'Invalid credentials'})

    else:
        form = AuthenticationForm()

    return render(request, 'account/login.html', {'form': form})

def custom_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists. Please choose another one.")
            return redirect('custom_signup')

        if password1 != password2:
            messages.error(request, "Passwords do not match")
            return redirect('custom_signup')

        try:
            # Validate password using Django's built-in validators
            validate_password(password1)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect('custom_signup')

        # Create the user
        user = User.objects.create_user(username=username, email=email, password=password1)
        
        user.is_staff = True  # Allow access to the admin interface
        user.is_superuser = True  # Optionally make them a superuser
        user.save()
        user.backend = 'django.contrib.auth.backends.ModelBackend'

        # Add the user to the 'Staff' group
        staff_group = Group.objects.get(name='Staff')
        user.groups.add(staff_group)

        # Log the user in
        login(request, user)

        return redirect('custom_login')

    return render(request, 'account/signup.html')

# Dashboard View - Only accessible for 'Staff' users
class Dashboard(LoginRequiredMixin, UserPassesTestMixin, View):
    template_name = "restaurant/dashboard.html"

    def get(self, request, *args, **kwargs):
        # Get the current date
        today = datetime.today()
        orders = OrderModel.objects.filter(
            created_on__year=today.year, created_on__month=today.month, created_on__day=today.day)

        # Loop through the orders and add the price value, check if order is not shipped
        unshipped_orders = []
        total_revenue = 0
        for order in orders:
            total_revenue += order.price

            if not order.is_shipped:
                unshipped_orders.append(order)

        # Pass total number of orders and total revenue into the template
        context = {
            'orders': unshipped_orders,
            'total_revenue': total_revenue,
            'total_orders': len(orders)
        }

        return render(request, self.template_name, context)

    def test_func(self):
        # Only users in the 'Staff' group can access the dashboard
        return self.request.user.groups.filter(name='Staff').exists()

# Order Details View - For updating order status (shipped/unshipped)
class OrderDetails(LoginRequiredMixin, UserPassesTestMixin, View):
    def get(self, request, pk, *args, **kwargs):
        order = OrderModel.objects.get(pk=pk)
        context = {
            'order': order
        }

        return render(request, 'restaurant/order-details.html', context)

    def post(self, request, pk, *args, **kwargs):
        order = OrderModel.objects.get(pk=pk)
        order.is_shipped = True
        order.save()

        context = {
            'order': order
        }

        return render(request, 'restaurant/order-details.html', context)

    def test_func(self):
        # Only users in the 'Staff' group can update orders
        return self.request.user.groups.filter(name='Staff').exists()
