from django.db.models.aggregates import Sum
from .models import Invoice, Transaction
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db import transaction as db_transaction
from decimal import Decimal



class InvoiceDetails(APIView):

    def get(self, request, pk=None):
        if pk is None:
            invoices = Invoice.objects.all().prefetch_related('transactions')
            if not invoices:
                msg = 'No invoice data found'
                return Response({'status': 'error', 'message': msg}, status=status.HTTP_400_BAD_REQUEST)

            response_data = []
            for invoice in invoices:
                transactions = []
                for transaction in invoice.transactions.all():
                    transactions.append({
                        'id': transaction.id,
                        'product': transaction.product,
                        'quantity': transaction.quantity,
                        'price': str(transaction.price),
                        'line_total': str(transaction.line_total)
                    })

                response_data.append({
                    'id': invoice.id,
                    'customer': invoice.customer,
                    'total_amount': str(invoice.total_amount),
                    'total_quantity': invoice.total_quantity,
                    'date': str(invoice.date),
                    'transactions': transactions
                })
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            try:
                invoice = Invoice.objects.get(id=pk)
            except Invoice.DoesNotExist:
                return Response({'error': 'Invoice does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

            invoice_data = {
                'id': invoice.id,
                'customer': invoice.customer,
                'total_amount': str(invoice.total_amount),
                'total_quantity': invoice.total_quantity,
                'date': invoice.date.strftime('%Y-%m-%d'),
                'transactions': []
            }

            for transaction in invoice.transactions.all():
                transaction_data = {
                    'id': transaction.id,
                    'product': transaction.product,
                    'quantity': transaction.quantity,
                    'price': str(transaction.price),
                    'line_total': str(transaction.line_total),
                }
                invoice_data['transactions'].append(transaction_data)
            return Response(invoice_data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        if 'customer' not in data:
            return Response({'customer': 'Customer field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        customer = data['customer']
        if not isinstance(customer, str):
            return Response({'customer': 'Customer field must be a string.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate transactions field
        if 'transactions' not in data:
            return Response({'transactions': 'Transactions field is required.'}, status=status.HTTP_400_BAD_REQUEST)
        transactions = data['transactions']
        if not isinstance(transactions, list) or len(transactions) == 0:
            return Response({'transactions': 'Transactions field must be a non-empty list.'}, status=status.HTTP_400_BAD_REQUEST)

        total_quantity = 0
        total_amount = 0.0
        invoice_transactions = []

        for transaction_data in transactions:
            # Validate product field
            if 'product' not in transaction_data:
                return Response({'product': 'Product field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            product = transaction_data['product']
            if not isinstance(product, str):
                return Response({'product': 'Product field must be a string.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate quantity field
            if 'quantity' not in transaction_data:
                return Response({'quantity': 'Quantity field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            quantity = transaction_data['quantity']
            if not isinstance(quantity, int) or quantity <= 0:
                return Response({'quantity': 'Quantity field must be a positive integer.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate price field
            if 'price' not in transaction_data:
                return Response({'price': 'Price field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            price = transaction_data['price']
            if not isinstance(price, float) and not isinstance(price, int) or price <= 0:
                return Response({'price': 'Price field must be a positive number.'}, status=status.HTTP_400_BAD_REQUEST)


            line_total = quantity * price
            total_quantity += quantity
            total_amount += line_total

            # print(transactions, total_quantity)

            transaction = Transaction(
                product=product,
                quantity=quantity,
                price=price,
                line_total=line_total
            )
            invoice_transactions.append(transaction)
        try:
            with db_transaction.atomic():
                invoice = Invoice(
                    customer=customer,
                    total_quantity=total_quantity,
                    total_amount=total_amount
                )
                invoice.save()
                for transaction in invoice_transactions:
                    transaction.invoice_id = invoice.id
                    transaction.save()
        except Exception as e:
            return Response({'message': f'error is {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        invoice.transactions.set(invoice_transactions)

        return Response({'id': invoice.id}, status=status.HTTP_201_CREATED)

    def delete(self, request, pk=None):

        try:
            invoice = Invoice.objects.get(id=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice does not exist.'}, status=status.HTTP_400_BAD_REQUEST)

        invoice.delete()

        return Response({'message': 'Invoice deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

    def put(self, request, pk=None):
        data = request.data
        if not data:
            return Response({'error': 'No Data Found'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            invoice = Invoice.objects.get(id=pk)
        except Invoice.DoesNotExist:
            return Response({'error': 'Invoice does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with db_transaction.atomic():
                # Update customer if present in the request data
                if 'customer' in data:
                    invoice.customer = data['customer']
                    invoice.save(update_fields=['customer'])

                # Retrieve the existing transactions for the invoice
                existing_transactions = invoice.transactions.all()
                existing_transaction_ids = set(existing_transactions.values_list('id', flat=True))

                new_transactions = data.get('transactions', [])

                # Process each transaction in the request data
                for transaction_data in new_transactions:
                    transaction_id = transaction_data.get('id')

                    if transaction_id:
                        # Update existing transaction
                        try:
                            transaction = existing_transactions.get(id=transaction_id)
                        except Transaction.DoesNotExist:
                            continue

                        # Update the transaction details
                        transaction.product = transaction_data.get('product', transaction.product)
                        transaction.quantity = Decimal(transaction_data.get('quantity', transaction.quantity))
                        transaction.price = Decimal(transaction_data.get('price', transaction.price))
                        transaction.line_total = transaction.quantity * transaction.price
                        transaction.save()

                        # Remove the transaction ID from the existing transaction IDs set
                        existing_transaction_ids.remove(transaction_id)
                    else:
                        # Create a new transaction
                        product = transaction_data.get('product')
                        quantity = Decimal(transaction_data.get('quantity'))
                        price = Decimal(transaction_data.get('price'))

                        if product and quantity and price:
                            line_total = quantity * price
                            transaction = Transaction.objects.create(
                                product=product,
                                quantity=quantity,
                                price=price,
                                line_total=line_total,
                                invoice=invoice
                            )

                # Delete any remaining transactions not present in the request data
                existing_transactions.filter(id__in=existing_transaction_ids).delete()

                # Update the invoice total_quantity and total_amount
                total_quantity = invoice.transactions.aggregate(Sum('quantity'))['quantity__sum']
                invoice.total_quantity = Decimal(total_quantity) if total_quantity else Decimal(0)
                total_line_total = invoice.transactions.aggregate(Sum('line_total'))['line_total__sum']
                invoice.total_amount = Decimal(total_line_total) if total_line_total else Decimal(0)
                invoice.save(update_fields=['total_quantity', 'total_amount'])
        except Exception as e:
            return Response({'message': f'Db transaction issue {e}'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Invoice updated successfully.'}, status=status.HTTP_200_OK)