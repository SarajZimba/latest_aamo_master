import pytz
from django.utils import timezone
from organization.models import Organization, EndDayDailyReport, MailRecipient, MailSendRecord

from datetime import datetime
import environ
env = environ.Env(DEBUG=(bool, False))
from .utils import send_combined_mail_to_receipients
from threading import Thread

from organization.utils import mobile_payment_func, check_end_day_terminal, get_credit

def fetch_details():

    is_all_terminal_end = check_end_day_terminal()

    print(f"is_all_terminal_end {is_all_terminal_end}")
    if is_all_terminal_end:
        print("I am in")
        ny_timezone = pytz.timezone('Asia/Kathmandu')
        current_datetime_ny = timezone.now().astimezone(ny_timezone)

        formatted_date = current_datetime_ny.strftime("%Y-%m-%d")
        transaction_date = current_datetime_ny.date()

        enddays = EndDayDailyReport.objects.filter(date_time__startswith=formatted_date)
        print(enddays)
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
                grouped_bills = get_credit(endday)



                # calcualting the report total for the individual terminals.
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
                    'formatted_mobile_payment':formatted_mobile_payment,
                    'grouped_bills':grouped_bills
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
        print(f"mail_list {mail_list}")

        print(f"enddays_terminal {enddays_terminal}")
        try:
            Thread(target=send_combined_mail_to_receipients, args=(combine_data, enddays_terminal, mail_list, sender)).start()
            print("Mail Sent")
        except Exception as e:
            print(f"Error in sending combined mail: {e}")

    else:
        print("Endday are not done yet")
