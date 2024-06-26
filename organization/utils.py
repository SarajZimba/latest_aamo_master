from django.core.mail import send_mail
from django.template.loader import render_to_string

def send_mail_to_receipients(data, mail_list, sender):
    email_body = render_to_string('organization/mail_template.html', data)
    try:
        send_mail(
            'End Day Report',
            '',
            sender,
            mail_list,
            fail_silently=False,
            html_message=email_body
        )
    except Exception:
        pass

from django.db.models import Sum
def get_mobilepayments(branch, terminal):
    from bill.models import MobilePaymentSummary
    mobilepayment_summary = MobilePaymentSummary.objects.filter(branch=branch, terminal=terminal, sent_in_mail=False) 

    if mobilepayment_summary:
        total_per_type = mobilepayment_summary.values('type__name').annotate(total_value=Sum('value'))

        # # Convert the queryset to a dictionary
        # total_per_type_dict = {item['type__name']: item['total_value'] for item in total_per_type}


        # print(total_per_type)
        return mobilepayment_summary,total_per_type
    else:
        return None, None

# convert_to_dict = get_mobilepayments(3, 2)

def convert_to_dict(value):
    # Convert the queryset to a dictionary
    if value:
        total_per_type_dict = {item['type__name']: item['total_value'] for item in value}   

        return total_per_type_dict
    else:
        return None