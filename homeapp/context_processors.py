from django.db.models import Sum

from backend.models import categorydb
from homeapp.models import Cartdb


def store(request):
    """Data shared by every storefront page: category menu, cart badge, current user."""
    username = request.session.get('username')
    cart_count = 0
    if username:
        cart_count = Cartdb.objects.filter(Username=username).aggregate(n=Sum('Quantity'))['n'] or 0
    return {
        'nav_categories': categorydb.objects.all(),
        'cart_count': cart_count,
        'current_user': username,
    }
