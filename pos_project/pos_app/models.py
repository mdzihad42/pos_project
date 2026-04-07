from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Role-based User Profile
class Profile(models.Model):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Cashier', 'Cashier'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Cashier')
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

# Signal to create or update profile when User is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

# Product Category
class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

# Product Model
class Product(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

# Customer Model
class Customer(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Debt amount
    loyalty_points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.name} ({self.phone})"

# Supplier Model
class Supplier(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return self.name

# Purchase Model (To increase stock)
class Purchase(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.quantity * self.purchase_price

    def __str__(self):
        return f"Purchase of {self.product.name} from {self.supplier.name}"

# Sale Model (Main structure for a sale)
class Sale(models.Model):
    PAYMENT_METHODS = (
        ('Cash', 'Cash'),
        ('Card', 'Card'),
        ('Digital Wallet', 'Digital Wallet (Bkash/Nagad)'),
    )
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    cashier = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='Cash')
    sale_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sale #{self.id} - {self.total_price}"

# Sale Item (Multiple products in one sale)
class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2) # Selling Price
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0) # Cost Price (Snapshot)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

# Movement Logs (Sale vs Purchase history)
class StockMovement(models.Model):
    MOVEMENT_TYPES = (
        ('Purchase', 'Purchase'),
        ('Sale', 'Sale'),
        ('Adjustment', 'Adjustment'),
        ('Return', 'Return'),
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField() # Negative for sales/adjustments, positive for purchases
    date = models.DateTimeField(auto_now_add=True)
    reference_id = models.CharField(max_length=100, blank=True, null=True) # ID of Sale or Purchase

    def __str__(self):
        return f"{self.product.name} - {self.movement_type} ({self.quantity})"

# Signals for Stock Updates
@receiver(post_save, sender=Purchase)
def update_stock_on_purchase(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        product.stock += instance.quantity
        product.save()

        # Log the movement
        StockMovement.objects.create(
            product=product,
            movement_type='Purchase',
            quantity=instance.quantity,
            reference_id=f"Purchase #{instance.id}"
        )

@receiver(post_save, sender=SaleItem)
def update_stock_on_sale_item(sender, instance, created, **kwargs):
    if created:
        product = instance.product
        product.stock -= instance.quantity
        product.save()

        # Log the movement
        StockMovement.objects.create(
            product=product,
            movement_type='Sale',
            quantity=-instance.quantity,
            reference_id=f"Sale #{instance.sale.id}"
        )

# Return Model
class SaleReturn(models.Model):
    sale_item = models.OneToOneField(SaleItem, on_delete=models.CASCADE, related_name='return_record')
    reason = models.TextField(blank=True, null=True)
    return_date = models.DateTimeField(auto_now_add=True)
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Return for {self.sale_item.product.name} (Sale #{self.sale_item.sale.id})"

# Expense Management
class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self): return self.name

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField(auto_now_add=True)
    def __str__(self): return f"{self.category.name} - {self.amount}"

# Signals for Returns (Increase Stock)
@receiver(post_save, sender=SaleReturn)
def update_stock_on_return(sender, instance, created, **kwargs):
    if created:
        product = instance.sale_item.product
        product.stock += instance.sale_item.quantity
        product.save()

        # Log the movement
        StockMovement.objects.create(
            product=product,
            movement_type='Return',
            quantity=instance.sale_item.quantity,
            reference_id=f"Return for Sale #{instance.sale_item.sale.id}"
        )
