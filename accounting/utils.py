from pyBSDate import convert_AD_to_BS
from datetime import datetime


def get_fiscal_year():
    from organization.models import Organization
    org = Organization.objects.first()
    return org.get_fiscal_year()


def calculate_depreciation(amount, percentage, bill_date):
    date_format = '%Y-%m-%d'
    ad_date = datetime.strptime(str(bill_date), date_format)
    year, month, day = ad_date.year, ad_date.month, ad_date.day
    bs_date = convert_AD_to_BS(year, month, day)
    nepali_month_int = bs_date[1]
    depreciation_amount = 0
    amount= float(amount)
    if nepali_month_int <= 3:
        depreciation_amount = (amount*(percentage/100))/3
    elif nepali_month_int <= 9:
        depreciation_amount = amount*(percentage/100)
    else:
        depreciation_amount = (amount*(percentage/100))*2/3
    return depreciation_amount, bs_date


class ProfitAndLossData():

    @staticmethod
    def get_data(revenues, expenses):
        revenue_list= []
        revenue_total = 0
        expense_list= []
        expense_total = 0

        for revenue in revenues:
            revenue_list.append({'title':revenue.ledger_name, 'amount': revenue.total_value})
            revenue_total += revenue.total_value

        for expense in expenses:
            expense_list.append({'title':expense.ledger_name, 'amount': expense.total_value})
            expense_total += expense.total_value

        return expense_list, expense_total, revenue_list, revenue_total
    
"""
Signal to update Cumulative Ledger
"""
from datetime import date
def update_cumulative_ledger_journal(instance, journal):
    from .models import CumulativeLedger

    ledger = CumulativeLedger.objects.filter(ledger=instance).last()
    value_changed = instance.total_value - ledger.total_value
    if instance.account_chart.account_type in ['Asset', 'Expense']:
        if value_changed > 0:
                CumulativeLedger.objects.create(account_chart=instance.account_chart, ledger_name=instance.ledger_name, total_value=instance.total_value, value_changed=value_changed, debit_amount=abs(value_changed), ledger=instance,journal=journal)
        else:
            CumulativeLedger.objects.create(account_chart=instance.account_chart, ledger_name=instance.ledger_name, total_value=instance.total_value, value_changed=value_changed, credit_amount=abs(value_changed), ledger=instance, journal=journal)
    else:
        if value_changed > 0:
            CumulativeLedger.objects.create(account_chart=instance.account_chart, ledger_name=instance.ledger_name, total_value=instance.total_value, value_changed=value_changed, credit_amount=abs(value_changed), ledger=instance, journal=journal)
        else:
            CumulativeLedger.objects.create(account_chart=instance.account_chart, ledger_name=instance.ledger_name, total_value=instance.total_value, value_changed=value_changed, debit_amount=abs(value_changed), ledger=instance, journal=journal)

def create_cumulative_ledger_journal(instance, journal):
    from .models import TblCrJournalEntry, TblDrJournalEntry, TblJournalEntry, CumulativeLedger
    if instance.account_chart.account_type in ['Asset', 'Expense']:
        CumulativeLedger.objects.create(account_chart=instance.account_chart, ledger_name=instance.ledger_name, total_value=instance.total_value, value_changed=instance.total_value, ledger=instance, debit_amount=instance.total_value)
    else:
        CumulativeLedger.objects.create(account_chart=instance.account_chart, ledger_name=instance.ledger_name, total_value=instance.total_value, value_changed=instance.total_value, ledger=instance, credit_amount=instance.total_value)
    if instance.account_chart.group == "Sundry Debtors":
        journal = TblJournalEntry.objects.create(employee_name=f"From Debtors form {instance.ledger_name}", journal_total=instance.total_value)
        TblDrJournalEntry.objects.create(ledger=instance, debit_amount=instance.total_value, particulars=f"Automatic: {instance.ledger_name} a/c Dr", journal_entry=journal)


    if instance.account_chart.group == "Sundry Creditors":
        journal = TblJournalEntry.objects.create(employee_name=f"From Creditors form {instance.ledger_name}", journal_total=instance.total_value)
        TblCrJournalEntry.objects.create(ledger=instance, credit_amount=instance.total_value, particulars=f"Automatic: To {instance.ledger_name}", journal_entry=journal)

