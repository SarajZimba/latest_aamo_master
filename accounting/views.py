from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView,DetailView,ListView,TemplateView,UpdateView,View
from root.utils import DeleteMixin
from .models import AccountChart, Depreciation, FiscalYearLedger, FiscalYearSubLedger, CumulativeLedger
from django.views.generic import TemplateView
from .forms import AccountChartForm
from decimal import Decimal as D
from django.db.models import Q, Sum
from django.contrib import messages
from organization.models import Organization
from rest_framework.response import Response
from accounting.utils import calculate_depreciation
from rest_framework.decorators import api_view
from .utils import ProfitAndLossData
from user.permission import IsAdminMixin
import json
from decimal import Decimal
from itertools import chain
from operator import attrgetter
from datetime import datetime
from django.db import models
from .forms import JournalEntryForm
from collections import defaultdict
from django.db.models.functions import Coalesce




class AccountChartMixin(IsAdminMixin):
    model = AccountChart
    form_class = AccountChartForm
    paginate_by = 10
    queryset = AccountChart.objects.prefetch_related('accountledger_set')
    success_url = reverse_lazy('accountchart_list')


class AccountChartList(AccountChartMixin, ListView):
    queryset = AccountChart.objects.all()
    template_name = "accounting/accounting_chart.html"


    def get(self, request, *args, **kwargs):
        query_set = self.queryset
        sundry_debtors_total = AccountLedger.objects.filter(account_chart__group='Sundry Debtors').aggregate(total_value_sum=Sum('total_value'))['total_value_sum']
        sundry_creditors_total = AccountLedger.objects.filter(account_chart__group='Sundry Creditors').aggregate(total_value_sum=Sum('total_value'))['total_value_sum']
        # print(sundry_debtors_total)
        assets = query_set.filter(account_type='Asset')
        liabilities = query_set.filter(account_type='Liability')
        equities = query_set.filter(account_type='Equity')
        revenues = query_set.filter(account_type='Revenue')
        expenses = query_set.filter(account_type='Expense')
        others = query_set.filter(account_type='Other')


        context = {
            'sundry_debtors_total': sundry_debtors_total,
            'sundry_creditors_total': sundry_creditors_total,
            'assets': assets,
            'liabilities':liabilities,
            'equities':equities,
            'revenues':revenues,
            'expenses': expenses,
            'others': others
        }
        return render(request, 'accounting/accounting_chart.html', context)



class AccountChartDetail(AccountChartMixin, DetailView):
    template_name = "accounting/accountchart_detail.html"

class AccountChartCreate(AccountChartMixin, CreateView):
    template_name = "accounting/create.html"

class AccountChartUpdate(AccountChartMixin, UpdateView):
    template_name = "update.html"

class AccountChartDelete(AccountChartMixin, DeleteMixin, View):
    pass


from .models import AccountLedger, AccountSubLedger
from .forms import AccountLedgerForm
class AccountLedgerMixin(IsAdminMixin):
    model = AccountLedger
    form_class = AccountLedgerForm
    paginate_by = 10
    queryset = AccountLedger.objects.all()
    success_url = reverse_lazy('accountledger_list')

class AccountLedgerList(AccountLedgerMixin, ListView):
    template_name = "accounting/accountledger_list.html"
    queryset = AccountLedger.objects.all()

class AccountLedgerDetail(AccountLedgerMixin, DetailView):
    template_name = "accounting/accountledger_detail.html"

class AccountLedgerCreate(AccountLedgerMixin, CreateView):
    template_name = "accounting/create.html"

class AccountLedgerUpdate(AccountLedgerMixin, UpdateView):
    template_name = "update.html"

class AccountLedgerDelete(AccountChartMixin, DeleteMixin, View):
    pass


from .forms import AccountSubLedgerForm
class AccountSubLedgerCreate(IsAdminMixin, CreateView):
    template_name = "accounting/subledger/create.html"
    form_class = AccountSubLedgerForm
    success_url = reverse_lazy('accountchart_list')

class AccountSubLedgerUpdate(IsAdminMixin, UpdateView):
    form_class = AccountSubLedgerForm
    queryset = AccountSubLedger.objects.all()
    template_name = "update.html"

from .models import Expense
from .forms import ExpenseForm
class ExpenseMixin(IsAdminMixin):
    model = Expense
    form_class = ExpenseForm
    paginate_by = 10
    queryset = Expense.objects.all()
    success_url = reverse_lazy('expenses_list')

class ExpenseList(ExpenseMixin, ListView):
    template_name = "accounting/expenses/expenses_list.html"

class ExpenseDetail(ExpenseMixin, DetailView):
    template_name = "expense/expense_detail.html"

class ExpenseCreate(ExpenseMixin, CreateView):
    template_name = "accounting/expenses/expenses_create.html"

class ExpenseUpdate(ExpenseMixin, UpdateView):
    template_name = "update.html"

class ExpenseDelete(ExpenseMixin, DeleteMixin, View):
    pass



from .models import TblDrJournalEntry, TblCrJournalEntry, TblJournalEntry, AccountSubLedger

