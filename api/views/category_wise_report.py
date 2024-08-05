# from rest_framework.views import APIView
# from rest_framework.response import Response
# from bill.models import Bill, BillItem
# from datetime import datetime



# class CategoryWiseSaleAPIView(APIView):
#     def get(self, request):
#         all_queryset = Bill.objects.filter(status=True, is_deleted=False)
#         from_date_str = request.GET.get('fromDate')
#         to_date_str = request.GET.get('toDate')

#         from_date = datetime.strptime(from_date_str, '%Y-%m-%d') if from_date_str else None
#         to_date = datetime.strptime(to_date_str, '%Y-%m-%d') if to_date_str else None

#         if from_date and to_date:
#             queryset = all_queryset.filter(transaction_date__range=(from_date, to_date))
#         else:
#             today_date = datetime.today().strftime("%Y-%m-%d")
#             queryset = all_queryset.filter(transaction_date__range=(today_date, today_date))

#         sales_type = request.GET.get('sales_type', 'all')
        
#         if sales_type == "complimentary":
#             queryset = queryset.filter(payment_mode="complimentary")
#         elif sales_type == "others":
#             queryset = queryset.exclude(payment_mode="complimentary")
        
#         budclass_data = {}
        
#         for bill in queryset:
#             for item in bill.bill_items.all():
#                 product_title = item.product.title
#                 budclass = item.product.category.title
#                 budclass_items = budclass_data.get(budclass, {'items': [], 'amount_total': 0, 'quantity_total': 0})
                
#                 item_exists = next((x for x in budclass_items['items'] if x['name'] == product_title and x['rate'] == item.rate), None)
                
#                 if not item_exists:
#                     budclass_items['items'].append({
#                         'name': product_title,
#                         'quantity': item.product_quantity,
#                         'amount': item.amount,
#                         'unit': item.unit_title,
#                         'rate': item.rate
#                     })
#                     budclass_items['amount_total'] += item.amount
#                     budclass_items['quantity_total'] += item.product_quantity
#                 else:
#                     item_exists['quantity'] += item.product_quantity
#                     item_exists['amount'] += item.amount
#                     budclass_items['amount_total'] += item.amount
#                     budclass_items['quantity_total'] += item.product_quantity
                
#                 budclass_data[budclass] = budclass_items
        
#         for k, v in budclass_data.items():
#             v['items'] = sorted(v['items'], key=lambda x: x['quantity'], reverse=True)
        
#         return Response(budclass_data, 200)


from datetime import datetime
from rest_framework.response import Response
from rest_framework.views import APIView
from bill.models import Bill

class CategoryWiseSaleAPIView(APIView):
    def post(self, request):
        branch = request.data['branch']

        all_queryset = Bill.objects.filter(status=True, is_deleted=False, branch__id=branch)
        from_date_str = request.GET.get('fromDate')
        to_date_str = request.GET.get('toDate')

        from_date = datetime.strptime(from_date_str, '%Y-%m-%d') if from_date_str else None
        to_date = datetime.strptime(to_date_str, '%Y-%m-%d') if to_date_str else None

        if from_date and to_date:
            queryset = all_queryset.filter(transaction_date__range=(from_date.date(), to_date.date()))
        else:
            today_date = datetime.today().date()
            queryset = all_queryset.filter(transaction_date__range=(today_date, today_date))

        sales_type = request.GET.get('sales_type', 'all')
        
        if sales_type == "complimentary":
            queryset = queryset.filter(payment_mode="complimentary")
        elif sales_type == "others":
            queryset = queryset.exclude(payment_mode="complimentary")

        budclass_data = {}

        # Aggregate data
        for bill in queryset:
            for item in bill.bill_items.all():
                product_title = item.product.title
                budclass = item.product.category.title
                if budclass not in budclass_data:
                    budclass_data[budclass] = {
                        'amount_total': 0,
                        'quantity_total': 0,
                        'items': []
                    }

                # Find existing item
                item_exists = next((x for x in budclass_data[budclass]['items'] if x['name'] == product_title and x['rate'] == item.rate), None)
                
                if not item_exists:
                    budclass_data[budclass]['items'].append({
                        'name': product_title,
                        'quantity': item.product_quantity,
                        'amount': item.amount,
                        'unit': item.unit_title,
                        'rate': item.rate,
                        'category': item.product.category.title
                    })
                    budclass_data[budclass]['amount_total'] += item.amount
                    budclass_data[budclass]['quantity_total'] += item.product_quantity
                else:
                    item_exists['quantity'] += item.product_quantity
                    item_exists['amount'] += item.amount
                    budclass_data[budclass]['amount_total'] += item.amount
                    budclass_data[budclass]['quantity_total'] += item.product_quantity

        # Convert dictionary to list and sort items
        result = []
        for category, data in budclass_data.items():
            data['items'] = sorted(data['items'], key=lambda x: x['quantity'], reverse=True)
            result.append({
                'category': category,
                'items': data['items'],
                'amount_total': data['amount_total'],
                'quantity_total': data['quantity_total'],
                'total_items': len(data['items'])
            })

        return Response(result, status=200)