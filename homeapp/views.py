from django.contrib import messages
from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from backend.models import categorydb, productdb
from homeapp.models import regdb, Cartdb, Checkout, OrderItem

FREE_DELIVERY_ABOVE = 500
DELIVERY_FEE = 40


# ---------- helpers ----------
def _cart_items(username):
    return Cartdb.objects.filter(Username=username).select_related('Product')


def _cart_summary(items):
    subtotal = sum(i.Total or 0 for i in items)
    delivery = 0 if subtotal == 0 or subtotal >= FREE_DELIVERY_ABOVE else DELIVERY_FEE
    return {
        'subtotal': subtotal,
        'delivery': delivery,
        'grand_total': subtotal + delivery,
        'free_delivery_above': FREE_DELIVERY_ABOVE,
        'to_free_delivery': max(FREE_DELIVERY_ABOVE - subtotal, 0),
    }


def _safe_next(request, fallback='homepage'):
    nxt = request.POST.get('next') or request.GET.get('next')
    if nxt and url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        return nxt
    return fallback


def _require_login(request):
    if 'username' not in request.session:
        messages.info(request, "Please sign in to continue.")
        return redirect(f"{reverse('loginpg')}?next={request.path}")
    return None


def _parse_qty(value, default=1):
    try:
        return max(1, min(int(value), 99))
    except (TypeError, ValueError):
        return default


def _password_matches(raw, stored):
    if not stored:
        return False
    try:
        identify_hasher(stored)
    except ValueError:
        return raw == stored  # legacy plain-text password
    return check_password(raw, stored)


# ---------- pages ----------
def homepage(req):
    featured = productdb.objects.order_by('-id')[:8]
    return render(req, "home.html", {'featured': featured})


def aboutus(req):
    return render(req, "aboutus.html", {
        'product_count': productdb.objects.count(),
        'category_count': categorydb.objects.count(),
    })


def contactus(req):
    if req.method == "POST":
        if req.POST.get('name') and req.POST.get('email') and req.POST.get('message'):
            messages.success(req, "Thanks for reaching out! We'll get back to you within 24 hours.")
        else:
            messages.error(req, "Please fill in your name, email and message.")
        return redirect('contactus')
    return render(req, "contactus.html")


def shop(req, catname=None):
    products = productdb.objects.all()
    q = req.GET.get('q', '').strip()
    category = catname or req.GET.get('category', '')
    sort = req.GET.get('sort', 'new')

    if q:
        products = products.filter(Q(ProductName__icontains=q) | Q(Description__icontains=q) | Q(Category__icontains=q))
    if category:
        products = products.filter(Category__iexact=category)

    products = products.order_by({
        'price_asc': 'Price',
        'price_desc': '-Price',
        'name': 'ProductName',
    }.get(sort, '-id'))

    page = Paginator(products, 12).get_page(req.GET.get('page'))
    return render(req, "shop.html", {
        'page': page,
        'products': page.object_list,
        'total': products.count(),
        'q': q,
        'active_category': category,
        'sort': sort,
    })


def pro(req, catname):
    return shop(req, catname=catname)


def singleproduct(req, proid):
    product = get_object_or_404(productdb, id=proid)
    related = productdb.objects.filter(Category=product.Category).exclude(id=product.id)[:4]
    return render(req, "singleproduct.html", {'product': product, 'related': related})


# ---------- accounts ----------
def register(req):
    if 'username' in req.session:
        return redirect('homepage')
    return render(req, "register.html")


def loginpg(req):
    if 'username' in req.session:
        return redirect('homepage')
    return render(req, "login.html", {'next': req.GET.get('next', '')})


def registersave(req):
    if req.method != "POST":
        return redirect('register')
    un = (req.POST.get('username') or '').strip()
    en = (req.POST.get('email') or '').strip()
    ps = req.POST.get('password') or ''
    cps = req.POST.get('confirm_password')
    img = req.FILES.get('image')

    if not un or not en or not ps:
        messages.error(req, "All fields are required.")
    elif len(ps) < 6:
        messages.error(req, "Password must be at least 6 characters.")
    elif cps is not None and ps != cps:
        messages.error(req, "Passwords do not match.")
    elif regdb.objects.filter(Username__iexact=un).exists():
        messages.error(req, "That username is already taken.")
    elif regdb.objects.filter(Email__iexact=en).exists():
        messages.error(req, "An account with that email already exists.")
    else:
        regdb.objects.create(Username=un, Email=en, Password=make_password(ps), Image=img)
        messages.success(req, "Account created! Please sign in.")
        return redirect('loginpg')
    return redirect('register')