class JournalEntryCreateView(IsAdminMixin,View):

    def get(self, request):
        ledgers = AccountLedger.objects.all()
        sub_ledgers = AccountSubLedger.objects.all()
        return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers':ledgers, 'sub_ledgers':sub_ledgers})
    
    def get_subledger(self, subledger, ledger):
        subled = None
        if not subledger.startswith('-'):
            try:
                subledger_id = int(subledger)
                subled = AccountSubLedger.objects.get(pk=subledger_id)
            except ValueError:
                subled = AccountSubLedger.objects.create(sub_ledger_name=subledger, is_editable=True, ledger=ledger)
        return subled
    
    # def post(self, request):
    #     data = request.POST
    #     debit_ledgers = data.getlist('debit_ledger', [])
    #     debit_particulars = data.getlist('debit_particular', [])
    #     debit_amounts = data.getlist('debit_amount', [])
    #     debit_subledgers = data.getlist('debit_subledger', [])

    #     credit_ledgers = data.getlist('credit_ledger', [])
    #     credit_particulars = data.getlist('credit_particular', [])
    #     credit_amounts = data.getlist('credit_amount', [])
    #     credit_subledgers = data.getlist('credit_subledger', [])
    #     print(credit_ledgers)

    #     ledgers = AccountLedger.objects.all()
    #     sub_ledgers = AccountSubLedger.objects.all()

    #     try:
    #         parsed_debitamt = (lambda x: [D(i) for i in x])(debit_amounts)
    #         parsed_creditamt = (lambda x: [D(i) for i in x])(credit_amounts)
    #     except Exception:
    #         messages.error(request, "Please Enter valid amount")
    #         return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers':ledgers, 'sub_ledgers':sub_ledgers})
        
    #     debit_sum, credit_sum = sum(parsed_debitamt), sum(parsed_creditamt)
    #     if debit_sum != credit_sum:
    #         messages.error(request, "Debit Total and Credit Total must be equal")
    #         return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers':ledgers, 'sub_ledgers':sub_ledgers})

    #     for dr in debit_ledgers:
    #         if dr.startswith('-'):
    #             messages.error(request, "Ledger must be selected")
    #             return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers':ledgers, 'sub_ledgers':sub_ledgers}) 
        
    #     credit_to_debit_mapping = {}

    #     journal_entry = TblJournalEntry.objects.create(employee_name=request.user.username, journal_total=debit_sum)
    #     for i in range(len(debit_ledgers)):
    #         debit_ledger_id = int(debit_ledgers[i])
    #         debit_ledger = AccountLedger.objects.get(pk=debit_ledger_id)
    #         debit_particular = debit_particulars[i]
    #         debit_amount = D(debit_amounts[i])
    #         subledger = self.get_subledger( debit_subledgers[i], debit_ledger)
    #         debit_ledger_type = debit_ledger.account_chart.account_type
    #         TblDrJournalEntry.objects.create(ledger=debit_ledger, journal_entry=journal_entry, particulars=debit_particular, debit_amount=debit_amount, sub_ledger=subledger)
    #         if debit_ledger_type in ['Asset', 'Expense']:
    #             debit_ledger.total_value =debit_ledger.total_value + debit_amount
    #             debit_ledger.save()
    #             if subledger:
    #                 subledger.total_value = subledger.total_value + debit_amount
    #                 subledger.save()

    #         elif debit_ledger_type in ['Liability', 'Revenue', 'Equity']:
    #             debit_ledger.total_value = debit_ledger.total_value - debit_amount
    #             debit_ledger.save()
    #             if subledger:
    #                 subledger.total_value = subledger.total_value - debit_amount
    #                 subledger.save()

    #     for i in range(len(credit_ledgers)):
    #         credit_ledger_id = int(credit_ledgers[i])
    #         credit_ledger = AccountLedger.objects.get(pk=credit_ledger_id)
    #         credit_particular = credit_particulars[i]
    #         credit_amount = D(credit_amounts[i])
    #         subledger = self.get_subledger( credit_subledgers[i], credit_ledger)
    #         credit_ledger_type = credit_ledger.account_chart.account_type
    #         TblCrJournalEntry.objects.create(ledger=credit_ledger, journal_entry=journal_entry, particulars=credit_particular, credit_amount=credit_amount, sub_ledger=subledger,paidfrom_ledger=credit_ledger)
    #         if credit_ledger_type in ['Asset', 'Expense']:
    #             credit_ledger.total_value = credit_ledger.total_value - credit_amount
    #             credit_ledger.save()
    #             if subledger:
    #                 subledger.total_value = subledger.total_value - credit_amount
    #                 subledger.save()
    #         elif credit_ledger_type in ['Liability', 'Revenue', 'Equity']:
    #             credit_ledger.total_value = credit_ledger.total_value + credit_amount
    #             credit_ledger.save()
    #             if subledger:
    #                 subledger.total_value = subledger.total_value + credit_amount
    #                 subledger.save()

    #     return redirect('journal_list')

    def post(self, request):
        data = request.POST
        debit_ledgers = data.getlist('debit_ledger', [])
        debit_particulars = data.getlist('debit_particular', [])
        debit_amounts = data.getlist('debit_amount', [])
        debit_subledgers = data.getlist('debit_subledger', [])

        credit_ledgers = data.getlist('credit_ledger', [])
        credit_particulars = data.getlist('credit_particular', [])
        credit_amounts = data.getlist('credit_amount', [])
        credit_subledgers = data.getlist('credit_subledger', [])
        # print(credit_ledgers)

        ledgers = AccountLedger.objects.all()
        sub_ledgers = AccountSubLedger.objects.all()

        try:
            parsed_debitamt = (lambda x: [D(i) for i in x])(debit_amounts)
            parsed_creditamt = (lambda x: [D(i) for i in x])(credit_amounts)
        except Exception:
            messages.error(request, "Please Enter a valid amount")
            return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

        debit_sum, credit_sum = sum(parsed_debitamt), sum(parsed_creditamt)
        if debit_sum != credit_sum:
            messages.error(request, "Debit Total and Credit Total must be equal")
            return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

        for dr in debit_ledgers:
            if dr.startswith('-'):
                messages.error(request, "Ledger must be selected")
                return render(request, 'accounting/journal/journal_entry_create.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

        credit_to_debit_mapping = {}

        journal_entry = TblJournalEntry.objects.create(employee_name=request.user.username, journal_total=debit_sum)
        for i in range(len(credit_ledgers)):
            credit_ledger_id = int(credit_ledgers[i])
            
            credit_ledger = AccountLedger.objects.get(pk=credit_ledger_id)
          
            credit_to_debit_mapping[credit_ledger] = credit_ledger
            credit_particular = credit_particulars[i]
            credit_amount = D(credit_amounts[i])
            subledger = self.get_subledger(credit_subledgers[i], credit_ledger)
            credit_ledger_type = credit_ledger.account_chart.account_type
            TblCrJournalEntry.objects.create(ledger=credit_ledger, journal_entry=journal_entry, particulars=credit_particular, credit_amount=credit_amount, sub_ledger=subledger, paidfrom_ledger=credit_ledger)
            if credit_ledger_type in ['Asset', 'Expense']:
                credit_ledger.total_value = credit_ledger.total_value - credit_amount
                credit_ledger.save()
                if subledger:
                    subledger.total_value = subledger.total_value - credit_amount
                    subledger.save()
            elif credit_ledger_type in ['Liability', 'Revenue', 'Equity']:
                credit_ledger.total_value = credit_ledger.total_value + credit_amount
                credit_ledger.save()
                if subledger:
                    subledger.total_value = subledger.total_value + credit_amount
                    subledger.save()

        
        for i in range(len(debit_ledgers)):
            debit_ledger_id = int(debit_ledgers[i])
            debit_ledger = AccountLedger.objects.get(pk=debit_ledger_id)
            debit_particular = debit_particulars[i]
            debit_amount = D(debit_amounts[i])
            subledger = self.get_subledger(debit_subledgers[i], debit_ledger)
            debit_ledger_type = debit_ledger.account_chart.account_type
            TblDrJournalEntry.objects.create(ledger=debit_ledger, journal_entry=journal_entry, particulars=debit_particular, debit_amount=debit_amount, sub_ledger=subledger, paidfrom_ledger=credit_to_debit_mapping.get(credit_ledger))
            if debit_ledger_type in ['Asset', 'Expense']:
                debit_ledger.total_value = debit_ledger.total_value + debit_amount
                debit_ledger.save()
                if subledger:
                    subledger.total_value = subledger.total_value + debit_amount
                    subledger.save()
            elif debit_ledger_type in ['Liability', 'Revenue', 'Equity']:
                debit_ledger.total_value = debit_ledger.total_value - debit_amount
                debit_ledger.save()
                if subledger:
                    subledger.total_value = subledger.total_value - debit_amount
                    subledger.save()

        return redirect('journal_list')



class JournalEntryView(IsAdminMixin, View):

    def get(self, request, pk=None):
        from_date = request.GET.get('fromDate', None)
        to_date = request.GET.get('toDate', None)

        if from_date and to_date and (to_date > from_date):
            journals = TblJournalEntry.objects.filter(created_at__range=[from_date, to_date])

            journal_entries = {
                'entries': [],
                "debit_sum": 0,
                "credit_sum": 0
            }
            debit_sum, credit_sum = 0,0
            for journal in journals:
                data = {'dr':[], 'cr':[], "dr_total": 0, "cr_total": 0}
                for dr in journal.tbldrjournalentry_set.all():
                    data['dr'].append(dr)
                    data['dr_total'] += dr.debit_amount
                for cr in journal.tblcrjournalentry_set.all():
                    data['cr'].append(cr)
                    data['cr_total'] += cr.credit_amount
                journal_entries['entries'].append(data)
                journal_entries['debit_sum']+=data['dr_total']
                journal_entries['credit_sum']+=data['cr_total']


            context = {
                'from_date':from_date,
                'to_date': to_date,
                'journals':journal_entries
            }

            return render(request,'accounting/journal/journal.html' , context=context)
        if pk:
            journal = TblJournalEntry.objects.get(pk=pk)
            credit_details = TblCrJournalEntry.objects.filter(journal_entry=journal)
            debit_details = TblDrJournalEntry.objects.filter(journal_entry=journal)
            debit_total, credit_total = 0, 0
            for dr in debit_details:
                debit_total += dr.debit_amount

            for cr in credit_details:
                credit_total += cr.credit_amount

            context = {
                'credit': credit_details,
                'debit': debit_details,
                "dr_total":debit_total,
                "cr_total": credit_total,
                'journal':journal
            }
            return render(request, 'accounting/journal/journal_voucher.html', context)
            

        journal_entries = TblJournalEntry.objects.prefetch_related('tbldrjournalentry_set').order_by('-created_at').all()
        return render(request, 'accounting/journal/journal_list.html',  {'journal_entries': journal_entries})





class TrialBalanceView(IsAdminMixin, View):

    def filtered_view(self, from_date, to_date):
        filtered_transactions = CumulativeLedger.objects.filter(created_at__range=[from_date, to_date])
        filtered_sum = filtered_transactions.values('ledger_name', 'account_chart__account_type', 'account_chart__group').annotate(Sum('value_changed'))
        # print(filtered_sum)
        trial_balance = []

        total = {'debit_total':0, 'credit_total':0}

        for fil in filtered_sum:
            data = {}
            data['ledger'] = fil['ledger_name']
            account_type = fil['account_chart__account_type']
            account_group = fil['account_chart__group']
            # print(account_group)
            if account_type in ['Asset', 'Expense']:
                data['actual_value'] = fil['value_changed__sum']
                if fil['value_changed__sum'] < 0:
                    val = abs(fil['value_changed__sum'])
                    data['credit'] = val
                    data['debit'] = '-'
                    total['credit_total'] += val
                else:
                    val = fil['value_changed__sum']
                    data['debit'] = val
                    data['credit'] = '-'
                    total['debit_total'] += val
            else:
                if fil['value_changed__sum'] < 0:
                    val = abs(fil['value_changed__sum'])
                    data['debit'] = val
                    data['credit'] = '-'
                    total['debit_total'] += val
                else:
                    val = fil['value_changed__sum']
                    data['credit'] = val
                    data['debit'] = '-'
                    total['credit_total'] += val

            if not any(d['account_type'] == account_type for d in trial_balance):
                    trial_balance.append(
                        {
                            'account_type': account_type,
                            'ledgers' : [data],
                            'group' : account_group,
                        }
                    )
            else:
                for tb in trial_balance:
                    if tb['account_type'] == account_type:
                        # print(data)
                        tb['ledgers'].append(data)
                        break

        return trial_balance, total

    def detail_view(self, from_date, to_date):
        all_ledgers_list = AccountLedger.objects.values_list('ledger_name', flat=True)
        before_transactions = CumulativeLedger.objects.filter(created_at__lt=from_date, total_value__gt=0).order_by('-created_at')

        trial_balance = []
        total = {'debit_total':0, 'credit_total':0}

        filtered_transactions = CumulativeLedger.objects.filter(created_at__range=[from_date, to_date])
        filtered_sum = filtered_transactions.values('ledger_name', 'account_chart__account_type', 'account_chart__group' ).annotate(Sum('debit_amount'), Sum('credit_amount'), Sum('value_changed'))

        for fil in filtered_sum:
            data = {}
            data['ledger'] = fil['ledger_name']
            account_type = fil['account_chart__account_type']
            account_group = fil['account_chart__account_group']
            data['debit'] = fil['debit_amount__sum']
            data['credit'] = fil['credit_amount__sum']
            if account_type in ['Asset', 'Expense']:
                if fil['value_changed__sum'] < 0:
                    total['credit_total'] += abs(fil['value_changed__sum'])
                else:
                    total['debit_total'] += abs(fil['value_changed__sum'])
            else:
                if fil['value_changed__sum'] < 0:
                    total['debit_total'] += abs(fil['value_changed__sum'])
                else:
                    total['credit_total'] += abs(fil['value_changed__sum'])



            if not any(d['account_type'] == account_type for d in trial_balance):
                    trial_balance.append(
                        {
                            'account_type': account_type,
                            'ledgers' : [data],
                            'group' : account_group
                        }
                    )
            else:
                for tb in trial_balance:
                    if tb['account_type'] == account_type:
                        tb['ledgers'].append(data)
                        break


        included_ledgers = []

        for trans in before_transactions:
            account_type = trans.account_chart.account_type
            if trans.ledger_name not in included_ledgers:
                included_ledgers.append(trans.ledger_name)
                if not any(d['account_type'] == account_type for d in trial_balance):
                    data = {
                        'ledger': trans.ledger_name,
                        'opening': trans.total_value,
                        'debit':'-',
                        'credit':'-',
                        'closing': trans.total_value,
                        'group': account_group
                    }
                    trial_balance.append({'account_type':account_type, 'ledgers':[data], 'group': account_group})
                else:
                    for tb in trial_balance:
                        if tb['account_type'] == account_type:
                            if not any(d['ledger'] == trans.ledger_name for d in tb['ledgers']):
                                tb['ledgers'].append({
                                    'ledger': trans.ledger_name,
                                    'opening': trans.total_value,
                                    'debit':'-',
                                    'credit':'-',
                                    'closing': trans.total_value,
                                    'group': account_group
                                })
                            else:
                                for led in tb['ledgers']:
                                    if led['ledger'] == trans.ledger_name:
                                        led['opening'] = trans.total_value
                                        if account_type in ['Asset', 'Expense']:
                                            led['closing'] = trans.total_value + led['debit'] - led['credit']
                                        else:
                                            led['closing'] = trans.total_value + led['credit'] - led['debit']
                                        break


            if len(included_ledgers) >= len(all_ledgers_list):
                break
        # print(trial_balance)

 
        return trial_balance, total

    def get(self, request):
        from_date = request.GET.get('fromDate', None)
        to_date = request.GET.get('toDate', None)
        option = request.GET.get('option', None)
        current_fiscal_year = Organization.objects.last().current_fiscal_year
        first_date=None
        last_date=None

        if from_date and to_date:
            if option and option =='openclose':
                trial_balance, total = self.detail_view(from_date, to_date)
                context = {
                    'trial_balance': trial_balance,
                    "total": total,
                    "from_date":from_date,
                    "to_date":to_date,
                    'openclose':True,
                    'current_fiscal_year':current_fiscal_year
                }
                return render(request, 'accounting/trial_balance.html', context)
            else:
                trial_balance, total= self.filtered_view(from_date, to_date)
                context = {
                    'trial_balance': trial_balance,
                    "total": total,
                    "from_date":from_date,
                    "to_date":to_date,
                    'current_fiscal_year':current_fiscal_year
                }

                return render(request, 'accounting/trial_balance.html', context)
        
        else:
            trial_balance = []
            total = {'debit_total':0, 'credit_total':0}
            ledgers = AccountLedger.objects.filter(~Q(total_value=0))
            for led in ledgers:
                data = {}
                account_type = led.account_chart.account_type
                # account_group = led.account_chart.group
                # print(account_group)
                
                data['ledger']=led.ledger_name
                data['group']=led.account_chart.group
                if account_type in ['Asset', 'Expense']:
                    if led.total_value > 0:
                        data['debit'] = led.total_value
                        total['debit_total'] += led.total_value
                        data['credit'] = '-'
                    else:
                        val = abs(led.total_value)
                        data['credit'] = val
                        total['credit_total'] += val
                        data['debit'] = '-'
                else:
                    if led.total_value > 0:
                        data['credit'] = led.total_value
                        total['credit_total'] += led.total_value
                        data['debit'] = '-'
                    else:
                        val = abs(led.total_value)
                        data['debit'] = val
                        total['debit_total'] += val
                        data['credit'] = '-'
                if not any(d['account_type'] == account_type for d in trial_balance):
                    trial_balance.append(
                        {
                            'account_type': account_type,
                            'ledgers' : [data]
                            # 'group': account_group
                        }
                    )
                else:
                    for tb in trial_balance:
                        if tb['account_type'] == account_type:
                            tb['ledgers'].append(data)
                            break
                
                debit_entries = TblDrJournalEntry.objects.filter(ledger=led)
                credit_entries = TblCrJournalEntry.objects.filter(ledger=led)

                # Check the count of credit entries
                credit_entry_count = credit_entries.count()

                # Check the count of debit entries
                debit_entry_count = debit_entries.count()

                if credit_entry_count > 0 or debit_entry_count > 0:
                    # Calculate the first and last dates for credit entries
                    credit_date_range = credit_entries.aggregate(
                        first_credit_date=Min('created_at'),
                        last_credit_date=Max('created_at')
                    )

                    # Calculate the first and last dates for debit entries
                    debit_date_range = debit_entries.aggregate(
                        first_debit_date=Min('created_at'),
                        last_debit_date=Max('created_at')
                    )

                    # Determine the minimum date for this ledger (comparing debit and credit)
                    ledger_first_date = None

                    if credit_date_range['first_credit_date'] and debit_date_range['first_debit_date']:
                        ledger_first_date = min(
                            credit_date_range['first_credit_date'],
                            debit_date_range['first_debit_date']
                        )
                    elif credit_date_range['first_credit_date']:
                        ledger_first_date = credit_date_range['first_credit_date']
                    elif debit_date_range['first_debit_date']:
                        ledger_first_date = debit_date_range['first_debit_date']

                    # Update the overall minimum date
                    if ledger_first_date and (first_date is None or ledger_first_date < first_date):
                        first_date = ledger_first_date

                    # Determine the maximum date for this ledger (comparing debit and credit)
                    ledger_last_date = None

                    if credit_date_range['last_credit_date'] and debit_date_range['last_debit_date']:
                        ledger_last_date = max(
                            credit_date_range['last_credit_date'],
                            debit_date_range['last_debit_date']
                        )
                    elif credit_date_range['last_credit_date']:
                        ledger_last_date = credit_date_range['last_credit_date']
                    elif debit_date_range['last_debit_date']:
                        ledger_last_date = debit_date_range['last_debit_date']

                    # Update the overall maximum date
                    if ledger_last_date and (last_date is None or ledger_last_date > last_date):
                        last_date = ledger_last_date

             

        vat_receivable, vat_payable = 0, 0
        new_vat_ledger = None  # Define a variable to store the new VAT ledger entry

        


        # Find the new VAT ledger entry
        for sata in trial_balance:

            new_ledgers = []
            for data in sata['ledgers']:
                if data['ledger'] == 'VAT Receivable':
                    if data['debit'] == '-':
                        data['debit'] = 0
                    vat_receivable = data['debit']
 
                    total['debit_total'] -= data['debit']
                elif data['ledger'] == 'VAT Payable':
                    if data['credit'] == '-':
                        data['credit'] = 0
                    vat_payable = data['credit']
                    total['credit_total'] -= data['credit']
                else:
                    new_ledgers.append(data)  # Keep all other ledgers

            sata['ledgers'] = new_ledgers  # Replace ledgers with the filtered list

        # Calculate the VAT amount
        vat_amount = vat_receivable - vat_payable

        if vat_amount != 0:
            new_vat_ledger = {'ledger': 'VAT'}
            if vat_amount > 0:
                new_vat_ledger['account_head'] = 'Asset'
                new_vat_ledger['debit'] = vat_amount
                new_vat_ledger['credit'] = '-'
                total['debit_total'] += vat_amount
            else:
                new_vat_ledger['account_head'] = 'Liability'
                new_vat_ledger['debit'] = '-'
                new_vat_ledger['credit'] = abs(vat_amount)
                total['credit_total'] += abs(vat_amount)

        # Merge the new VAT entry with the existing Asset or Liability entry
        if new_vat_ledger:
            for sata in trial_balance:
                if sata['account_type'] in ['Asset', 'Liability']:
                    sata['ledgers'].append(new_vat_ledger)
                    break



        Sundry_debtors_total = 0
        Sundry_creditors_total = 0
        new_ledgers_asset = []
        new_ledgers_liability = []

        for entry in trial_balance:
            new_ledger_entries = []
            for data in entry['ledgers']:
                group = data.get('group')
                if group == 'Sundry Debtors':
                    Sundry_debtors_total += data.get('debit')
                elif group == 'Sundry Creditors':
                    Sundry_creditors_total += data.get('credit')
                else:
                    new_ledger_entries.append(data)  # Keep all other ledgers
            
            entry['ledgers'] = new_ledger_entries  # Replace ledgers with the filtered list

        # Create new ledger entries for Sundry Debtors and add to the Asset section
        if Sundry_debtors_total != 0:
            new_sundry_debtors_entry = {'ledger': 'Sundry Debtors', 'group': 'Asset', 'debit': Sundry_debtors_total, 'credit': '-'}
            new_ledgers_asset.append(new_sundry_debtors_entry)

        # Create new ledger entries for Sundry Creditors and add to the Liability section
        if Sundry_creditors_total != 0:
            new_sundry_creditors_entry = {'ledger': 'Sundry Creditors', 'group': 'Liability', 'debit': '-', 'credit': Sundry_creditors_total}
            new_ledgers_liability.append(new_sundry_creditors_entry)

        # Add the new ledger entries to the respective sections
        for entry in trial_balance:
            if entry['account_type'] == 'Asset':
                entry['ledgers'] += new_ledgers_asset
            elif entry['account_type'] == 'Liability':
                entry['ledgers'] += new_ledgers_liability




        context = {
            'trial_balance': trial_balance,
            "total": total,
            "from_date":from_date,
            "to_date":to_date,
            'current_fiscal_year':current_fiscal_year,
            'first_date': first_date,
            'last_date': last_date
        }

        return render(request, 'accounting/trial_balance.html', context)


    



class ProfitAndLoss(IsAdminMixin, TemplateView):
    template_name = "accounting/profit_and_loss.html"

    def get_context_data(self, **kwargs):
        from_date = self.request.GET.get('fromDate', None)
        to_date = self.request.GET.get('toDate', None)
        context = super().get_context_data(**kwargs)
        if from_date and to_date:
            expenses = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Expense", created_at__range=[from_date, to_date])
            revenues = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Revenue", created_at__range=[from_date, to_date])
        else:
            expenses = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Expense")
            revenues = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Revenue")

        expense_list, expense_total, revenue_list, revenue_total = ProfitAndLossData.get_data(revenues=revenues, expenses=expenses)


        context['expenses'] = expense_list
        context['expense_total'] = expense_total
        context['revenues'] = revenue_list
        context['revenue_total'] = revenue_total

        return context
    

# class BalanceSheet(IsAdminMixin, TemplateView):
#     template_name = "accounting/balance_sheet.html"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         asset_dict = {}
#         liability_dict = {}

#         assets = AccountChart.objects.filter(account_type='Asset')
#         for ledger in assets:
#             sub = AccountLedger.objects.filter(~Q(total_value=0), account_chart__group=ledger)
#             if sub:
#                 asset_dict[ledger.group] = sub


#         liabilities = AccountChart.objects.filter(Q(account_type="Liability") | Q(account_type="Equity") )
#         for ledger in liabilities:
#             sub = AccountLedger.objects.filter(~Q(total_value=0), account_chart__group=ledger)
#             if sub:
#                 liability_dict[ledger.group] = sub

#         asset_total = AccountLedger.objects.filter(account_chart__account_type='Asset').aggregate(Sum('total_value')).get('total_value__sum')
#         liability_total = AccountLedger.objects.filter(Q(account_chart__account_type="Liability") | Q(account_chart__account_type="Equity") )\
#                                     .aggregate(Sum('total_value')).get('total_value__sum')
        

#         """"""
#         expenses = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Expense")
#         revenues = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Revenue")
#         _, expense_total, _, revenue_total = ProfitAndLossData.get_data(revenues=revenues, expenses=expenses)
#         # print(revenue_total)
#         # print(expense_total)
#         """"""
#         # print(f"Revenue_total {revenue_total}")
#         # print(f"Expense_total {expense_total}")
#         if revenue_total > expense_total:
#             difference_sum = abs(revenue_total-expense_total)
#             context['lib_retained_earnings'] =  difference_sum
#             # context['lib_retained_earnings'] =  revenue_total
#             liability_total +=  difference_sum  #difference of expense and the sales
#             # print(liability_total)
#         else:
#             difference_sum = abs(revenue_total-expense_total)
#             context['asset_retained_earnings'] =  difference_sum
#             asset_total +=  difference_sum
#             # print(liability_total)
        
#         context['asset_total'] = asset_total
#         context['liability_total'] = liability_total
#         context['assets'] = asset_dict
#         context['liabilities'] =  liability_dict

#         return context

class BalanceSheet(IsAdminMixin, TemplateView):
    template_name = "accounting/balance_sheet.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        asset_dict = {}
        liability_dict = {}

        assets = AccountChart.objects.filter(account_type='Asset')
        for ledger in assets:
            sub = AccountLedger.objects.filter(~Q(total_value=0), account_chart__group=ledger)
            if sub:
                asset_dict[ledger.group] = sub


        liabilities = AccountChart.objects.filter(Q(account_type="Liability") | Q(account_type="Equity") )
        for ledger in liabilities:
            sub = AccountLedger.objects.filter(~Q(total_value=0), account_chart__group=ledger)
            if sub:
                liability_dict[ledger.group] = sub

        asset_total = AccountLedger.objects.filter(account_chart__account_type='Asset').aggregate(Sum('total_value')).get('total_value__sum')
        liability_total = AccountLedger.objects.filter(Q(account_chart__account_type="Liability") | Q(account_chart__account_type="Equity") )\
                                    .aggregate(Sum('total_value')).get('total_value__sum')
        

        """"""
        expenses = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Expense")
        revenues = AccountLedger.objects.filter(~Q(total_value=0), account_chart__account_type="Revenue")
        _, expense_total, _, revenue_total = ProfitAndLossData.get_data(revenues=revenues, expenses=expenses)

        sundry_debtors = AccountLedger.objects.filter(
            ~Q(total_value=0),
            account_chart__group="Sundry Debtors"
        ).aggregate(Sum('total_value'))['total_value__sum']

        # Calculate the total value for Sundry Creditors
        sundry_creditors = AccountLedger.objects.filter(
            ~Q(total_value=0),
            account_chart__group="Sundry Creditors"
        ).aggregate(Sum('total_value'))['total_value__sum']


        # print(revenue_total)
        # print(expense_total)
        """"""
        # print(f"Revenue_total {revenue_total}")
        # print(f"Expense_total {expense_total}")
        if revenue_total > expense_total:
            difference_sum = abs(revenue_total-expense_total)
            context['lib_retained_earnings'] =  difference_sum
            # context['lib_retained_earnings'] =  revenue_total
            liability_total +=  difference_sum  #difference of expense and the sales
            # print(liability_total)
        else:
            difference_sum = abs(revenue_total-expense_total)
            context['asset_retained_earnings'] =  difference_sum
            asset_total +=  difference_sum
            # print(liability_total)
        
        context['asset_total'] = asset_total
        context['liability_total'] = liability_total
        context['assets'] = asset_dict
        context['liabilities'] =  liability_dict
        context['sundry_debtors_total'] = sundry_debtors
        context['sundry_creditors_total'] = sundry_creditors

        return context


class DepreciationView(IsAdminMixin, View):

    def get(self, request):
        depreciations = Depreciation.objects.all()
        return render(request, 'accounting/depreciation_list.html', {'depreciations':depreciations})
    
# class PartyLedgerView(IsAdminMixin, View):
#     template_name = 'accounting/partyledger_list.html'
  
    # def get(self, request):
    #     # depreciations = Depreciation.objects.all()
    #     return render(request, 'accounting/partyledger_list.html')

    # def get(self, request):
    #     depreciations = Depreciation.objects.all()
    #     return render(request, 'accounting/depreciation_list.html', {'depreciations':depreciations})

class PartyLedgerView(View):
    template_name = 'accounting/partyledger_list.html'

    def get(self, request):
        search_query = request.GET.get('ledger_search', '')
        ledgers = AccountLedger.objects.filter(ledger_name__icontains=search_query)
        all_ledger_names = list(AccountLedger.objects.values_list('ledger_name', flat=True))

        context = {
            'ledgers': ledgers,
            'search_query': search_query,
            'ledger_names': all_ledger_names,
        }

        return render(request, self.template_name, context)
    
class PartyLedgerJournalView(CreateView):
    template_name = 'accounting/partyledgerjournal.html'

    def get(self, request, ledger_id):
     
        paid_from = AccountLedger.objects.filter(account_chart__group='Liquid Asset')
        
        # search_query = request.GET.get('ledger_search', '')
        paying_ledger = AccountLedger.objects.get(id=ledger_id)
      
        

        context = {
            'ledger': paying_ledger,
            'paid_from':paid_from
          
        }

        return render(request, self.template_name, context)
    
    def post(self, request, ledger_id):

        debit_ledger1 = request.POST.get('debit_ledger')
        selected_ledger = AccountLedger.objects.get(id=debit_ledger1)
        # print(selected_ledger)
        debit_ledger1 = request.POST.get('debit_ledger')
        # print(debit_ledger1)
        amount = request.POST.get('amount')
        particular = request.POST.get('particular')
        # journal_entry = TblJournalEntry.objects.create(employee_name=request.user.username, journal_total=amount)
        # print(journal_entry)

        journal_entry = TblJournalEntry.objects.create(employee_name=request.user.username, journal_total=amount)
       
        debit_ledger_id = ledger_id
        debit_ledger = AccountLedger.objects.get(pk=debit_ledger_id)
        print(debit_ledger_id)

        debit_particular = particular
        debit_amount = Decimal(amount)
        debit_ledger_type = debit_ledger.account_chart.account_type
   

        TblDrJournalEntry.objects.create(ledger=debit_ledger, journal_entry=journal_entry, particulars=debit_particular, debit_amount=debit_amount, paidfrom_ledger=selected_ledger)
        if debit_ledger_type in ['Asset', 'Expense']:
            debit_ledger.total_value =debit_ledger.total_value + debit_amount
            debit_ledger.save()
                

        elif debit_ledger_type in ['Liability', 'Revenue', 'Equity']:
            debit_ledger.total_value = debit_ledger.total_value - debit_amount
            debit_ledger.save()
                
        
        credit_ledger_id = debit_ledger1
        # print(credit_ledger_id)
        # credit_ledger1 = AccountLedger.objects.get(pk=debit_ledger)
        # print(credit_ledger1)
        credit_ledger = AccountLedger.objects.get(id=credit_ledger_id)
        print(credit_ledger)
        credit_particular = particular
        credit_amount = D(amount)
        credit_ledger_type = credit_ledger.account_chart.account_type
        TblCrJournalEntry.objects.create(ledger=credit_ledger, journal_entry=journal_entry, particulars=credit_particular, credit_amount=credit_amount, paidfrom_ledger=selected_ledger)
        if credit_ledger_type in ['Asset', 'Expense']:
            credit_ledger.total_value = credit_ledger.total_value - credit_amount
            credit_ledger.save()
         
        elif credit_ledger_type in ['Liability', 'Revenue', 'Equity']:
            credit_ledger.total_value = credit_ledger.total_value + credit_amount
            credit_ledger.save()
        current_page_url = reverse('ledger_detail', args=[ledger_id]) + f'?debit_ledger1={debit_ledger1}'
        
    
        return redirect(current_page_url)
    
    
class PartyLedgerJournal1View(CreateView):
    template_name = 'accounting/partyledgerjournal.html'

    def get(self, request, ledger_id):
     
        paid_from = AccountLedger.objects.filter(account_chart__group='Liquid Asset')
        
        # search_query = request.GET.get('ledger_search', '')
        paying_ledger = AccountLedger.objects.get(id=ledger_id)
      
        

        context = {
            'ledger': paying_ledger,
            'paid_from':paid_from
          
        }

        return render(request, self.template_name, context)
    
    def post(self, request, ledger_id):
        

        debit_ledger1 = request.POST.get('debit_ledger')
        selected_ledger = AccountLedger.objects.get(id=debit_ledger1)
        # print(selected_ledger)

        
        amount = request.POST.get('amount')
        particular = request.POST.get('particular')
        # journal_entry = TblJournalEntry.objects.create(employee_name=request.user.username, journal_total=amount)
        # print(journal_entry)

        journal_entry = TblJournalEntry.objects.create(employee_name=request.user.username, journal_total=amount)
       
        # debit_ledger_id = ledger_id
        debit_ledger = AccountLedger.objects.get(pk=debit_ledger1)
     

        debit_particular = particular
        debit_amount = Decimal(amount)
        debit_ledger_type = debit_ledger.account_chart.account_type
   

        TblDrJournalEntry.objects.create(ledger=debit_ledger, journal_entry=journal_entry, particulars=debit_particular, debit_amount=debit_amount, paidfrom_ledger=selected_ledger)
        if debit_ledger_type in ['Asset', 'Expense']:
            debit_ledger.total_value =debit_ledger.total_value + debit_amount
            debit_ledger.save()
                

        elif debit_ledger_type in ['Liability', 'Revenue', 'Equity']:
            debit_ledger.total_value = debit_ledger.total_value - debit_amount
            debit_ledger.save()
                
        
        credit_ledger_id = ledger_id
        # print(credit_ledger_id)
        # credit_ledger1 = AccountLedger.objects.get(pk=debit_ledger)
        # print(credit_ledger1)
        credit_ledger = AccountLedger.objects.get(id=credit_ledger_id)
        # print(credit_ledger)
        credit_particular = particular
        credit_amount = D(amount)
        credit_ledger_type = credit_ledger.account_chart.account_type
        TblCrJournalEntry.objects.create(ledger=credit_ledger, journal_entry=journal_entry, particulars=credit_particular, credit_amount=credit_amount, paidfrom_ledger=selected_ledger)
        if credit_ledger_type in ['Asset', 'Expense']:
            credit_ledger.total_value = credit_ledger.total_value - credit_amount
            credit_ledger.save()
         
        elif credit_ledger_type in ['Liability', 'Revenue', 'Equity']:
            credit_ledger.total_value = credit_ledger.total_value + credit_amount
            credit_ledger.save()
        current_page_url = reverse('ledger_detail', args=[ledger_id]) + f'?debit_ledger1={debit_ledger1}'
        return redirect(current_page_url)

# class LedgerDetailView(View):
#     template_name = 'accounting/ledger_detail.html'  # Replace with your actual template path

#     def get(self, request, ledger_id):
#         ledger = get_object_or_404(AccountLedger, id=ledger_id)
#         credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
#         total_credit = 0
#         total_debit = 0
#         debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)

#         from_date = request.GET.get('fromDate')
#         to_date = request.GET.get('toDate')
#         option = request.GET.get('option')

#         if from_date and to_date:


#             credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
#             debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])

#         for credit in credit_entries:
#             total_credit += credit.credit_amount

#         all_entries = sorted(
#             chain(credit_entries, debit_entries),
#             key=attrgetter('created_at')
#         )
#         print(all_entries)
#         for debit in debit_entries:
#             total_debit += debit.debit_amount
#         print(total_debit)
#         print(total_credit)
#         total_diff = total_debit - total_credit
#         opening_balance = 0
#         closing_balance = 0
#         if option == 'openclose':
#             total_diff1 = total_debit - total_credit
#             if total_diff < 0:
#                 opening_balance = abs(total_diff1)
#             else:
#                 closing_balance = total_diff1
#         # if total_diff < 0:
#         #     opening_balance = total_diff
#         # else:
#         neg = 0
#         if total_diff < 0:
#             neg = 1
#         elif total_diff == 0:
#             neg = 2
#         closing_balance = abs(total_diff)
        
        
#         # final_opening_balance = opening_balance
        
#         context = {
#             'ledger': ledger,
#             'entries': all_entries, 
#             'credit_entries': credit_entries,
#             'debit_entries': debit_entries,
#             'total_debit': total_debit,
#             'total_credit': total_credit,
#             'closing_balance': closing_balance,
#             'opening_balance': opening_balance,
#             'from_date': from_date,
#             'to_date': to_date,
#             'openclose': option == 'openclose',
#             'neg': neg,
            
#             # 'final_opening_balance' : final_opening_balance
#                    }
#         return render(request, self.template_name, context)

#latest_one
# class LedgerDetailView(View):
#     template_name = 'accounting/ledger_detail.html'  # Replace with your actual template path

#     def get(self, request, ledger_id):
#         ledger = get_object_or_404(AccountLedger, id=ledger_id)
#         credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
#         total_credit = 0
#         total_debit = 0
#         debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)

#         from_date = request.GET.get('fromDate')
#         to_date = request.GET.get('toDate')
#         option = request.GET.get('option')

#         if from_date and to_date:
#             credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
#             debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])

#         for credit in credit_entries:
#             total_credit += credit.credit_amount

#         all_entries = sorted(
#             chain(credit_entries, debit_entries),
#             key=attrgetter('created_at')
#         )

#         for debit in debit_entries:
#             total_debit += debit.debit_amount

#         total_diff = total_debit - total_credit
#         opening_balance = 0
#         closing_balance = 0
#         if option == 'openclose':
#             total_diff1 = total_debit - total_credit
#             if total_diff1 < 0:
#                 opening_balance = abs(total_diff1)
#             else:
#                 closing_balance = total_diff1

#         neg = 0
#         if total_diff < 0:
#             neg = 1
#         elif total_diff == 0:
#             neg = 2
#         closing_balance = abs(total_diff)

#         # Calculate the opening balance before filtering
#         if from_date:
#             opening_balance = 0
#             opening_entries = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__lt=from_date)
#             for entry in opening_entries:
#                 opening_balance += entry.credit_amount

#         context = {
#             'ledger': ledger,
#             'entries': all_entries,
#             'credit_entries': credit_entries,
#             'debit_entries': debit_entries,
#             'total_debit': total_debit,
#             'total_credit': total_credit,
#             'closing_balance': closing_balance,
#             'opening_balance': opening_balance,
#             'from_date': from_date,
#             'to_date': to_date,
#             'openclose': option == 'openclose',
#             'neg': neg,
#         }
#         return render(request, self.template_name, context)

# from django.db.models import Sum, F, DecimalField, Q, Value
# from django.db.models import Min, Max
# from django.utils import timezone  as django_timezone
# from pytz import timezone as pytz_timezone
# class LedgerDetailView(View):
#     template_name = 'accounting/ledger_detail.html'  # Replace with your actual template path

#     def get(self, request, ledger_id):
#         kathmandu_timezone = pytz_timezone('Asia/Kathmandu')
#         ledger = get_object_or_404(AccountLedger, id=ledger_id)
      
#         credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
#         total_credit = 0
#         total_debit = 0
#         debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
#         from_date = request.GET.get('fromDate')
#         to_date = request.GET.get('toDate')
#         option = request.GET.get('option')
#         current_fiscal_year = Organization.objects.last().current_fiscal_year
#         if from_date and to_date:
#             credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
#             debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])
#         unique_journal_ids = debit_entries.values_list('journal_entry_id', flat=True).distinct()
#         unique_journal_ids1 = credit_entries.values_list('journal_entry_id', flat=True).distinct()
      
       
#         details = []
#         for journal_id1 in unique_journal_ids1:
           
#             debit_entries_testing = TblDrJournalEntry.objects.filter(journal_entry_id=journal_id1)
            
                
#             ledger_names = [debit_entry.ledger.ledger_name for debit_entry in debit_entries_testing]
#             ledger_amount = [debit_entry.debit_amount for debit_entry in debit_entries_testing]
         

#             debit_entries_test3 = TblCrJournalEntry.objects.filter(Q(journal_entry_id=journal_id1) & Q(ledger_id=ledger_id))
#             date = [debit_entry.created_at.astimezone(kathmandu_timezone).strftime("%Y-%m-%d %H:%M:%S") for debit_entry in debit_entries_test3]
#             credit  = [debit_entry.credit_amount for debit_entry in debit_entries_test3]
#             # print(credit)
#             particulars  = [debit_entry.particulars for debit_entry in debit_entries_test3]
           
#             payers_info = ', '.join([f'{name} ({amount})' for name, amount in zip(ledger_names, ledger_amount)])
           
           
#             for credit_entry in credit_entries:
                
             
#                 # Create a dictionary for this ledger
#                 debit_ledger_entry = {
#                         'journal_id': journal_id1,
#                         # 'payers': ', '.join(ledger_names),  # Join ledger names with a comma
#                         'payers': payers_info,
#                         'date': date,
#                         'particulars': particulars,
#                         'debit': Decimal('0'),
#                         'credit': credit

#                     }

#             details.append(debit_ledger_entry)

#         for journal_id1 in unique_journal_ids:
#             debit_entries_test1 = TblCrJournalEntry.objects.filter(journal_entry_id=journal_id1)
#             ledger_names = [debit_entry.ledger.ledger_name for debit_entry in debit_entries_test1]
#             ledger_amount = [debit_entry.credit_amount for debit_entry in debit_entries_test1]
#             payers_info = ', '.join([f'{name} ({amount})' for name, amount in zip(ledger_names, ledger_amount)])

#             debit_entries_test2 = TblDrJournalEntry.objects.filter(Q(journal_entry_id=journal_id1) & Q(ledger_id=ledger_id))
#             date = [debit_entry.created_at.astimezone(kathmandu_timezone).strftime("%Y-%m-%d %H:%M:%S")  for debit_entry in debit_entries_test2]
#             debit  = [debit_entry.debit_amount for debit_entry in debit_entries_test2]
#             particulars  = [debit_entry.particulars for debit_entry in debit_entries_test2]

#             for debit_entry in debit_entries:
             
#                 # Create a dictionary for this ledger
#                 debit_ledger_entry = {
#                         'journal_id': journal_id1,
#                         # 'payers': ', '.join(ledger_names),  # Join ledger names with a comma
#                         'payers': payers_info,
#                         'date': date,
#                         'particulars': particulars,
#                         'debit': debit,
#                         'credit': Decimal('0')

#                     }

#             details.append(debit_ledger_entry)
        
  

#         sorted_details = sorted(details, key=lambda x: x['date'])




#         # Check the count of credit entries
#         credit_entry_count = credit_entries.count()

#         # Check the count of debit entries
#         debit_entry_count = debit_entries.count()

#         # Initialize variables as None
#         first_date = None
#         last_date = None


#         if credit_entry_count > 0 or debit_entry_count > 0:
#             credit_date_range = credit_entries.aggregate(
#                 first_credit_date=Min('created_at'),
#                 last_credit_date=Max('created_at')
#             )

#             # Calculate the first and last dates for debit entries
#             debit_date_range = debit_entries.aggregate(
#                 first_debit_date=Min('created_at'),
#                 last_debit_date=Max('created_at')
#             )

#             first_credit_date = credit_date_range['first_credit_date'] or django_timezone.datetime.max.replace(tzinfo=django_timezone.utc)
#             last_credit_date = credit_date_range['last_credit_date'] or django_timezone.datetime.min.replace(tzinfo=django_timezone.utc)
#             first_debit_date = debit_date_range['first_debit_date'] or django_timezone.datetime.max.replace(tzinfo=django_timezone.utc)
#             last_debit_date = debit_date_range['last_debit_date'] or django_timezone.datetime.min.replace(tzinfo=django_timezone.utc)

#             # Determine the overall date range
#             first_date = min(first_credit_date, first_debit_date) 
#             last_date = max(last_credit_date, last_debit_date) 

#         if from_date and to_date:
#             credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
#             debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])

#         for credit in credit_entries:
#             total_credit += credit.credit_amount

#         all_entries = sorted(
#             chain(credit_entries, debit_entries),
#             key=attrgetter('created_at')
#         )

#         for debit in debit_entries:
#             total_debit += debit.debit_amount

#         total_diff = total_debit - total_credit
#         opening_balance_credit = 0
#         opening_balance_debit = 0
#         closing_balance = 0
#         if option == 'openclose':
#             total_diff1 = total_debit - total_credit
#             if total_diff1 < 0:
#                 opening_balance_credit = abs(total_diff1)
#             else:
#                 closing_balance = total_diff1

#         neg = 0
#         if total_diff < 0:
#             neg = 1
#         elif total_diff == 0:
#             neg = 2
#         closing_balance = abs(total_diff)

#         # Calculate the opening balance before filtering
#         if from_date:
#             opening_balance_credit = 0
#             opening_balance_debit = 0
#             opening_entries_credit = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__lt=from_date)
#             opening_entries_debit = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__lt=from_date)
            
#             for entry in opening_entries_credit:
#                 opening_balance_credit += entry.credit_amount
#             for entry in opening_entries_debit:
#                 opening_balance_debit += entry.debit_amount

#         context = {
#             'ledger': ledger,
#             'entries': all_entries,
#             'credit_entries': credit_entries,
#             'debit_entries': debit_entries,
#             'total_debit': total_debit,
#             'total_credit': total_credit,
#             'closing_balance': closing_balance,
#             'opening_balance': {'credit': opening_balance_credit, 'debit': opening_balance_debit},
#             'from_date': from_date,
#             'to_date': to_date,
#             'openclose': option == 'openclose',
#             'neg': neg,
#             'current_fiscal_year':current_fiscal_year,
#             'first_credit_date': first_date,
#             'last_credit_date': last_date,
#             'sorted_details':sorted_details
    
#         }
#         return render(request, self.template_name, context)
    
from datetime import datetime, timedelta
from django.db.models import Sum, F, DecimalField, Q, Value
from django.db.models import Min, Max
from django.utils import timezone  as django_timezone
from pytz import timezone as pytz_timezone


class LedgerDetailView(View):
    template_name = 'accounting/ledger_detail.html'  # Replace with your actual template path

    def get(self, request, ledger_id):
        kathmandu_timezone = pytz_timezone('Asia/Kathmandu')
        ledger = get_object_or_404(AccountLedger, id=ledger_id)
        current_date = datetime.today().date()
        tomorrow_date = current_date + timedelta(days=1) 
        credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__range=[current_date, tomorrow_date])
        # credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
        total_credit = 0
        total_debit = 0
        debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__range=[current_date, tomorrow_date])
        # debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')
        print(to_date)
        
        option = request.GET.get('option')
        current_fiscal_year = Organization.objects.last().current_fiscal_year
        if from_date and to_date:
            to_date_str = request.GET.get('toDate')
            
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            to_date += timedelta(days=1)
            credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
            debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
            credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
            debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])
        unique_journal_ids = debit_entries.values_list('journal_entry_id', flat=True).distinct()
        unique_journal_ids1 = credit_entries.values_list('journal_entry_id', flat=True).distinct()
      
       
        details = []
        for journal_id1 in unique_journal_ids1:
           
            debit_entries_testing = TblDrJournalEntry.objects.filter(journal_entry_id=journal_id1)
            
                
            ledger_names = [debit_entry.ledger.ledger_name for debit_entry in debit_entries_testing]
            ledger_amount = [debit_entry.debit_amount for debit_entry in debit_entries_testing]
         

            debit_entries_test3 = TblCrJournalEntry.objects.filter(Q(journal_entry_id=journal_id1) & Q(ledger_id=ledger_id))
            date = [debit_entry.created_at.astimezone(kathmandu_timezone).strftime("%Y-%m-%d %H:%M:%S") for debit_entry in debit_entries_test3]
            credit  = [debit_entry.credit_amount for debit_entry in debit_entries_test3]
            # print(credit)
            particulars  = [debit_entry.particulars for debit_entry in debit_entries_test3]
           
            payers_info = ', '.join([f'{name} ({amount})' for name, amount in zip(ledger_names, ledger_amount)])
           
           
            for credit_entry in credit_entries:
                
             
                # Create a dictionary for this ledger
                debit_ledger_entry = {
                        'journal_id': journal_id1,
                        # 'payers': ', '.join(ledger_names),  # Join ledger names with a comma
                        'payers': payers_info,
                        'date': date,
                        'particulars': particulars,
                        'debit': Decimal('0'),
                        'credit': credit

                    }

            details.append(debit_ledger_entry)

        for journal_id1 in unique_journal_ids:
            debit_entries_test1 = TblCrJournalEntry.objects.filter(journal_entry_id=journal_id1)
            ledger_names = [debit_entry.ledger.ledger_name for debit_entry in debit_entries_test1]
            ledger_amount = [debit_entry.credit_amount for debit_entry in debit_entries_test1]
            payers_info = ', '.join([f'{name} ({amount})' for name, amount in zip(ledger_names, ledger_amount)])

            debit_entries_test2 = TblDrJournalEntry.objects.filter(Q(journal_entry_id=journal_id1) & Q(ledger_id=ledger_id))
            date = [debit_entry.created_at.astimezone(kathmandu_timezone).strftime("%Y-%m-%d %H:%M:%S")  for debit_entry in debit_entries_test2]
            debit  = [debit_entry.debit_amount for debit_entry in debit_entries_test2]
            particulars  = [debit_entry.particulars for debit_entry in debit_entries_test2]

            for debit_entry in debit_entries:
             
                # Create a dictionary for this ledger
                debit_ledger_entry = {
                        'journal_id': journal_id1,
                        # 'payers': ', '.join(ledger_names),  # Join ledger names with a comma
                        'payers': payers_info,
                        'date': date,
                        'particulars': particulars,
                        'debit': debit,
                        'credit': Decimal('0')

                    }

            details.append(debit_ledger_entry)
        
  

        sorted_details = sorted(details, key=lambda x: x['date'])




        # Check the count of credit entries
        credit_entry_count = credit_entries.count()

        # Check the count of debit entries
        debit_entry_count = debit_entries.count()

        # Initialize variables as None
        first_date = None
        last_date = None


        if credit_entry_count > 0 or debit_entry_count > 0:
            credit_date_range = credit_entries.aggregate(
                first_credit_date=Min('created_at'),
                last_credit_date=Max('created_at')
            )

            # Calculate the first and last dates for debit entries
            debit_date_range = debit_entries.aggregate(
                first_debit_date=Min('created_at'),
                last_debit_date=Max('created_at')
            )

            first_credit_date = credit_date_range['first_credit_date'] or django_timezone.datetime.max.replace(tzinfo=django_timezone.utc)
            last_credit_date = credit_date_range['last_credit_date'] or django_timezone.datetime.min.replace(tzinfo=django_timezone.utc)
            first_debit_date = debit_date_range['first_debit_date'] or django_timezone.datetime.max.replace(tzinfo=django_timezone.utc)
            last_debit_date = debit_date_range['last_debit_date'] or django_timezone.datetime.min.replace(tzinfo=django_timezone.utc)

            # Determine the overall date range
            first_date = min(first_credit_date, first_debit_date) 
            last_date = max(last_credit_date, last_debit_date) 

        print('first_date_from_loop', first_date)
        if from_date and to_date:
            credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
            debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])

        for credit in credit_entries:
            total_credit += credit.credit_amount

        all_entries = sorted(
            chain(credit_entries, debit_entries),
            key=attrgetter('created_at')
        )

        for debit in debit_entries:
            total_debit += debit.debit_amount

        total_diff = total_debit - total_credit
        opening_balance_credit = 0
        opening_balance_debit = 0
        closing_balance = 0

        yesterday = current_date - timedelta(days=1)

        earliest_credit_date = TblCrJournalEntry.objects.aggregate(earliest_credit_date=Min('created_at'))['earliest_credit_date']
        earliest_debit_date = TblDrJournalEntry.objects.aggregate(earliest_debit_date=Min('created_at'))['earliest_debit_date']

