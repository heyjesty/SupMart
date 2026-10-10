from django.db import models

from backend.models import productdb


# Create your models here.
class regdb(models.Model):
    Username = models.CharField(max_length=50, null=True, blank=True)
    Email = models.EmailField(max_length=50, null=True, blank=True)
    # Holds a Django password hash (legacy plain-text values are upgraded on login)
    Password = models.CharField(max_length=128, null=True, blank=True)
    Image = models.ImageField(upload_to="userdt", null=True, blank=True)

    def __str__(self):
        return self.Username or ""


class Cartdb(models.Model):
    Username = models.CharField(null=True, blank=True, max_length=400)
    Product = models.ForeignKey(productdb, null=True, blank=True, on_delete=models.CASCADE)
    ProductName = models.CharField(null=True, blank=True, max_length=400)
    Quantity = models.IntegerField(null=True, blank=True)
    Total = models.IntegerField(null=True, blank=True)

    @property
    def unit_price(self):
        if self.Product and self.Product.Price is not None:
            return self.Product.Price
        if self.Quantity:
            return (self.Total or 0) // self.Quantity
        return self.Total or 0


class Checkout(models.Model):
    STATUS_CHOICES = [
        ("Placed", "Placed"),
        ("Packed", "Packed"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
    ]
    PAYMENT_CHOICES = [
        ("COD", "Cash on Delivery"),
        ("UPI", "UPI on Delivery"),
    ]

    Username = models.CharField(max_length=50, null=True, blank=True)
    C_Name = models.CharField(max_length=50, null=True, blank=True)
    C_Email = models.EmailField(max_length=50, null=True, blank=True)
    C_Address = models.TextField(null=True, blank=True)
    C_Phone = models.CharField(max_length=15, null=True, blank=True)
    Subtotal = models.IntegerField(default=0)
    DeliveryFee = models.IntegerField(default=0)
    Total = models.IntegerField(default=0)
    Payment = models.CharField(max_length=10, choices=PAYMENT_CHOICES, default="COD")
    Status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Placed")
    Created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["-id"]

    @property
    def order_number(self):
        return f"SM{self.id:06d}"


class OrderItem(models.Model):
    Order = models.ForeignKey(Checkout, related_name="items", on_delete=models.CASCADE)
    Product = models.ForeignKey(productdb, null=True, blank=True, on_delete=models.SET_NULL)
    ProductName = models.CharField(max_length=400)
    Price = models.IntegerField(default=0)
    Quantity = models.IntegerField(default=1)
    Total = models.IntegerField(default=0)
