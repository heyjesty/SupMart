from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from backend.models import categorydb, productdb


# Create your views here.
# index page
def indexpage(req):
    return render(req, "index.html")


# category page
def categorypage(req):
    return render(req, "category.html")


def categorysave(req):
    if req.method == "POST":
        cn = req.POST.get('categoryname')
        dn = req.POST.get('description')
        img = req.FILES.get('image')
        if not img:
            messages.error(req, "Please select an image")
            return redirect(categorypage)
        obj = categorydb(CategoryName=cn, Description=dn, Image=img)
        obj.save()
        messages.success(req, "Category Saved Successfully")
        return redirect(categorypage)
    return redirect(categorypage)


def categorydisplay(req):
    data = categorydb.objects.all()
    return render(req, "categorydisplay.html", {'data': data})


def categoryedit(req, dataid):
    data = get_object_or_404(categorydb, id=dataid)
    return render(req, "categoryedit.html", {'data': data})


def categoryupdate(req, dataid):
    if req.method == "POST":
        ct = req.POST.get('categoryname')
        ds = req.POST.get('description')
        category = get_object_or_404(categorydb, id=dataid)
        category.CategoryName = ct
        category.Description = ds
        img = req.FILES.get('image')
        if img:
            category.Image = img
        category.save()
        messages.success(req, "Update Successfully")
        return redirect(categorydisplay)
    return redirect(categorydisplay)


def categorydelete(req, dataid):
    categorydb.objects.filter(id=dataid).delete()
    messages.warning(req, "Delete Successfully")
    return redirect(categorydisplay)


# product page
def productpage(req):
    cat = categorydb.objects.all()
    return render(req, "product.html", {'cat': cat})


def productsave(req):
    if req.method == "POST":
        ct = req.POST.get('category')
        pn = req.POST.get('productname')
        ds = req.POST.get('description')
        pr = req.POST.get('price')
        img = req.FILES.get('image')
        if not img:
            messages.error(req, "Please select an image")
            return redirect(productpage)
        obj = productdb(Category=ct, ProductName=pn, Description=ds, Price=pr, Image=img)
        obj.save()
        messages.success(req, "Product Saved Successfully")
        return redirect(productpage)
    return redirect(productpage)


def productdisplay(req):
    data = productdb.objects.all()
    return render(req, "productdisplay.html", {'data': data})


def productedit(req, dataid):
    cat = categorydb.objects.all()
    data = get_object_or_404(productdb, id=dataid)
    return render(req, "productedit.html", {'data': data, 'cat': cat})


def productupdate(req, dataid):
    if req.method == "POST":
        ct = req.POST.get('category')
        pn = req.POST.get('productname')
        ds = req.POST.get('description')
        pr = req.POST.get('price')
        prod = get_object_or_404(productdb, id=dataid)
        prod.Category = ct
        prod.ProductName = pn
        prod.Description = ds
        prod.Price = pr
        img = req.FILES.get('image')
        if img:
            prod.Image = img
        prod.save()
        messages.success(req, "Update Successfully")
        return redirect(productdisplay)
    return redirect(productdisplay)


def productdelete(req, dataid):
    productdb.objects.filter(id=dataid).delete()
    messages.warning(req, "Delete Successfully")
    return redirect(productdisplay)


# admin page
def adminpage(req):
    return render(req, "adminpage.html")


def adminsave(request):
    if request.method == "POST":
        uname = request.POST.get('username')
        pwd = request.POST.get('password')
        user = authenticate(request, username=uname, password=pwd)
        if user is not None:
            login(request, user)
            request.session['username'] = uname
            request.session['password'] = pwd
            messages.success(request, "Login Successfully")
            return redirect(indexpage)
        else:
            messages.error(request, "Invalid username or password")
            return redirect(adminpage)
    return redirect(adminpage)


def adminlogut(request):
    request.session.pop('username', None)
    request.session.pop('password', None)
    messages.success(request, "Logout Successfully")
    return redirect(adminpage)

