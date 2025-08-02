from django.db import models
from django.core.mail import EmailMessage, send_mail
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
import uuid

def send_admin_booking_notification(booking):
    try:
        current_site = Site.objects.get_current()
        confirm_url = f"http://{current_site.domain}{reverse('send_customer_confirmation', args=[booking.confirmation_token])}"

        message = f"""
📥 New Booking Received!

👤 Name: {booking.name}
💅 Service: {booking.get_service_display()}
📧 Email: {booking.email}
📅 Date: {booking.date}
💳 Payment Method: {booking.get_payment_method_display()}

Click below to verify and send confirmation to the customer:
🔗 {confirm_url}
"""

        send_mail(
            subject="📥 New Booking Notification - Lashify Artistry",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=["admin@example.com"],  # Update with your real admin email
            fail_silently=False,
        )
    except Exception as e:
        print("Failed to send admin notification:", e)


class Booking(models.Model):
    SERVICE_CHOICES = [
        ('nails', 'Nail Tech'),
        ('pedicure', 'Pedicure'),
        ('manicure', 'Manicure'),
        ('facial', 'Facial Treatment'),
        ('lashes', 'Lash Extension'),
        ('tattoo', 'Semi-Permanent Tattoo'),
        ('hair', 'Hair Styling'),
    ]

    PAYMENT_METHODS = [
        ('manual', 'Manual Transfer'),
        ('paystack', 'Paystack (Online)'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    service = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    custom_details = models.TextField(blank=True)
    date = models.DateField()
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=5000)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHODS, default='manual')
    payment_verified = models.BooleanField(default=False)
    payment_proof = models.ImageField(upload_to='proofs/', blank=True, null=True)
    reference = models.CharField(max_length=100, unique=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verification_notes = models.TextField(blank=True, null=True)
    verification_slip = models.ImageField(upload_to='verification_slips/', blank=True, null=True)
    confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.get_service_display()} on {self.date}"
    
    '''
    def save(self, *args, **kwargs):
        is_new = self.pk is None  # Check if it's a new booking
        send_verification_email = False

        if self.pk:
            previous = Booking.objects.get(pk=self.pk)
            if not previous.paid and self.paid:
                send_verification_email = True

        super().save(*args, **kwargs)  # Save booking

        # 📨 Send verification email if just paid
        if send_verification_email and self.email and self.verification_slip:
            email = EmailMessage(
                subject="✅ Payment Verified - Lashify Artistry",
                body=f"""
                    Hi {self.name},

                    Your payment for {self.get_service_display()} has been successfully verified.

                    📅 Appointment Date: {self.date}
                    💵 Fee: ₦{self.fee}
                    📌 Reference: {self.reference}

                    Attached is your proof of verification.

                    We look forward to seeing you!

                    With love,  
                    Lashify Artistry 💖
                    """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[self.email],
            )
            email.attach_file(self.verification_slip.path)
            email.send(fail_silently=True)

        # 📧 Send admin notification if it's a new booking
        # if is_new:
        #     send_admin_booking_notification(self)
    '''