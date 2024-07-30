from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from api.serializers.organization import BranchSerializer, OrganizationSerializer
from datetime import datetime
from organization.models import Branch, Organization


class OrganizationApi(ReadOnlyModelViewSet):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.active()

    def list(self, request, *args, **kwargs):
        instance = Organization.objects.last()
        serializer_data = self.get_serializer(instance).data
        serializer_data['server_date'] = datetime.now().date()
        return Response(serializer_data)


class BranchApi(ReadOnlyModelViewSet):
    serializer_class = BranchSerializer
    queryset = Branch.objects.active().filter(is_central_billing=False)

from rest_framework import generics
from organization.models import PrinterSetting
from api.serializers.organization import PrinterSettingSerializer
from rest_framework.views import APIView
import jwt
from rest_framework import status
from organization.models import Terminal

class PrinterSettingListView(APIView):

    def post(self, request, *args, **kwargs):
        data = request.data

        # jwt_token = request.META.get("HTTP_AUTHORIZATION")
        # jwt_token = jwt_token.split()[1]
        # try:
        #     token_data = jwt.decode(jwt_token, options={"verify_signature": False})  # Disable signature verification for claims extraction
        #     # You can access other claims as needed

        #     # Assuming "branch" is one of the claims, access it
        #     branch = token_data.get("branch")
        #     terminal_no = token_data.get("terminal")
        #     # token_type = token_data.get("token_type")


        #     # Print the branch
        #     print("Branch:", branch)
        #     print("Terminal:", terminal_no)
        # except jwt.ExpiredSignatureError:
        #     print("Token has expired.")
        # except jwt.DecodeError:
        #     print("Token is invalid.")
        branch = kwargs.get('branch_id')
        terminal_no = kwargs.get('terminal_no')

        ip = data['ip']
        port = data['port']
        url = data ['url']
        type = data['type']
        print_status = data['print_status']
        try:
            terminal_obj = Terminal.objects.get(terminal_no = int(terminal_no), status=True, is_deleted=False, branch=Branch.objects.get(id=branch, status=True, is_deleted=False))
        except Terminal.DoesNotExist:
            return Response({"detail":"Terminal does not exists"}, status=status.HTTP_400_BAD_REQUEST)
        print(terminal_obj)
        try:
            PrinterSetting.objects.filter(terminal=terminal_obj, printer_location=type, is_deleted=False, status=True).delete()
            PrinterSetting.objects.create(ip=ip, port=port, url=url, terminal=terminal_obj, printer_location=type, print_status=print_status)
        except Exception as e:
            print(e)
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail":"PrinterSetting created successfully"}, status=status.HTTP_200_OK)
        
    def get(self, request, *args, **kwargs):
        branch = kwargs.get('branch_id')
        terminal_no = kwargs.get('terminal_no')
        try:
            terminal_obj = Terminal.objects.get(terminal_no = int(terminal_no), status=True, is_deleted=False, branch=Branch.objects.get(id=branch, status=True, is_deleted=False))
        except Terminal.DoesNotExist:
            return Response({"detail":"Terminal does not exists"}, status=status.HTTP_400_BAD_REQUEST)
        print(terminal_obj)
        try:
            printersettings = PrinterSetting.objects.filter(terminal=terminal_obj, is_deleted=False, status=True)
            serializer = PrinterSettingSerializer(printersettings, many=True)
            # PrinterSetting.objects.create(ip=ip, port=port, url=url, terminal=terminal_obj, printer_location=type, print_status=print_status)
        except Exception as e:
            print(e)
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, *args, **kwargs):
        branch = kwargs.get('branch_id')
        terminal_no = kwargs.get('terminal_no')
        try:
            terminal_obj = Terminal.objects.get(terminal_no = int(terminal_no), status=True, is_deleted=False, branch=Branch.objects.get(id=branch, status=True, is_deleted=False))
        except Terminal.DoesNotExist:
            return Response({"detail":"Terminal does not exists"}, status=status.HTTP_400_BAD_REQUEST)
        print(terminal_obj)
        try:
            PrinterSetting.objects.filter(terminal=terminal_obj, is_deleted=False, status=True).delete()
            # serializer = PrinterSettingSerializer(printersettings, many=True)
            # PrinterSetting.objects.create(ip=ip, port=port, url=url, terminal=terminal_obj, printer_location=type, print_status=print_status)
        except Exception as e:
            print(e)
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({"detail":"PrinterSettings have been deleted successfully"}, status=status.HTTP_200_OK)
    
