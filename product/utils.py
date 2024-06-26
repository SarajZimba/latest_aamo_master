from accounting.models import AccountLedger, AccountSubLedger
from purchase.models import AccountProductTracking

def create_subledgers_after_product_create(product):
    ledger = AccountLedger.objects.get(ledger_name="Inventory Purchases")
    subledgername = f'{product.title} ({product.category.title})'
    total = product.cost_price * product.opening_count
    try:
        sub = AccountSubLedger.objects.get(sub_ledger_name=subledgername, ledger=ledger)
        sub.total_value += total
        sub.save()
    except AccountSubLedger.DoesNotExist:
        AccountSubLedger.objects.create(sub_ledger_name=subledgername, ledger=ledger, total_value=total)
    AccountProductTracking.objects.create(product=product, purchase_rate=product.cost_price, quantity=product.opening_count, remaining_stock=product.opening_count)