# Determine the overall first date
        first_date1 = min(earliest_credit_date, earliest_debit_date)

        print('first_date_from_method', first_date1)

        # Filter credit entries from 'first_date' to 'yesterday'
        opening_credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__range=[first_date1, current_date])

        # Aggregate the sum of credit amounts
        opening_balance_credit = opening_credit_entries.aggregate(total_credit=Sum('credit_amount'))['total_credit'] or 0

        opening_debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__range=[first_date1, current_date])

        # Aggregate the sum of credit amounts
        opening_balance_debit = opening_debit_entries.aggregate(total_debit=Sum('debit_amount'))['total_debit'] or 0

        
        if option == 'openclose':
            total_diff1 = total_debit - total_credit
            if total_diff1 < 0:
                opening_balance_credit = abs(total_diff1)
            else:
                closing_balance = total_diff1

        neg = 0
        if total_diff < 0:
            neg = 1
        elif total_diff == 0:
            neg = 2
        closing_balance = abs(total_diff)

        # Calculate the opening balance before filtering
        if from_date:
            to_date_str = request.GET.get('toDate')        
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
            to_date += timedelta(days=1)
            opening_balance_credit = 0
            opening_balance_debit = 0
            opening_entries_credit = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__lt=from_date)
            opening_entries_debit = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__lt=from_date)
            
            for entry in opening_entries_credit:
                opening_balance_credit += entry.credit_amount
            for entry in opening_entries_debit:
                opening_balance_debit += entry.debit_amount
            to_date -= timedelta(days=1)

            to_date = to_date.strftime('%Y-%m-%d')

    #     if from_date:
    # # Initialize opening balances
    #         to_date_str = request.GET.get('toDate')
            
    #         to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
    #         to_date += timedelta(days=1)
    #         opening_balance_credit = 0
    #         opening_balance_debit = 0

    #         # Filter credit entries before the entered date
    #         opening_entries_credit = TblCrJournalEntry.objects.filter(ledger=ledger)
    #         opening_entries_debit = TblDrJournalEntry.objects.filter(ledger=ledger)

    #         # Calculate the sum of credit and debit amounts before the entered date
    #         opening_balance_credit += opening_entries_credit.aggregate(total_credit=Sum('credit_amount'))['total_credit'] or 0
    #         opening_balance_debit += opening_entries_debit.aggregate(total_debit=Sum('debit_amount'))['total_debit'] or 0
    #         print(opening_balance_credit)
    #         print(opening_balance_debit)

    #         # Calculate the sum of credit and debit amounts within the entered date range
    #         credit_entries_within_range = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__range=[from_date, to_date])
    #         debit_entries_within_range = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__range=[from_date, to_date])

    #         total_credit_within_range = credit_entries_within_range.aggregate(total_credit=Sum('credit_amount'))['total_credit'] or 0
    #         total_debit_within_range = debit_entries_within_range.aggregate(total_debit=Sum('debit_amount'))['total_debit'] or 0

    #         # Subtract the sum within the date range from the sum before the date
    #         opening_balance_credit -= total_credit_within_range
    #         opening_balance_debit -= total_debit_within_range
    #         to_date -= timedelta(days=1)

    #         to_date = to_date.strftime('%Y-%m-%d')

        context = {
            'ledger': ledger,
            'entries': all_entries,
            'credit_entries': credit_entries,
            'debit_entries': debit_entries,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'closing_balance': closing_balance,
            'opening_balance': {'credit': opening_balance_credit, 'debit': opening_balance_debit},
            'from_date': from_date,
            'to_date': to_date,
            'openclose': option == 'openclose',
            'neg': neg,
            'current_fiscal_year':current_fiscal_year,
            'first_credit_date': first_date,
            'last_credit_date': last_date,
            'sorted_details':sorted_details
    
        }
        return render(request, self.template_name, context)
    


