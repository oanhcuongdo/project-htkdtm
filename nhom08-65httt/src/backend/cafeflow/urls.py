from django.urls import include, path
from wagtail.admin import urls as wagtailadmin_urls

from cafeflow.views import overview
from market.views import ExchangeRateList, PriceList, exchange_rate_page, price_page

urlpatterns = [
    path("", overview, name="overview"),
    path("market/", price_page, name="price-page"),
    path("market/exchange-rates/", exchange_rate_page, name="exchange-rate-page"),
    path("api/v1/prices/", PriceList.as_view(), name="price-list"),
    path("api/v1/exchange-rates/", ExchangeRateList.as_view(), name="exchange-rate-list"),
    path("cms/", include(wagtailadmin_urls)),
]
