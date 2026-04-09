from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.db.models import Sum, Count, F
from django.utils import timezone
from .models import Product, Category, Customer, Supplier, Purchase, Sale, SaleItem, StockMovement, Profile, Expense, ExpenseCategory, SaleReturn
import csv
from django.http import HttpResponse
from datetime import datetime, timedelta
import json
from decimal import Decimal
import io
from .models import Product, Category, Customer, Supplier, Purchase, Sale, SaleItem, StockMovement, Profile, Expense, ExpenseCategory, SaleReturn, SystemSetting, Shift, HoldSale
from django.http import JsonResponse


# ================= AUTHENTICATION =================

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('login')

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Account created successfully. Please login.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

# Helper to get system settings
def get_settings():
    settings = SystemSetting.objects.first()
    if not settings:
        settings = SystemSetting.objects.create(shop_name="SmartPOS")
    return settings

# ================= DASHBOARD =================

@login_required
def dashboard(request):
    today = timezone.now().date()
    total_sales_today = Sale.objects.filter(sale_date__date=today).aggregate(Sum('total_price'))['total_price__sum'] or 0
    total_sales_count = Sale.objects.count()
    low_stock_products = Product.objects.filter(stock__lte=10)
    top_selling = SaleItem.objects.values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

    sales_data = []
    profit_data = []
    labels = []
    total_profit_today = 0
    
    # Statistics for Profit
    last_7_days = [(timezone.now() - timedelta(days=i)).date() for i in range(6, -1, -1)]
    today_sales = Sale.objects.filter(sale_date__date=today)
    for sale in today_sales:
        for item in sale.items.all():
            total_profit_today += (item.unit_price - item.purchase_price) * item.quantity

    for day in last_7_days:
        daily_sales = Sale.objects.filter(sale_date__date=day)
        daily_sum = daily_sales.aggregate(Sum('total_price'))['total_price__sum'] or 0
        
        # Calculate daily profit
        daily_profit = 0
        for s in daily_sales:
            for itm in s.items.all():
                daily_profit += (itm.unit_price - itm.purchase_price) * itm.quantity
        
        sales_data.append(float(daily_sum))
        profit_data.append(float(daily_profit))
        labels.append(day.strftime("%b %d"))

    # Statistics for Expenses
    total_expenses_today = Expense.objects.filter(date=today).aggregate(Sum('amount'))['amount__sum'] or 0
    net_cash = total_sales_today - total_expenses_today

    context = {
        'total_sales_today': total_sales_today,
        'total_profit_today': total_profit_today,
        'total_expenses_today': total_expenses_today,
        'net_cash': net_cash,
        'total_sales_count': total_sales_count,
        'low_stock_count': low_stock_products.count(),
        'low_stock_products': low_stock_products[:5],
        'top_selling': top_selling,
        'chart_labels': json.dumps(labels),
        'chart_data': json.dumps(sales_data),
        'profit_chart_data': json.dumps(profit_data),
        'settings': get_settings(),
    }
    return render(request, 'pos/dashboard.html', context)

# ================= PRODUCT CRUD =================

@login_required
def product_list(request):
    products = Product.objects.all().select_related('category')
    return render(request, 'inventory/product_list.html', {'products': products})

@login_required
def product_add(request):
    if request.method == 'POST':
        name = request.POST['name']
        category_id = request.POST['category']
        price = request.POST['price']
        stock = request.POST.get('stock', 0)
        barcode = request.POST.get('barcode', '')
        image = request.FILES.get('image')
        
        category = Category.objects.get(id=category_id)
        Product.objects.create(name=name, category=category, price=price, stock=stock, barcode=barcode, image=image)
        messages.success(request, "Product added successfully.")
        return redirect('product_list')
    
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {'categories': categories})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.category = Category.objects.get(id=request.POST['category'])
        product.price = request.POST['price']
        product.stock = request.POST.get('stock', product.stock)
        product.barcode = request.POST.get('barcode', product.barcode)
        if request.FILES.get('image'):
            product.image = request.FILES.get('image')
        product.save()
        messages.success(request, "Product updated.")
        return redirect('product_list')
    
    categories = Category.objects.all()
    return render(request, 'inventory/product_form.html', {'product': product, 'categories': categories})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, "Product deleted.")
    return redirect('product_list')

# ================= CATEGORY, CUSTOMER, SUPPLIER (Simplified CRUD) =================

@login_required
def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

