from .user import urlpatterns as user_urlpatterns
from .product import urlpatterns as product_urlpatterns
from .bill import urlpatterns as bill_urlpatterns
from .organization import urlpatterns as org_urlpatterns
from .discount_urls import urlpatterns as discount_urlspatterns
from .purchaserequisition_api import urlpatterns as purchaserequisition_urlpattern
from .accounting_urls import urlpatterns as accounting_urlpatterns
from .mobilepayment_type import urlpatterns as mobile_urlpatterns

urlpatterns = (
    [] + user_urlpatterns + product_urlpatterns + bill_urlpatterns + org_urlpatterns+discount_urlspatterns+purchaserequisition_urlpattern+accounting_urlpatterns+mobile_urlpatterns
)
