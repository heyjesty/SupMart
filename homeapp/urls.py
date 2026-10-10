from django.urls import path

from homeapp import views

urlpatterns = [
    path('', views.homepage, name="home_root"),
    path('homepage/', views.homepage, name="homepage"),
    path('aboutus/', views.aboutus, name="aboutus"),
    path('contactus/', views.contactus, name="contactus"),
    path('shop/', views.shop, name="shop"),
    path('pro/<catname>/', views.pro, name="pro"),
    path('singleproduct/<int:proid>', views.singleproduct, name="singleproduct"),
    path('singleproduct/<int:proid>/', views.singleproduct, name="singleproduct_slash"),
    path('register/', views.register, name="register"),
    path('loginpg/', views.loginpg, name="loginpg"),
    path('registersave/', views.registersave, name="registersave"),
    path('userlogin/', views.userlogin, name="userlogin"),
    path('logout/', views.logout, name="logout"),
    path('cartsave/', views.cartsave, name="cartsave"),
    path('cartdisplay/', views.cartdisplay, name="cartdisplay"),
    path('cartupdate/<int:dataid>/', views.cartupdate, name="cartupdate"),
    path('cartdel/<int:dataid>/', views.cartdel, name="cartdel"),
    path('checkout/', views.checkout, name="checkout"),
    path('checksave/', views.checksave, name="checksave"),
    path('order/<int:orderid>/', views.ordersuccess, name="ordersuccess"),
    path('myorders/', views.myorders, name="myorders"),
]
