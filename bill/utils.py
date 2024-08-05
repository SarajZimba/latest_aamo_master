from accounting.models import AccountChart, AccountLedger, TblCrJournalEntry, TblJournalEntry, TblDrJournalEntry
from accounting.models import AccountSubLedger, AccountLedger, AccountChart
from purchase.models import AccountProductTracking
from decimal import Decimal
from product.models import Product


def create_journal_for_complimentary(instance):
    grand_total = Decimal(instance.sub_total)
    complimentary_sales = AccountLedger.objects.get(ledger_name__iexact='complimentary sales')
    complimentary_expenses = AccountLedger.objects.get(ledger_name__iexact='complimentary expenses')

    journal_entry = TblJournalEntry.objects.create(employee_name='Created automatically during sale', journal_total=grand_total)
    TblDrJournalEntry.objects.create(particulars="Complimentary Expenses A/C Dr.", debit_amount = grand_total, journal_entry=journal_entry, ledger=complimentary_expenses)
    TblCrJournalEntry.objects.create(particulars="To Complimentary Sales", credit_amount = grand_total, journal_entry=journal_entry, ledger=complimentary_sales)
    
    complimentary_expenses.total_value += grand_total
    complimentary_expenses.save()

    complimentary_sales.total_value += grand_total
    complimentary_sales.save()


def create_journal_for_bill(instance):
    print(instance.amount_in_words)
    payment_mode = instance.payment_mode.lower().strip()
    print(payment_mode)
    
    grand_total = Decimal(instance.grand_total)
    tax_amount = Decimal(instance.tax_amount)
    discount_amount = Decimal(instance.discount_amount)
    invoice_number = instance.invoice_number
  
    sale_ledger = AccountLedger.objects.get(ledger_name='Sales')
    journal_entry = TblJournalEntry.objects.create(employee_name='Created Automatically during Sale', journal_total=(grand_total-discount_amount))


    if discount_amount > 0:
        discount_expenses = AccountLedger.objects.get(ledger_name__iexact='Discount Expenses')
        discount_sales = AccountLedger.objects.get(ledger_name__iexact='Discount Sales')

        TblDrJournalEntry.objects.create(particulars="Discount Expenses A/C Dr.", debit_amount = discount_amount, journal_entry=journal_entry, ledger=discount_expenses)
        TblCrJournalEntry.objects.create(particulars="To Discount Sales", credit_amount = discount_amount, journal_entry=journal_entry, ledger=discount_sales)
        
        discount_expenses.total_value += discount_amount
        discount_expenses.save()

        discount_sales.total_value += discount_amount
        discount_sales.save()


    if tax_amount > 0:
        vat_payable = AccountLedger.objects.get(ledger_name='VAT Payable')
        vat_payable.total_value = vat_payable.total_value + tax_amount
        vat_payable.save()
        TblCrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"To VAT Payable", ledger=vat_payable, credit_amount=tax_amount)

    if payment_mode == 'credit':
        account_chart = AccountChart.objects.get(group='Sundry Debtors')
        try:
            dr_ledger = AccountLedger.objects.get(ledger_name=f'{instance.customer.pk} - {instance.customer.name}')
            dr_ledger.total_value += grand_total
            dr_ledger.save()
        except AccountLedger.DoesNotExist:
            dr_ledger = AccountLedger.objects.create(ledger_name=f'{instance.customer.pk} - {instance.customer.name}', account_chart=account_chart, total_value=grand_total)

        TblDrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"{instance.customer.name} A/C Dr", ledger=dr_ledger, debit_amount=grand_total)
        TblCrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"To Sales", ledger=sale_ledger, credit_amount=(grand_total-tax_amount))
        
        
    elif payment_mode == "credit card":
        card_transaction_ledger = AccountLedger.objects.get(ledger_name='Card Transactions')
        TblDrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"Card Transaction A/C Dr", ledger=card_transaction_ledger, debit_amount=grand_total)
        TblCrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"To Sales", ledger=sale_ledger, credit_amount=(grand_total-tax_amount))
        card_transaction_ledger.total_value += grand_total
        card_transaction_ledger.save()


    elif payment_mode == "mobile payment":
        mobile_payment = AccountLedger.objects.get(ledger_name='Mobile Payments')

        TblDrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"Mobile Payment A/C Dr", ledger=mobile_payment, debit_amount=grand_total)
        TblCrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"To Sales", ledger=sale_ledger, credit_amount=(grand_total-tax_amount))
        mobile_payment.total_value += grand_total
        mobile_payment.save()


    elif payment_mode == "cash":
        cash_ledger = AccountLedger.objects.get(ledger_name='Cash-In-Hand')
        cash_ledger.total_value = cash_ledger.total_value + grand_total
        cash_ledger.save()

        TblDrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"Sales from invoice number {invoice_number} Cash A/C Dr", ledger=cash_ledger, debit_amount=grand_total)
        TblCrJournalEntry.objects.create(journal_entry=journal_entry, particulars=f"To Sales", ledger=sale_ledger, credit_amount=(grand_total-tax_amount))

    sale_ledger.total_value += (grand_total-tax_amount)
    sale_ledger.save()