@api_view(['POST'])
def end_fiscal_year(request):
        org = Organization.objects.first()
        fiscal_year = org.get_fiscal_year()
        ledgers = AccountLedger.objects.all()
        sub_ledgers = AccountSubLedger.objects.all()
        accumulated_depn = AccountLedger.objects.get(ledger_name='Accumulated Depreciation')


        for sub in sub_ledgers:
            FiscalYearSubLedger.objects.create(sub_ledger_name=sub.sub_ledger_name, total_value=sub.total_value, fiscal_year=fiscal_year, ledger=sub.ledger)

        for led in ledgers:
            FiscalYearLedger.objects.create(ledger_name=led.ledger_name, total_value=led.total_value,fiscal_year=fiscal_year, account_chart=led.account_chart)
            if led.account_chart.account_type in ['Revenue', 'Expense']:
                for sub in led.accountsubledger_set.all():
                    if sub.ledger.account_chart.group == 'Depreciation':
                        accumulated_depn.total_value += sub.total_value
                        accumulated_depn.save()
                    sub.total_value=0
                    sub.save()
                if not led.ledger_name == 'Accumulated Depreciation':
                    led.total_value = 0
                    led.save()
                    # AccountSubLedger.objects.create(sub_ledger_name=f'{sub.sub_ledger_name} for {fiscal_year}', total_value=sub.total_value, ledger=accumulated_depn)
                    
        depreciations = Depreciation.objects.filter(fiscal_year=fiscal_year)

        org.start_year+=1
        org.end_year += 1

        org.save()

        for depn in depreciations:
            amount = float(depn.net_amount)
            percentage = depn.item.asset.depreciation_pool.percentage
            bill_date = depn.item.asset_purchase.bill_date
            depreciation_amount, bs_date = calculate_depreciation(amount, percentage, bill_date)
            net_amount = amount-depreciation_amount
            Depreciation.objects.create(miti=bs_date,depreciation_amount=depreciation_amount, net_amount=net_amount, item=depn.item, ledger=depn.ledger)
            depreciation_amount = D(depreciation_amount)
            depn_subledger = AccountSubLedger.objects.get(sub_ledger_name=f'{depn.item.asset.title} Depreciation')
            depn_subledger.total_value += depreciation_amount
            depn_subledger.save()


            depn_ledger = depn_subledger.ledger
            depn_ledger.total_value+= depreciation_amount
            depn_ledger.save()

            asset_ledger = depn.ledger
            asset_ledger.total_value -= depreciation_amount
            asset_ledger.save()

            asset_ledger = AccountSubLedger.objects.get(sub_ledger_name=depn.item.asset.title, ledger__account_chart__account_type='Asset')
            asset_ledger.total_value -= depreciation_amount
            asset_ledger.save()
        
        return Response({})