import pytz 
from django.utils import timezone
from organization.models import MailRecipient, MailSendRecord
from organization.models import EndDayDailyReport
from organization.utils import mobile_payment_func
import environ
env = environ.Env(DEBUG=(bool, False))
from bill.models import MobilePaymentSummary
from django.db.models import Q, Sum
class TestMasterView(APIView):
    def get(self, request):

        ny_timezone = pytz.timezone('Asia/Kathmandu')
        current_datetime_ny = timezone.now().astimezone(ny_timezone)

        formatted_date = current_datetime_ny.strftime("%Y-%m-%d")
        transaction_date = current_datetime_ny.date()

        enddays = EndDayDailyReport.objects.filter(date_time__startswith=formatted_date)
        for endday in enddays:

            sender = env('EMAIL_HOST_USER')
            mail_list = []
            recipients = MailRecipient.objects.filter(status=True)
            for r in recipients:
                mail_list.append(r.email)
                MailSendRecord.objects.create(mail_recipient=r)
            if mail_list:

                dt_now = datetime.now()
                date_now = dt_now.date()
                time_now = dt_now.time().strftime('%I:%M %p')

                mobile_payment_func(endday)

        return Response("Success", 200)
    

from django.db.models import Q
from datetime import datetime
from django.dispatch import receiver
import environ
env = environ.Env(DEBUG=(bool, False))
# from .utils import send_combined_mail_to_receipients
from threading import Thread
from itertools import groupby
from operator import itemgetter
from bill.models import MobilePaymentSummary
from django.db.models import Sum
from organization.utils import mobile_payment_func, check_end_day_terminal

class TestMobileView(APIView):
    def get(self, request):

        terminal_to_end_their_day = check_end_day_terminal()
        print(terminal_to_end_their_day)
        # enddays = 
        ny_timezone = pytz.timezone('Asia/Kathmandu')
        current_datetime_ny = timezone.now().astimezone(ny_timezone)

        formatted_date = current_datetime_ny.strftime("%Y-%m-%d")
        transaction_date = current_datetime_ny.date()

        enddays = EndDayDailyReport.objects.filter(date_time__startswith=formatted_date)

        count_enddays = enddays.count()
        print(f"count_enddayscounts {count_enddays}")
        enddays_terminal = []

        combine_data = {}
        total_sale_holder = 0.0
        net_sales_holder = 0.0
        discount_holder = 0.0
        tax_holder = 0.0

        combined_mobile_payments = {}
        for endday in enddays:

            sender = env('EMAIL_HOST_USER')
            mail_list = []
            recipients = MailRecipient.objects.filter(status=True)
            for r in recipients:
                mail_list.append(r.email)
                MailSendRecord.objects.create(mail_recipient=r)
            if mail_list:

                dt_now = datetime.now()
                date_now = dt_now.date()
                time_now = dt_now.time().strftime('%I:%M %p')
                org = Organization.objects.first().org_name

                formatted_mobile_payment = mobile_payment_func(endday)



                # print(forma)
                # print("before sorting", bills)
                # sorted_bills = sorted(bills, key=itemgetter('customer_name'))
                report_data = {

                    'total_sale': endday.total_sale,
                    'date_time':endday.date_time,
                    'employee_name': endday.employee_name,
                    'net_sales': endday.net_sales,
                    'tax': endday.vat,  
                    'total_discounts': endday.total_discounts,
                    'cash': endday.cash,
                    'credit': endday.credit,
                    'credit_card': endday.credit_card,
                    'mobile_payment': endday.mobile_payment,
                    'complimentary': endday.complimentary,
                    'start_bill': endday.start_bill,
                    'end_bill': endday.end_bill,
                    'branch': endday.branch.name,
                    'terminal': endday.terminal,
                    'formatted_mobile_payment':formatted_mobile_payment
                }



                enddays_terminal.append(report_data)
                total_sale_holder += endday.total_sale
                net_sales_holder += endday.net_sales
                discount_holder += endday.total_discounts
                tax_holder += endday.vat
                
                for payment_type in formatted_mobile_payment:
                    type_name = payment_type['type']
                    total_value = payment_type['total']
                    
                    if type_name in combined_mobile_payments:
                        combined_mobile_payments[type_name] += total_value
                    else:
                        combined_mobile_payments[type_name] = total_value

        combine_data = {
                    'org_name':org,
                    'date_now': date_now,
                    'time_now': time_now,
                    "total_sale": total_sale_holder,
                    "net_sales": net_sales_holder,
                    "tax": tax_holder,
                    "total_discounts": discount_holder,
                    "combined_mobile_payment": combined_mobile_payments

                }
        
        print(f"This is the combined data {combine_data}")

                # print()


                # Inside the create_profile function
        
                # Thread(target=send_combined_mail_to_receipients, args=(combine_data, enddays_terminal, mail_list, sender)).start()
        print(f"mail_list {mail_list}")


        return Response("Success", 200)
    
from organization.utils import check_end_day_terminal
class TestAllEndday(APIView):
    def get(self, request):
        check_end_day_terminal()

        return Response("success", 200)
    
from organization.cron import fetch_details

class TestCron(APIView):
    def get(self, request):
        fetch_details()
        return Response('Success', 200)