def userlogin(request):
    if request.method != "POST":
        return redirect('loginpg')
    user = (request.POST.get('username') or '').strip()
    pwd = request.POST.get('pass') or request.POST.get('password') or ''
    account = regdb.objects.filter(Username=user).first()
    if account and _password_matches(pwd, account.Password):
        if not account.Password.startswith(('pbkdf2_', 'argon2', 'bcrypt', 'scrypt')):
            account.Password = make_password(pwd)
            account.save(update_fields=['Password'])
        request.session.cycle_key()
        request.session['username'] = account.Username
        messages.success(request, f"Welcome back, {account.Username}!")
        return redirect(_safe_next(request))
    messages.error(request, "Invalid username or password.")
    return redirect('loginpg')


def logout(request):
    request.session.pop('username', None)
    request.session.pop('password', None)
    messages.info(request, "You have been signed out.")
    return redirect('homepage')


# ---------- cart ----------
def cartsave(req):
    if req.method != "POST":
        return redirect('cartdisplay')
    blocked = _require_login(req)
    if blocked:
        return blocked

    username = req.session['username']
    product = get_object_or_404(productdb, id=req.POST.get('productid'))
    qty = _parse_qty(req.POST.get('qty'))
    price = product.Price or 0

    item = Cartdb.objects.filter(Username=username, Product=product).first()
    if item:
        item.Quantity = min((item.Quantity or 0) + qty, 99)
    else:
        item = Cartdb(Username=username, Product=product, ProductName=product.ProductName, Quantity=qty)
    item.Total = item.Quantity * price
    item.save()

    messages.success(req, f"{product.ProductName.title()} added to your cart.")
    if req.POST.get('buy_now'):
        return redirect('checkout')
    return redirect(_safe_next(req, fallback='cartdisplay'))


def cartupdate(req, dataid):
    if req.method == "POST" and 'username' in req.session:
        item = get_object_or_404(Cartdb, id=dataid, Username=req.session['username'])
        item.Quantity = _parse_qty(req.POST.get('qty'), default=item.Quantity or 1)
        item.Total = item.Quantity * item.unit_price
        item.save()
    return redirect('cartdisplay')


def cartdisplay(request):
    blocked = _require_login(request)
    if blocked:
        return blocked
    items = _cart_items(request.session['username'])
    return render(request, "cartdisplay.html", {'items': items, **_cart_summary(items)})


def cartdel(req, dataid):
    if 'username' in req.session:
        Cartdb.objects.filter(id=dataid, Username=req.session['username']).delete()
        messages.info(req, "Item removed from your cart.")
    return redirect('cartdisplay')


# ---------- checkout & orders ----------
def checkout(request):
    blocked = _require_login(request)
    if blocked:
        return blocked
    items = _cart_items(request.session['username'])
    if not items:
        messages.info(request, "Your cart is empty.")
        return redirect('shop')
    account = regdb.objects.filter(Username=request.session['username']).first()
    last_order = Checkout.objects.filter(Username=request.session['username']).first()
    return render(request, "checkout.html", {
        'items': items,
        'account': account,
        'last_order': last_order,
        **_cart_summary(items),
    })


def checksave(request):
    if request.method != "POST":
        return redirect('checkout')
    blocked = _require_login(request)
    if blocked:
        return blocked

    username = request.session['username']
    items = list(_cart_items(username))
    if not items:
        return redirect('shop')

    name = (request.POST.get('name') or '').strip()
    email = (request.POST.get('email') or '').strip()
    address = (request.POST.get('address') or '').strip()
    phone = ''.join(c for c in request.POST.get('phone', '') if c.isdigit())
    payment = request.POST.get('payment') if request.POST.get('payment') in dict(Checkout.PAYMENT_CHOICES) else 'COD'

    if not (name and email and address):
        messages.error(request, "Please fill in your name, email and delivery address.")
        return redirect('checkout')
    if len(phone) < 10:
        messages.error(request, "Please enter a valid 10-digit phone number.")
        return redirect('checkout')

    summary = _cart_summary(items)
    with transaction.atomic():
        order = Checkout.objects.create(
            Username=username, C_Name=name, C_Email=email, C_Address=address, C_Phone=phone[-10:],
            Subtotal=summary['subtotal'], DeliveryFee=summary['delivery'], Total=summary['grand_total'],
            Payment=payment,
        )
        OrderItem.objects.bulk_create([
            OrderItem(Order=order, Product=i.Product, ProductName=i.ProductName or '',
                      Price=i.unit_price, Quantity=i.Quantity or 1, Total=i.Total or 0)
            for i in items
        ])
        Cartdb.objects.filter(Username=username).delete()
    return redirect('ordersuccess', orderid=order.id)


def ordersuccess(request, orderid):
    blocked = _require_login(request)
    if blocked:
        return blocked
    order = get_object_or_404(Checkout, id=orderid, Username=request.session['username'])
    return render(request, "order_success.html", {'order': order})


def myorders(request):
    blocked = _require_login(request)
    if blocked:
        return blocked
    orders = Checkout.objects.filter(Username=request.session['username']).prefetch_related('items')
    return render(request, "orders.html", {'orders': orders})