from django.db.models import Sum



class SundryDebtorsLedgersView(View):
    template_name = 'accounting/sundry_debtors.html'

    def get(self, request):
        # Query the AccountLedger model to get all ledgers with group "Sundry Debtors"
        sundry_debtors_ledgers = AccountLedger.objects.filter(account_chart__group="Sundry Debtors")

        # Get the filter parameters from the request
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')
        option = request.GET.get('option')
        current_fiscal_year = Organization.objects.last().current_fiscal_year

        # Create a list to store ledger details
        ledger_details = []

        total_d = 0  # for storing the all total of the debit of the entries in ledger_details
        total_c = 0  # for storing the all total of the credit of the entries in ledger_details

        # Initialize variables for overall date range
        first_date = None
        last_date = None

        # Calculate debit and credit totals for each ledger for the selected date
        for ledger in sundry_debtors_ledgers:
            # Filter debit and credit entries by date range
            debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
            credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)

            # Check the count of credit entries
            credit_entry_count = credit_entries.count()

            # Check the count of debit entries
            debit_entry_count = debit_entries.count()

            if credit_entry_count > 0 or debit_entry_count > 0:
                # Calculate the first and last dates for credit entries
                credit_date_range = credit_entries.aggregate(
                    first_credit_date=Min('created_at'),
                    last_credit_date=Max('created_at')
                )

                # Calculate the first and last dates for debit entries
                debit_date_range = debit_entries.aggregate(
                    first_debit_date=Min('created_at'),
                    last_debit_date=Max('created_at')
                )

                # Determine the minimum date for this ledger (comparing debit and credit)
                ledger_first_date = None

                if credit_date_range['first_credit_date'] and debit_date_range['first_debit_date']:
                    ledger_first_date = min(
                        credit_date_range['first_credit_date'],
                        debit_date_range['first_debit_date']
                    )
                elif credit_date_range['first_credit_date']:
                    ledger_first_date = credit_date_range['first_credit_date']
                elif debit_date_range['first_debit_date']:
                    ledger_first_date = debit_date_range['first_debit_date']

                # Update the overall minimum date
                if ledger_first_date and (first_date is None or ledger_first_date < first_date):
                    first_date = ledger_first_date

                # Determine the maximum date for this ledger (comparing debit and credit)
                ledger_last_date = None

                if credit_date_range['last_credit_date'] and debit_date_range['last_debit_date']:
                    ledger_last_date = max(
                        credit_date_range['last_credit_date'],
                        debit_date_range['last_debit_date']
                    )
                elif credit_date_range['last_credit_date']:
                    ledger_last_date = credit_date_range['last_credit_date']
                elif debit_date_range['last_debit_date']:
                    ledger_last_date = debit_date_range['last_debit_date']

                # Update the overall maximum date
                if ledger_last_date and (last_date is None or ledger_last_date > last_date):
                    last_date = ledger_last_date

            # Rest of your code for calculating totals and appending to ledger_details
            if from_date and to_date:
                from_date = request.GET.get('fromDate')
                to_date_str = request.GET.get('toDate')        
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
                to_date += timedelta(days=1)
                debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])
                credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
                to_date -= timedelta(days=1)
                to_date = to_date.strftime('%Y-%m-%d')

            total_credit=0
            total_debit=0
                # Calculate debit total for the selected date
            for credit in credit_entries:
                total_credit += credit.credit_amount

                # Calculate credit total for the selected date
            for debit in debit_entries:
                total_debit += debit.debit_amount

            if total_debit != 0 or total_credit != 0:
                ledger_details.append({
                    'ledger_name': ledger.ledger_name,
                    'debit_total': total_debit,
                    'credit_total': total_credit,
                })
                    
                    #Update the overall totals
            total_d += total_debit
            total_c += total_credit

        balance = total_d - total_c
        if balance <= 0:
            c = 0  # tells that it is negative
        else:
            c = 1  # tells that it is positive

        new_balance = abs(balance)

        # Render a template with the retrieved ledger details and filter parameters
        return render(request, self.template_name, {
            'ledger_details': ledger_details,
            'from_date': from_date,
            'to_date': to_date,
            'option': option,
            'total_d': total_d,
            'total_c': total_c,
            'openclose': option == 'openclose',
            'balance': new_balance,
            'c': c,
            'current_fiscal_year': current_fiscal_year,
            'first_date': first_date,
            'last_date': last_date
        })
    