@login_required
def category_add(request):
    if request.method == 'POST':
        Category.objects.create(name=request.POST['name'], description=request.POST.get('description'))
        return redirect('category_list')
    return render(request, 'inventory/category_form.html')

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'pos/customer_list.html', {'customers': customers})

@login_required
def customer_add(request):
    if request.method == 'POST':
        Customer.objects.create(name=request.POST['name'], phone=request.POST['phone'], email=request.POST.get('email'), address=request.POST.get('address'))
        return redirect('customer_list')
    return render(request, 'pos/customer_form.html')

@login_required
def supplier_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_add(request):
    if request.method == 'POST':
        Supplier.objects.create(name=request.POST['name'], phone=request.POST['phone'])
        return redirect('supplier_list')
    return render(request, 'inventory/supplier_form.html')

# ================= PURCHASE =================

@login_required
def purchase_list(request):
    purchases = Purchase.objects.all().order_by('-purchase_date')
    return render(request, 'inventory/purchase_list.html', {'purchases': purchases})

@login_required
def purchase_create(request):
    if request.method == 'POST':
        product = Product.objects.get(id=request.POST['product'])
        supplier = Supplier.objects.get(id=request.POST['supplier'])
        qty = int(request.POST['quantity'])
        price = request.POST['purchase_price']
        
        Purchase.objects.create(product=product, supplier=supplier, quantity=qty, purchase_price=price)
        messages.success(request, f"Recorded purchase for {product.name}.")
        return redirect('purchase_list')
    
    products = Product.objects.all()
    suppliers = Supplier.objects.all()
    return render(request, 'inventory/purchase_form.html', {'products': products, 'suppliers': suppliers})

# ================= POS SYSTEM =================

@login_required
def pos_view(request):
    query = request.GET.get('search', '')
    category_id = request.GET.get('category')
    
    products = Product.objects.all()
    if query:
        # Auto-add if exact barcode match
        barcode_product = Product.objects.filter(barcode=query).first()
        if barcode_product:
            return redirect('add_to_cart', pk=barcode_product.id)
            
        products = products.filter(name__icontains=query) | products.filter(barcode=query)
    if category_id:
        products = products.filter(category_id=category_id)
        
    categories = Category.objects.all()
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = 0
    for product_id, item_data in cart.items():
        item_total = float(item_data['price']) * item_data['quantity']
        subtotal += item_total
        cart_items.append({'id': product_id, 'total_item_price': item_total, **item_data})
    
    settings = get_settings()
    tax_rate = float(settings.tax_percentage) / 100
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    customers = Customer.objects.all()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'cart_items': cart_items,
            'subtotal': subtotal,
            'tax': tax,
            'total': total,
            'currency': settings.currency_symbol
        })

    context = {
        'products': products,
        'categories': categories,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax': tax,
        'total': total,
        'customers': customers,
        'settings': settings,
    }
    return render(request, 'pos/pos.html', context)

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    
    # Backend Stock Check
    if product.stock <= 0:
        if is_ajax: return JsonResponse({'status': 'error', 'message': f"Sorry, {product.name} is out of stock."})
        messages.error(request, f"Sorry, {product.name} is out of stock.")
        return redirect('pos')

    cart = request.session.get('cart', {})
    p_id = str(product.id)
    
    if p_id in cart:
        if cart[p_id]['quantity'] >= product.stock:
            if is_ajax: return JsonResponse({'status': 'error', 'message': f"Stock limit reached for {product.name}."})
            messages.warning(request, f"Cannot add more of {product.name}. Stock limit reached.")
            return redirect('pos')
        cart[p_id]['quantity'] += 1
    else:
        cart[p_id] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': 1,
            'image': product.image.url if product.image else '/static/img/no-image.png'
        }
    
    request.session['cart'] = cart
    
    if is_ajax:
        return JsonResponse({'status': 'success', 'message': f"{product.name} added to cart."})
        
    messages.success(request, f"{product.name} added to cart.")
    return redirect('pos')

@login_required
def cart_view(request):
    # This might be used if separate cart page is needed, or just redirect to POS
    return redirect('pos')

@login_required
def update_cart(request, pk):
    cart = request.session.get('cart', {})
    p_id = str(pk)
    if p_id in cart:
        action = request.POST.get('action')
        if action == 'plus':
            cart[p_id]['quantity'] += 1
        elif action == 'minus':
            cart[p_id]['quantity'] -= 1
            if cart[p_id]['quantity'] <= 0:
                del cart[p_id]
        elif action == 'remove':
            del cart[p_id]
            
    request.session['cart'] = cart
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('pos')

