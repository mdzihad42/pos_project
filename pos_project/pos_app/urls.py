from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('', views.dashboard, name='dashboard'),
    
    # Product & Category CRUD
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.product_add, name='product_add'),
    path('products/import/', views.import_products_csv, name='import_products_csv'),
    path('products/edit/<int:pk>/', views.product_edit, name='product_edit'),
    path('products/delete/<int:pk>/', views.product_delete, name='product_delete'),
    
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_add, name='category_add'),
    
    # Customer CRUD
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_add, name='customer_add'),
    
    # Supplier CRUD
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/add/', views.supplier_add, name='supplier_add'),
    
    # Purchase
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/create/', views.purchase_create, name='purchase_create'),
    
    # POS & Sales
    path('pos/', views.pos_view, name='pos'),
    path('pos/add-to-cart/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('pos/cart/', views.cart_view, name='cart'),
    path('pos/cart/update/<int:pk>/', views.update_cart, name='update_cart'),
    path('pos/cart/remove/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),
    path('pos/checkout/', views.checkout, name='checkout'),
    path('pos/invoice/<int:pk>/', views.invoice_view, name='invoice'),
    path('pos/return/<int:pk>/', views.return_item, name='return_item'),
    
    # Reports
    path('reports/sales/', views.sales_report, name='sales_report'),
    path('reports/inventory/', views.inventory_report, name='inventory_report'),
    path('reports/export/csv/', views.export_sales_csv, name='export_sales_csv'),
    path('customers/pay-due/<int:pk>/', views.pay_due, name='pay_due'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/add/', views.expense_add, name='expense_add'),
]
