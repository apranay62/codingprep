from django.urls import path
from .views import InvoiceDetails

urlpatterns = [

    # URL for the GET method
    path('invoices/', InvoiceDetails.as_view(), name='invoice_list'),

    # URL for the POST method
    path('invoices/', InvoiceDetails.as_view(), name='invoice_create'),

    # URL for the GET method with a specific invoice ID
    path('invoices/<int:pk>/', InvoiceDetails.as_view(), name='invoice_detail'),

    # URL for update
    path('invoices/update/<int:pk>/', InvoiceDetails.as_view(), name='invoice_update'),

    # Delete Invoice
    path('invoices/delete/<int:pk>/', InvoiceDetails.as_view(), name='invoice_delete'),

]