# class SundryDebtorsLedgersView(View):
#     template_name = 'accounting/sundry_debtors.html'

#     def get(self, request):
#         # Query the AccountLedger model to get all ledgers with group "Sundry Debtors"
#         sundry_debtors_ledgers = AccountLedger.objects.filter(account_chart__group="Sundry Debtors")

#         # Get the filter parameters from the request
#         from_date = request.GET.get('fromDate')
#         to_date = request.GET.get('toDate')
#         option = request.GET.get('option')
#         current_fiscal_year = Organization.objects.last().current_fiscal_year
#         current_date = datetime.today().date()
#         tomorrow_date = current_date + timedelta(days=1)
#         # Create a list to store ledger details
#         ledger_details = []

#         total_d = 0  # for storing the all total of the debit of the entries in ledger_details
#         total_c = 0  # for storing the all total of the credit of the entries in ledger_details

#         # Initialize variables for overall date range
#         first_date = None
#         last_date = None

#         # Calculate debit and credit totals for each ledger for the selected date
#         for ledger in sundry_debtors_ledgers:
#             # Filter debit and credit entries by date range
#             debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__range=[current_date, tomorrow_date])
#             credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__range=[current_date, tomorrow_date])


#             # Check the count of credit entries
#             credit_entry_count = credit_entries.count()

#             # Check the count of debit entries
#             debit_entry_count = debit_entries.count()

#             if credit_entry_count > 0 or debit_entry_count > 0:
#                 # Calculate the first and last dates for credit entries
#                 credit_date_range = credit_entries.aggregate(
#                     first_credit_date=Min('created_at'),
#                     last_credit_date=Max('created_at')
#                 )

#                 # Calculate the first and last dates for debit entries
#                 debit_date_range = debit_entries.aggregate(
#                     first_debit_date=Min('created_at'),
#                     last_debit_date=Max('created_at')
#                 )

#                 # Determine the minimum date for this ledger (comparing debit and credit)
#                 ledger_first_date = None

#                 if credit_date_range['first_credit_date'] and debit_date_range['first_debit_date']:
#                     ledger_first_date = min(
#                         credit_date_range['first_credit_date'],
#                         debit_date_range['first_debit_date']
#                     )
#                 elif credit_date_range['first_credit_date']:
#                     ledger_first_date = credit_date_range['first_credit_date']
#                 elif debit_date_range['first_debit_date']:
#                     ledger_first_date = debit_date_range['first_debit_date']

#                 # Update the overall minimum date
#                 if ledger_first_date and (first_date is None or ledger_first_date < first_date):
#                     first_date = ledger_first_date

#                 # Determine the maximum date for this ledger (comparing debit and credit)
#                 ledger_last_date = None

#                 if credit_date_range['last_credit_date'] and debit_date_range['last_debit_date']:
#                     ledger_last_date = max(
#                         credit_date_range['last_credit_date'],
#                         debit_date_range['last_debit_date']
#                     )
#                 elif credit_date_range['last_credit_date']:
#                     ledger_last_date = credit_date_range['last_credit_date']
#                 elif debit_date_range['last_debit_date']:
#                     ledger_last_date = debit_date_range['last_debit_date']

#                 # Update the overall maximum date
#                 if ledger_last_date and (last_date is None or ledger_last_date > last_date):
#                     last_date = ledger_last_date

#             # Rest of your code for calculating totals and appending to ledger_details
#             if from_date and to_date:
#                 debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
#                 credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
#                 from_date = request.GET.get('fromDate')
#                 to_date_str = request.GET.get('toDate')        
#                 to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
#                 to_date += timedelta(days=1)
#                 debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])
#                 credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
#                 to_date -= timedelta(days=1)

#                 to_date = to_date.strftime('%Y-%m-%d')

#             total_credit=0
#             total_debit=0
#                 # Calculate debit total for the selected date
#             for credit in credit_entries:
#                 total_credit += credit.credit_amount

#                 # Calculate credit total for the selected date
#             for debit in debit_entries:
#                 total_debit += debit.debit_amount

#             if total_debit != 0 or total_credit != 0:
#                 ledger_details.append({
#                     'ledger_name': ledger.ledger_name,
#                     'debit_total': total_debit,
#                     'credit_total': total_credit,
#                 })
                    
#                     #Update the overall totals
#             total_d += total_debit
#             total_c += total_credit

#         balance = total_d - total_c
#         if balance <= 0:
#             c = 0  # tells that it is negative
#         else:
#             c = 1  # tells that it is positive

#         new_balance = abs(balance)

        # opeining_debit_entries = 
        # all_time_balance_debit = opening_debit_entries.aggregate(total_debit=Sum('debit_amount'))['total_debit'] or 0
        # all_time_balance_credit = opening_credit_entries.aggregate(total_debit=Sum('debit_amount'))['total_debit'] or 0


        # Render a template with the retrieved ledger details and filter parameters
        # return render(request, self.template_name, {
        #     'ledger_details': ledger_details,
        #     'from_date': from_date,
        #     'to_date': to_date,
        #     'option': option,
        #     'total_d': total_d,
        #     'total_c': total_c,
        #     'openclose': option == 'openclose',
        #     'balance': new_balance,
        #     'c': c,
        #     'current_fiscal_year': current_fiscal_year,
        #     'first_date': first_date,
        #     'last_date': last_date
        # })

class SundryCreditorsLedgersView(View):
    template_name = 'accounting/sundry_creditors.html'

    def get(self, request):
        # Query the AccountLedger model to get all ledgers with group "Sundry Debtors"
        sundry_creditors_ledgers = AccountLedger.objects.filter(account_chart__group="Sundry Creditors")

        # Get the filter parameters from the request
        from_date = request.GET.get('fromDate')
        to_date = request.GET.get('toDate')
        option = request.GET.get('option')
        current_fiscal_year = Organization.objects.last().current_fiscal_year

        # Create a list to store ledger details
        ledger_details = []

        total_d = 0  # for storing the all total of the debit of the entries in ledger_details
        total_c = 0  # for storing the all total of the credit of the entries in ledger_details

        # Initialize variables for overall date range
        first_date = None
        last_date = None

        # Calculate debit and credit totals for each ledger for the selected date
        for ledger in sundry_creditors_ledgers:
            # Filter debit and credit entries by date range
            debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
            credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)

            # Check the count of credit entries
            credit_entry_count = credit_entries.count()

            # Check the count of debit entries
            debit_entry_count = debit_entries.count()

            if credit_entry_count > 0 or debit_entry_count > 0:
                # Calculate the first and last dates for credit entries
                credit_date_range = credit_entries.aggregate(
                    first_credit_date=Min('created_at'),
                    last_credit_date=Max('created_at')
                )

                # Calculate the first and last dates for debit entries
                debit_date_range = debit_entries.aggregate(
                    first_debit_date=Min('created_at'),
                    last_debit_date=Max('created_at')
                )

                # Determine the minimum date for this ledger (comparing debit and credit)
                ledger_first_date = None

                if credit_date_range['first_credit_date'] and debit_date_range['first_debit_date']:
                    ledger_first_date = min(
                        credit_date_range['first_credit_date'],
                        debit_date_range['first_debit_date']
                    )
                elif credit_date_range['first_credit_date']:
                    ledger_first_date = credit_date_range['first_credit_date']
                elif debit_date_range['first_debit_date']:
                    ledger_first_date = debit_date_range['first_debit_date']

                # Update the overall minimum date
                if ledger_first_date and (first_date is None or ledger_first_date < first_date):
                    first_date = ledger_first_date

                # Determine the maximum date for this ledger (comparing debit and credit)
                ledger_last_date = None

                if credit_date_range['last_credit_date'] and debit_date_range['last_debit_date']:
                    ledger_last_date = max(
                        credit_date_range['last_credit_date'],
                        debit_date_range['last_debit_date']
                    )
                elif credit_date_range['last_credit_date']:
                    ledger_last_date = credit_date_range['last_credit_date']
                elif debit_date_range['last_debit_date']:
                    ledger_last_date = debit_date_range['last_debit_date']

                # Update the overall maximum date
                if ledger_last_date and (last_date is None or ledger_last_date > last_date):
                    last_date = ledger_last_date

            # Rest of your code for calculating totals and appending to ledger_details
            if from_date and to_date:
                from_date = request.GET.get('fromDate')
                to_date_str = request.GET.get('toDate')        
                to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
                to_date += timedelta(days=1)
                debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])
                credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
                to_date -= timedelta(days=1)
                to_date = to_date.strftime('%Y-%m-%d')

            total_credit=0
            total_debit=0
                # Calculate debit total for the selected date
            for credit in credit_entries:
                total_credit += credit.credit_amount

                # Calculate credit total for the selected date
            for debit in debit_entries:
                total_debit += debit.debit_amount

            if total_debit != 0 or total_credit != 0:
                ledger_details.append({
                    'ledger_name': ledger.ledger_name,
                    'debit_total': total_debit,
                    'credit_total': total_credit,
                })
                    
                    #Update the overall totals
            total_d += total_debit
            total_c += total_credit

        balance = total_d - total_c
        if balance <= 0:
            c = 0  # tells that it is negative
        else:
            c = 1  # tells that it is positive

        new_balance = abs(balance)

        # Render a template with the retrieved ledger details and filter parameters
        return render(request, self.template_name, {
            'ledger_details': ledger_details,
            'from_date': from_date,
            'to_date': to_date,
            'option': option,
            'total_d': total_d,
            'total_c': total_c,
            'openclose': option == 'openclose',
            'balance': new_balance,
            'c': c,
            'current_fiscal_year': current_fiscal_year,
            'first_date': first_date,
            'last_date': last_date
        })

    