@login_required
def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    p_id = str(pk)
    if p_id in cart:
        del cart[p_id]
    request.session['cart'] = cart
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    return redirect('pos')

@login_required
def checkout(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Cart is empty.")
            return redirect('pos')
            
        # Final Stock Verification before processing payment
        for p_id, item in cart.items():
            product = get_object_or_404(Product, id=p_id)
            if product.stock < item['quantity']:
                messages.error(request, f"Insufficient stock for {product.name}. Available: {product.stock}")
                return redirect('pos')

        customer_id = request.POST.get('customer')
        payment_method = request.POST.get('payment_method', 'Cash')
        discount = float(request.POST.get('discount', 0))
        amount_paid = float(request.POST.get('amount_paid', 0))
        
        customer = None
        customer = None
        if customer_id:
            customer = Customer.objects.get(id=customer_id)
            
        settings = get_settings()
        subtotal = sum(item['price'] * item['quantity'] for item in cart.values())
        tax_rate = float(settings.tax_percentage) / 100
        tax = subtotal * tax_rate
        total = subtotal + tax - discount
        
        balance_due = total - amount_paid
        if customer:
            if balance_due > 0:
                customer.balance += Decimal(str(balance_due))
            
            # Award Loyalty Points (1 point per 20 spent)
            points_earned = int(total // 20)
            customer.loyalty_points += points_earned
            customer.save()
            
        sale = Sale.objects.create(
            customer=customer,
            cashier=request.user,
            subtotal=subtotal,
            tax=tax,
            discount=discount,
            total_price=total,
            amount_paid=amount_paid,
            balance_due=max(0, balance_due),
            payment_method=payment_method
        )
        
        for p_id, item in cart.items():
            product = Product.objects.get(id=p_id)
            SaleItem.objects.create(
                sale=sale,
                product=product,
                quantity=item['quantity'],
                unit_price=item['price'],
                purchase_price=product.price,
                total_price=item['price'] * item['quantity']
            )
            
        request.session['cart'] = {}
        messages.success(request, f"Sale completed! Total: {total}")
        return redirect('invoice', pk=sale.id)
    
    return redirect('pos')

@login_required
def invoice_view(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    return render(request, 'pos/invoice.html', {'sale': sale})

@login_required
def return_item(request, pk):
    # pk is SaleItemID
    item = get_object_or_404(SaleItem, pk=pk)
    
    # Check if already returned
    if hasattr(item, 'return_record'):
        messages.warning(request, f"Product {item.product.name} has already been returned.")
        return redirect('invoice', pk=item.sale.id)
    
    
    SaleReturn.objects.create(
        sale_item=item,
        reason="Customer Return", # Optional: can be a form input
        refund_amount=item.total_price
    )
    
    messages.success(request, f"Item {item.product.name} returned successfully. Stock updated.")
    return redirect('invoice', pk=item.sale.id)

# ================= REPORTS =================

@login_required
def sales_report(request):
    sales = Sale.objects.all().order_by('-sale_date')
    return render(request, 'reports/sales_report.html', {'sales': sales})

@login_required
def inventory_report(request):
    products = Product.objects.all()
    # Adding movement summary
    for p in products:
        p.purchased = StockMovement.objects.filter(product=p, movement_type='Purchase').aggregate(Sum('quantity'))['quantity__sum'] or 0
        p.sold = abs(StockMovement.objects.filter(product=p, movement_type='Sale').aggregate(Sum('quantity'))['quantity__sum'] or 0)
        
    return render(request, 'reports/inventory_report.html', {'products': products})

@login_required
def export_sales_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Sale ID', 'Date', 'Customer', 'Total', 'Payment Method', 'Cashier'])
    
    sales = Sale.objects.all()
    for sale in sales:
        writer.writerow([sale.id, sale.sale_date, sale.customer.name if sale.customer else 'Guest', sale.total_price, sale.payment_method, sale.cashier.username])
        
    return response

@login_required
def pay_due(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        if amount > 0:
            customer.balance -= amount
            customer.save()
            messages.success(request, f"Collected ${amount} from {customer.name}. New Balance: ${customer.balance}")
        return redirect('customer_list')
    return render(request, 'pos/pay_due.html', {'customer': customer})

@login_required
def import_products_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid CSV file.")
            return redirect('product_list')
        
        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            next(io_string) # Skip header row
            
            for row in csv.reader(io_string, delimiter=','):
                # row structure: Name, Category, Price, Stock, Barcode
                category_name = row[1]
                category, _ = Category.objects.get_or_create(name=category_name)
                
                Product.objects.update_or_create(
                    name=row[0],
                    defaults={
                        'category': category,
                        'price': Decimal(row[2]),
                        'stock': int(row[3]),
                        'barcode': row[4]
                    }
                )
            messages.success(request, "Products imported successfully!")
        except Exception as e:
            messages.error(request, f"Error processing file: {e}")
            
        return redirect('product_list')
    return render(request, 'pos/import_products.html')

@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    return render(request, 'pos/expense_list.html', {'expenses': expenses})

@login_required
def expense_add(request):
    if request.method == 'POST':
        category_id = request.POST.get('category')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        
        category = ExpenseCategory.objects.get(id=category_id)
        Expense.objects.create(category=category, amount=amount, description=description)
        messages.success(request, "Expense recorded successfully.")
        return redirect('expense_list')
    
    categories = ExpenseCategory.objects.all()
    # Auto-create some categories if empty
    if not categories.exists():
        ExpenseCategory.objects.get_or_create(name="Rent")
        ExpenseCategory.objects.get_or_create(name="Electricity")
        ExpenseCategory.objects.get_or_create(name="Salary")
        categories = ExpenseCategory.objects.all()
        
    return render(request, 'pos/expense_form.html', {'categories': categories})

@login_required
def quick_add_customer(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        
        if name and phone:
            customer = Customer.objects.create(name=name, phone=phone, email=email, address=address)
            return JsonResponse({'status': 'success', 'id': customer.id, 'name': customer.name, 'phone': customer.phone})
        return JsonResponse({'status': 'error', 'message': 'Name and Phone are required.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

# ================= SHIFT MANAGEMENT =================

@login_required
def start_shift(request):
    if request.method == 'POST':
        balance = request.POST.get('opening_balance', 0)
        Shift.objects.create(user=request.user, opening_balance=balance)
        messages.success(request, "Shift started successfully.")
        return redirect('dashboard')
    return render(request, 'pos/start_shift.html')

@login_required
def end_shift(request, pk):
    shift = get_object_or_404(Shift, pk=pk)
    if request.method == 'POST':
        shift.closing_balance = request.POST.get('closing_balance')
        shift.end_time = timezone.now()
        shift.status = 'Closed'
        shift.save()
        messages.success(request, "Shift ended successfully.")
        return redirect('dashboard')
    return render(request, 'pos/end_shift.html', {'shift': shift})

# ================= HOLD / RESUME SALE =================

@login_required
def hold_sale(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            return JsonResponse({'status': 'error', 'message': 'Cart is empty.'})
            
        customer_id = request.POST.get('customer')
        customer = None
        if customer_id:
            customer = Customer.objects.get(id=customer_id)
            
        HoldSale.objects.create(
            user=request.user,
            customer=customer,
            cart_data=json.dumps(cart),
            note=request.POST.get('note', '')
        )
        request.session['cart'] = {}
        return JsonResponse({'status': 'success', 'message': 'Sale put on hold.'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})

@login_required
def resume_sale(request, pk):
    held_sale = get_object_or_404(HoldSale, pk=pk)
    request.session['cart'] = json.loads(held_sale.cart_data)
    held_sale.delete()
    messages.success(request, "Sale resumed.")
    return redirect('pos')

@login_required
def held_sales_list(request):
    held_sales = HoldSale.objects.filter(user=request.user)
    return render(request, 'pos/held_sales.html', {'held_sales': held_sales})

@login_required
def system_settings_view(request):
    if request.user.profile.role != 'Admin':
        messages.error(request, "Only admins can access settings.")
        return redirect('dashboard')
        
    settings = get_settings()
    if request.method == 'POST':
        settings.shop_name = request.POST.get('shop_name')
        settings.tax_percentage = request.POST.get('tax_percentage')
        settings.currency_symbol = request.POST.get('currency_symbol')
        settings.low_stock_threshold = request.POST.get('low_stock_threshold')
        if request.FILES.get('shop_logo'):
            settings.shop_logo = request.FILES.get('shop_logo')
        settings.save()
        messages.success(request, "Settings updated successfully!")
        return redirect('system_settings')
        
    return render(request, 'pos/settings.html', {'settings': settings})