def update_subledger_after_updating_product(product_id, initial_name, updated_name):
    product = Product.objects.get(pk=product_id)
    subledgername = f'{initial_name} ({product.category.title})'
    AccountSubLedger.objects.filter(sub_ledger_name=subledgername).update(sub_ledger_name=f"{updated_name} ({product.category.title})")
    

def product_sold(instance):
    product = instance.product
    subledgername = f'{product.title} ({product.category.title})'
    quantity_sold = int(instance.product_quantity)
    inventory_expenses_ledger, created = AccountLedger.objects.get_or_create(ledger_name='Inventory Expenses')
    
    sub, created = AccountSubLedger.objects.get_or_create(sub_ledger_name=subledgername, ledger__account_chart__account_type='Asset')


    expenses_subledger, _ = AccountSubLedger.objects.get_or_create(sub_ledger_name=subledgername, ledger=inventory_expenses_ledger)
    all_products = AccountProductTracking.objects.filter(product=instance.product, remaining_stock__gt=0).order_by('created_at')

    total_amount = 0
    for product in all_products:
        if product.remaining_stock >= quantity_sold:
            
            if total_amount <=0:
                product.remaining_stock -= quantity_sold
                product.save()
                sub.total_value -= (product.purchase_rate * quantity_sold)

                sub.ledger.total_value -= (product.purchase_rate * quantity_sold)
                sub.ledger.save()

                expenses_subledger.total_value += (product.purchase_rate * quantity_sold)
                expenses_subledger.save()

                inventory_expenses_ledger.total_value += (product.purchase_rate * quantity_sold)
                inventory_expenses_ledger.save()
                break
            else:
                total_amount += (product.purchase_rate * quantity_sold)
                product.remaining_stock -= quantity_sold
                product.save()
                sub.total_value -= total_amount

                sub.ledger.total_value -= total_amount
                sub.ledger.save()

                expenses_subledger.total_value += total_amount
                expenses_subledger.save()

                inventory_expenses_ledger.total_value += total_amount
                inventory_expenses_ledger.save()
        else:
            total_amount += product.purchase_rate * product.remaining_stock
            quantity_sold -= product.remaining_stock
            product.remaining_stock=0
            product.save()

    sub.save()
    
    sale_ledger = AccountLedger.objects.get(ledger_name='Sales')
    try:
        print("I was in try")        
        sale_subledger = AccountSubLedger.objects.get(sub_ledger_name=subledgername, ledger=sale_ledger)
        sale_subledger.total_value += Decimal(instance.amount)
        sale_subledger.save()
    except AccountSubLedger.DoesNotExist:
        print("I was in the exception")
        AccountSubLedger.objects.create(sub_ledger_name=subledgername, ledger=sale_ledger, total_value=Decimal(instance.amount))





    