# class SundryCreditorsLedgersView(View):
#     template_name = 'accounting/sundry_creditors.html'

#     def get(self, request):
#         # Query the AccountLedger model to get all ledgers with group "Sundry Debtors"
#         sundry_creditors_ledgers = AccountLedger.objects.filter(account_chart__group="Sundry Creditors")

#         # Get the filter parameters from the request
#         from_date = request.GET.get('fromDate')
#         to_date = request.GET.get('toDate')
#         option = request.GET.get('option')
#         current_fiscal_year = Organization.objects.last().current_fiscal_year

#         # Create a list to store ledger details
#         ledger_details = []

#         total_d = 0  # for storing the all total of the debit of the entries in ledger_details
#         total_c = 0  # for storing the all total of the credit of the entries in ledger_details

#         # Initialize variables for overall date range
#         first_date = None
#         last_date = None
#         current_date = datetime.today().date()
#         tomorrow_date = current_date + timedelta(days=1)

#         # Calculate debit and credit totals for each ledger for the selected date
#         for ledger in sundry_creditors_ledgers:
#             # Filter debit and credit entries by date range
#             debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger, created_at__range=[current_date, tomorrow_date])
#             credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger, created_at__range=[current_date, tomorrow_date])

#             # Check the count of credit entries
#             credit_entry_count = credit_entries.count()

#             # Check the count of debit entries
#             debit_entry_count = debit_entries.count()

#             if credit_entry_count > 0 or debit_entry_count > 0:
#                 # Calculate the first and last dates for credit entries
#                 credit_date_range = credit_entries.aggregate(
#                     first_credit_date=Min('created_at'),
#                     last_credit_date=Max('created_at')
#                 )

#                 # Calculate the first and last dates for debit entries
#                 debit_date_range = debit_entries.aggregate(
#                     first_debit_date=Min('created_at'),
#                     last_debit_date=Max('created_at')
#                 )

#                 # Determine the minimum date for this ledger (comparing debit and credit)
#                 ledger_first_date = None

#                 if credit_date_range['first_credit_date'] and debit_date_range['first_debit_date']:
#                     ledger_first_date = min(
#                         credit_date_range['first_credit_date'],
#                         debit_date_range['first_debit_date']
#                     )
#                 elif credit_date_range['first_credit_date']:
#                     ledger_first_date = credit_date_range['first_credit_date']
#                 elif debit_date_range['first_debit_date']:
#                     ledger_first_date = debit_date_range['first_debit_date']

#                 # Update the overall minimum date
#                 if ledger_first_date and (first_date is None or ledger_first_date < first_date):
#                     first_date = ledger_first_date

#                 # Determine the maximum date for this ledger (comparing debit and credit)
#                 ledger_last_date = None

#                 if credit_date_range['last_credit_date'] and debit_date_range['last_debit_date']:
#                     ledger_last_date = max(
#                         credit_date_range['last_credit_date'],
#                         debit_date_range['last_debit_date']
#                     )
#                 elif credit_date_range['last_credit_date']:
#                     ledger_last_date = credit_date_range['last_credit_date']
#                 elif debit_date_range['last_debit_date']:
#                     ledger_last_date = debit_date_range['last_debit_date']

#                 # Update the overall maximum date
#                 if ledger_last_date and (last_date is None or ledger_last_date > last_date):
#                     last_date = ledger_last_date

#             # Rest of your code for calculating totals and appending to ledger_details
#             if from_date and to_date:
#                 debit_entries = TblDrJournalEntry.objects.filter(ledger=ledger)
#                 credit_entries = TblCrJournalEntry.objects.filter(ledger=ledger)
#                 from_date = request.GET.get('fromDate')
#                 to_date_str = request.GET.get('toDate')        
#                 to_date = datetime.strptime(to_date_str, '%Y-%m-%d')
#                 to_date += timedelta(days=1)
#                 debit_entries = debit_entries.filter(created_at__range=[from_date, to_date])
#                 credit_entries = credit_entries.filter(created_at__range=[from_date, to_date])
#                 to_date -= timedelta(days=1)

#                 to_date = to_date.strftime('%Y-%m-%d')


#             total_credit=0
#             total_debit=0
#                 # Calculate debit total for the selected date
#             for credit in credit_entries:
#                 total_credit += credit.credit_amount

#                 # Calculate credit total for the selected date
#             for debit in debit_entries:
#                 total_debit += debit.debit_amount

#             if total_debit != 0 or total_credit != 0:
#                 ledger_details.append({
#                     'ledger_name': ledger.ledger_name,
#                     'debit_total': total_debit,
#                     'credit_total': total_credit,
#                 })
                    
#                     #Update the overall totals
#             total_d += total_debit
#             total_c += total_credit

#         balance = total_d - total_c
#         if balance <= 0:
#             c = 0  # tells that it is negative
#         else:
#             c = 1  # tells that it is positive

#         new_balance = abs(balance)

#         # Render a template with the retrieved ledger details and filter parameters
#         return render(request, self.template_name, {
#             'ledger_details': ledger_details,
#             'from_date': from_date,
#             'to_date': to_date,
#             'option': option,
#             'total_d': total_d,
#             'total_c': total_c,
#             'openclose': option == 'openclose',
#             'balance': new_balance,
#             'c': c,
#             'current_fiscal_year': current_fiscal_year,
#             'first_date': first_date,
#             'last_date': last_date
#         })


def soft_delete_journal(request, journal_id):
    try:
        # Retrieve the journal entry or return a 404 if it doesn't exist
        journal_entry = get_object_or_404(TblJournalEntry, id=journal_id)

        # Get related credit and debit entries
        credit_entries = TblCrJournalEntry.objects.filter(journal_entry=journal_entry)
        debit_entries = TblDrJournalEntry.objects.filter(journal_entry=journal_entry)

        # Reverse the ledger operations for credit entries
        for credit_entry in credit_entries:
            ledger = credit_entry.ledger
            ledger_type = ledger.account_chart.account_type

            # Reverse the operation based on ledger type
            if ledger_type in ['Asset', 'Expense']:
                ledger.total_value += credit_entry.credit_amount
            elif ledger_type in ['Liability', 'Revenue', 'Equity']:
                ledger.total_value -= credit_entry.credit_amount

            ledger.save()

        # Reverse the ledger operations for debit entries
        for debit_entry in debit_entries:
            ledger = debit_entry.ledger
            ledger_type = ledger.account_chart.account_type

            # Reverse the operation based on ledger type
            if ledger_type in ['Asset', 'Expense']:
                ledger.total_value -= debit_entry.debit_amount
            elif ledger_type in ['Liability', 'Revenue', 'Equity']:
                ledger.total_value += debit_entry.debit_amount

            ledger.save()

        # Soft delete the journal entry
 
        journal_entry.delete()

        # Soft delete related credit entries
        # credit_entries.delete()

        # # Soft delete related debit entries
        # debit_entries.delete()



    except TblJournalEntry.DoesNotExist:
        # Handle the case where the journal entry doesn't exist.
        messages.error(request, "Journal Entry not found.")
    except Exception as e:
        # Handle any other exceptions or errors as needed
        messages.error(request, f"An error occurred: {str(e)}")

    return redirect('journal_list')




# class JournalEntryUpdateView(IsAdminMixin, View):
#     # Define your GET method to display the form for updating a journal entry
#     def get(self, request, pk):
#         journal_entry = get_object_or_404(TblJournalEntry, pk=pk)
#         ledgers = AccountLedger.objects.all()
#         sub_ledgers = AccountSubLedger.objects.all()

#         # Create an instance of the JournalEntryForm and populate it with values from the journal_entry
#         form = JournalEntryForm(initial={
#             'debit_ledger': journal_entry.debit_ledger,
#             'debit_particulars': journal_entry.debit_particulars,
#             'debit_amount': journal_entry.debit_amount,
#             'credit_ledger': journal_entry.credit_ledger,
#             'credit_particulars': journal_entry.credit_particulars,
#             'credit_amount': journal_entry.credit_amount,
#         })

#         return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers, 'form': form, 'journal_entry': journal_entry})
    
#     # Define your POST method to handle the form submission for updating a journal entry
#     def post(self, request, pk):
#         journal_entry = get_object_or_404(TblJournalEntry, pk=pk)
#         data = request.POST
#         ledgers = AccountLedger.objects.all()
#         sub_ledgers = AccountSubLedger.objects.all()

#         # Create an instance of the JournalEntryForm and populate it with values from the journal_entry
#         form = JournalEntryForm(data)

#         if form.is_valid():
#             # Update the journal entry with the values from the form
#             journal_entry.debit_ledger = form.cleaned_data['debit_ledger']
#             journal_entry.debit_particulars = form.cleaned_data['debit_particulars']
#             journal_entry.debit_amount = form.cleaned_data['debit_amount']
#             journal_entry.credit_ledger = form.cleaned_data['credit_ledger']
#             journal_entry.credit_particulars = form.cleaned_data['credit_particulars']
#             journal_entry.credit_amount = form.cleaned_data['credit_amount']

#             journal_entry.save()
#             messages.success(request, 'Journal entry updated successfully.')
#             return redirect('journal_list')  # Replace with the appropriate URL name

#         messages.error(request, 'Error updating journal entry. Please check the form.')
#         return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers, 'form': form, 'journal_entry': journal_entry})

# class JournalEntryUpdateView(IsAdminMixin, View):
#     # Define your GET method to display the form for updating a journal entry
#     def get(self, request, pk):
#         journal_entry = get_object_or_404(TblJournalEntry, pk=pk)
#         ledgers = AccountLedger.objects.all()
#         sub_ledgers = AccountSubLedger.objects.all()

#         # Get the related debit and credit entries
#         debit_entries = TblDrJournalEntry.objects.filter(journal_entry=journal_entry)
#         credit_entries = TblCrJournalEntry.objects.filter(journal_entry=journal_entry)

#         # You can customize how you want to populate the form based on your model structure
#         # In this example, we'll concatenate all debit and credit entries' data
#         debit_data = "\n".join([f"{entry.ledger.ledger_name} - {entry.debit_amount}" for entry in debit_entries])
#         credit_data = "\n".join([f"{entry.ledger.ledger_name} - {entry.credit_amount}" for entry in credit_entries])
#         # for entry in debit_entries:
#         #     debit_ledger_name  = entry.ledger.ledger_name
#         #     debit_amount = entry.debit_amount
#         # for entry in credit_entries:
#         #     credit_ledger_name  = entry.ledger.ledger_name
#         #     debit_amount = entry.debit_amount
#         print(f'debit data {debit_data}')
#         print(credit_data)

#         # Create an instance of the JournalEntryForm and populate it with values
#         form = JournalEntryForm(initial={
#             'debit': debit_data,
#             'credit': credit_data,
#             'journal_total': journal_entry.journal_total,
#             'fiscal_year': journal_entry.fiscal_year,
#         })

#         return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers, 'form': form, 'journal_entry': journal_entry})
    
#     # Define your POST method to handle the form submission for updating a journal entry
#     def post(self, request, pk):
#         journal_entry = get_object_or_404(TblJournalEntry, pk=pk)
#         data = request.POST
#         ledgers = AccountLedger.objects.all()
#         sub_ledgers = AccountSubLedger.objects.all()

#         # Create an instance of the JournalEntryForm and populate it with values
#         form = JournalEntryForm(data)

#         if form.is_valid():
#             # Update the journal entry with the values from the form
#             # You'll need to parse the debit and credit entries from the form data and update the related models accordingly
#             # This part depends on how your form is structured and how you want to update the related entries
#             # Example: Split the debit_data and credit_data, create/update related entries, etc.
#             # Update employee_name, journal_total, fiscal_year accordingly
#             # journal_entry.employee_name = form.cleaned_data['employee_name']
#             # journal_entry.journal_total = form.cleaned_data['journal_total']
#             # journal_entry.fiscal_year = form.cleaned_data['fiscal_year']
#             # journal_entry.save()

#             messages.success(request, 'Journal entry updated successfully.')
#             return redirect('journal_list')  # Replace with the appropriate URL name

#         messages.error(request, 'Error updating journal entry. Please check the form.')
#         return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers, 'form': form, 'journal_entry': journal_entry})

class JournalEntryUpdateView(IsAdminMixin, View):
    # Define your GET method to display the form for updating a journal entry
    def get(self, request, pk):
        journal_entry = get_object_or_404(TblJournalEntry, pk=pk)
        ledgers = AccountLedger.objects.all()
        sub_ledgers = AccountSubLedger.objects.all()

        # Get the related debit and credit entries
        debit_entries = TblDrJournalEntry.objects.filter(journal_entry=journal_entry)
        credit_entries = TblCrJournalEntry.objects.filter(journal_entry=journal_entry)

        # Create a list to store debit and credit entry data
        debit_data = []
        credit_data = []

        # Populate debit_data
        for entry in debit_entries:
            debit_data.append({
                'ledger_name': entry.ledger.ledger_name,
                'debit_amount': entry.debit_amount,
            })

        # Populate credit_data
        for entry in credit_entries:
            credit_data.append({
                'ledger_name': entry.ledger.ledger_name,
                'credit_amount': entry.credit_amount,
            })

        # Create an instance of the JournalEntryForm and populate it with values
        form = JournalEntryForm(initial={
            'debit_entries': debit_data,
            'credit_entries': credit_data,
            'journal_total': journal_entry.journal_total,
            'fiscal_year': journal_entry.fiscal_year,
        })

        return render(request, 'accounting/journal/journal_entry_update.html', {
            'ledgers': ledgers,
            'sub_ledgers': sub_ledgers,
            'form': form,
            'journal_entry': journal_entry,
        })
    
    def get_subledger(self, subledger, ledger):
        subled = None
        if not subledger.startswith('-'):
            try:
                subledger_id = int(subledger)
                subled = AccountSubLedger.objects.get(pk=subledger_id)
            except ValueError:
                subled = AccountSubLedger.objects.create(sub_ledger_name=subledger, is_editable=True, ledger=ledger)
        return subled
        

    # def post(self, request, pk):
    #     data = request.POST
    #     debit_ledgers = data.getlist('debit_ledger', [])
    #     debit_particulars = data.getlist('debit_particular', [])
    #     debit_amounts = data.getlist('debit_amount', [])
    #     debit_subledgers = data.getlist('debit_subledger', [])

    #     credit_ledgers = data.getlist('credit_ledger', [])
    #     credit_particulars = data.getlist('credit_particular', [])
    #     credit_amounts = data.getlist('credit_amount', [])
    #     credit_subledgers = data.getlist('credit_subledger', [])

    #     ledgers = AccountLedger.objects.all()
    #     sub_ledgers = AccountSubLedger.objects.all()

    #     try:
    #         parsed_debitamt = [D(i) for i in debit_amounts]
    #         parsed_creditamt = [D(i) for i in credit_amounts]
    #     except Exception:
    #         messages.error(request, "Please Enter a valid amount")
    #         return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

    #     debit_sum, credit_sum = sum(parsed_debitamt), sum(parsed_creditamt)
    #     if debit_sum != credit_sum:
    #         messages.error(request, "Debit Total and Credit Total must be equal")
    #         return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

    #     for dr in debit_ledgers:
    #         if dr.startswith('-'):
    #             messages.error(request, "Ledger must be selected")
    #             return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

    #     credit_to_debit_mapping = {}

    #     # Retrieve the journal_entry object or raise a 404 error if not found
    #     try:
    #         journal_entry = TblJournalEntry.objects.get(pk=pk)
    #     except TblJournalEntry.DoesNotExist:
    #         raise Http404("Journal Entry does not exist")

    #     # Update journal entry data
    #     journal_entry.employee_name = request.user.username
    #     journal_entry.journal_total = debit_sum
    #     journal_entry.save()

    #     # Update credit entries
    #     for i in range(len(credit_ledgers)):
    #         credit_ledger_id = int(credit_ledgers[i])
    #         credit_ledger = AccountLedger.objects.get(pk=credit_ledger_id)
    #         credit_to_debit_mapping[credit_ledger] = credit_ledger
    #         credit_particular = credit_particulars[i]
    #         credit_amount = parsed_creditamt[i]
    #         subledger = self.get_subledger(credit_subledgers[i], credit_ledger)  # Implement your subledger utility function
    #         credit_ledger_type = credit_ledger.account_chart.account_type
    #         TblCrJournalEntry.objects.create(
    #             ledger=credit_ledger,
    #             journal_entry=journal_entry,
    #             particulars=credit_particular,
    #             credit_amount=credit_amount,
    #             sub_ledger=subledger,
    #             paidfrom_ledger=credit_ledger
    #         )
    #         if credit_ledger_type in ['Asset', 'Expense']:
    #             credit_ledger.total_value -= credit_amount
    #             credit_ledger.save()
    #             if subledger:
    #                 subledger.total_value -= credit_amount
    #                 subledger.save()
    #         elif credit_ledger_type in ['Liability', 'Revenue', 'Equity']:
    #             credit_ledger.total_value += credit_amount
    #             credit_ledger.save()
    #             if subledger:
    #                 subledger.total_value += credit_amount
    #                 subledger.save()

    #     # Update debit entries
    #     for i in range(len(debit_ledgers)):
    #         debit_ledger_id = int(debit_ledgers[i])
    #         debit_ledger = AccountLedger.objects.get(pk=debit_ledger_id)
    #         debit_particular = debit_particulars[i]
    #         debit_amount = parsed_debitamt[i]
    #         subledger = self.get_subledger(debit_subledgers[i], debit_ledger)  # Implement your subledger utility function
    #         debit_ledger_type = debit_ledger.account_chart.account_type
    #         TblDrJournalEntry.objects.create(
    #             ledger=debit_ledger,
    #             journal_entry=journal_entry,
    #             particulars=debit_particular,
    #             debit_amount=debit_amount,
    #             sub_ledger=subledger,
    #             paidfrom_ledger=credit_to_debit_mapping.get(credit_ledger)
    #         )
    #         if debit_ledger_type in ['Asset', 'Expense']:
    #             debit_ledger.total_value += debit_amount
    #             debit_ledger.save()
    #             if subledger:
    #                 subledger.total_value += debit_amount
    #                 subledger.save()
    #         elif debit_ledger_type in ['Liability', 'Revenue', 'Equity']:
    #             debit_ledger.total_value -= debit_amount
    #             debit_ledger.save()
    #             if subledger:
    #                 subledger.total_value -= debit_amount
    #                 subledger.save()

    #     return redirect('journal_list')         

    def post(self, request, pk):
        data = request.POST
        debit_ledgers = data.getlist('debit_ledger', [])
        debit_particulars = data.getlist('debit_particular', [])
        debit_amounts = data.getlist('debit_amount', [])
        debit_subledgers = data.getlist('debit_subledger', [])

        credit_ledgers = data.getlist('credit_ledger', [])
        credit_particulars = data.getlist('credit_particular', [])
        credit_amounts = data.getlist('credit_amount', [])
        credit_subledgers = data.getlist('credit_subledger', [])

        ledgers = AccountLedger.objects.all()
        sub_ledgers = AccountSubLedger.objects.all()

        try:
            parsed_debitamt = [D(i) for i in debit_amounts]
            parsed_creditamt = [D(i) for i in credit_amounts]
        except Exception:
            messages.error(request, "Please Enter a valid amount")
            return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

        debit_sum, credit_sum = sum(parsed_debitamt), sum(parsed_creditamt)
        if debit_sum != credit_sum:
            messages.error(request, "Debit Total and Credit Total must be equal")
            return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

        for dr in debit_ledgers:
            if dr.startswith('-'):
                messages.error(request, "Ledger must be selected")
                return render(request, 'accounting/journal/journal_entry_update.html', {'ledgers': ledgers, 'sub_ledgers': sub_ledgers})

        # Retrieve the journal_entry object or raise a 404 error if not found
        try:
            journal_entry = TblJournalEntry.objects.get(pk=pk)
        except TblJournalEntry.DoesNotExist:
            raise Http404("Journal Entry does not exist")

        # Update journal entry data
        journal_entry.employee_name = request.user.username
        journal_entry.journal_total = debit_sum
        journal_entry.save()

        # Update or create credit entries
        existing_credit_entries = TblCrJournalEntry.objects.filter(journal_entry=journal_entry)
        credit_to_debit_mapping = {}
        for i in range(len(credit_ledgers)):
            credit_ledger_id = int(credit_ledgers[i])
            credit_ledger = AccountLedger.objects.get(pk=credit_ledger_id)
            credit_particular = credit_particulars[i]
            credit_amount = parsed_creditamt[i]
            subledger = self.get_subledger(credit_subledgers[i], credit_ledger)  # Implement your subledger utility function
            credit_ledger_type = credit_ledger.account_chart.account_type
            
            # Check if there is an existing entry for this ledger, if so, update it, otherwise, create a new one
            existing_entry = existing_credit_entries.filter(ledger=credit_ledger).first()
            if existing_entry:  
                existing_entry.particulars = credit_particular
                existing_entry.credit_amount = credit_amount
                existing_entry.sub_ledger = subledger
                existing_entry.paidfrom_ledger = credit_ledger
                existing_entry.save()
            else:
                TblCrJournalEntry.objects.create(
                    ledger=credit_ledger,
                    journal_entry=journal_entry,
                    particulars=credit_particular,
                    credit_amount=credit_amount,
                    sub_ledger=subledger,
                    paidfrom_ledger=credit_ledger
                )

            if credit_ledger_type in ['Asset', 'Expense']:
                credit_ledger.total_value -= credit_amount
                credit_ledger.save()
                if subledger:
                    subledger.total_value -= credit_amount
                    subledger.save()
            elif credit_ledger_type in ['Liability', 'Revenue', 'Equity']:
                credit_ledger.total_value += credit_amount
                credit_ledger.save()
                if subledger:
                    subledger.total_value += credit_amount
                    subledger.save()

        # Update or create debit entries
        existing_debit_entries = TblDrJournalEntry.objects.filter(journal_entry=journal_entry)
        for i in range(len(debit_ledgers)):
            debit_ledger_id = int(debit_ledgers[i])
            debit_ledger = AccountLedger.objects.get(pk=debit_ledger_id)
            debit_particular = debit_particulars[i]
            debit_amount = parsed_debitamt[i]
            subledger = self.get_subledger(debit_subledgers[i], debit_ledger)  # Implement your subledger utility function
            debit_ledger_type = debit_ledger.account_chart.account_type
            
            # Check if there is an existing entry for this ledger, if so, update it, otherwise, create a new one
            existing_entry = existing_debit_entries.filter(ledger=debit_ledger).first()
            if existing_entry:
                existing_entry.particulars = debit_particular
                existing_entry.debit_amount = debit_amount
                existing_entry.sub_ledger = subledger
                existing_entry.paidfrom_ledger = credit_to_debit_mapping.get(credit_ledger)
                existing_entry.save()
            else:
                TblDrJournalEntry.objects.create(
                    ledger=debit_ledger,
                    journal_entry=journal_entry,
                    particulars=debit_particular,
                    debit_amount=debit_amount,
                    sub_ledger=subledger,
                    paidfrom_ledger=credit_to_debit_mapping.get(credit_ledger)
                )

            if debit_ledger_type in ['Asset', 'Expense']:
                debit_ledger.total_value += debit_amount
                debit_ledger.save()
                if subledger:
                    subledger.total_value += debit_amount
                    subledger.save()
            elif debit_ledger_type in ['Liability', 'Revenue', 'Equity']:
                debit_ledger.total_value -= debit_amount
                debit_ledger.save()
                if subledger:
                    subledger.total_value -= debit_amount
                    subledger.save()

        # Delete any existing entries that are no longer present in the form
        existing_credit_entries.exclude(ledger__id__in=credit_ledgers).delete()
        existing_debit_entries.exclude(ledger__id__in=debit_ledgers).delete()

        return redirect('journal_list')


