from django.db import models
from django.core.mail import EmailMessage
from django.conf import settings
from django.contrib.sites.models import Site
from django.urls import reverse
import uuid
import random
import string


def generate_reference_code():
    """
    Generates a random reference code consisting of uppercase letters and digits.
    Default length is 10 characters.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choices(characters, k=16))


def send_admin_booking_notification(booking):
    """
    Send an email to admin when a new booking is created.
    Uses Brevo SMTP (configured in settings.py).
    """
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

        email = EmailMessage(
            subject="📥 New Booking Notification - Lashify Artistry",
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=["admin@example.com"],  # Change to your real admin email
        )
        email.send(fail_silently=False)

    except Exception as e:
        print("❌ Failed to send admin notification:", e)


class Booking(models.Model):
    # models.py

    SERVICE_CHOICES = [
    # Tattoos
    ('tattoo', 'Semi Permanent Tattoos'),

    # Gel Nails
    ('GNSL_nails', 'Gel nails (short length)'),
    ('GNML_nails', 'Gel nails (medium length)'),
    ('GNLL_nails', 'Gel nails (long length)'),

    # Acrylic Nails - Short
    ('ANSLP_nails', 'Acrylic nails short length plain'),
    ('ANSLFT_nails', 'Acrylic nails short length french tips'),
    ('ANSLED_nails', 'Acrylic nails short length extra designs'),

    # Acrylic Nails - Medium
    ('ANMLP_nails', 'Acrylic nails medium length plain'),
    ('ANMLFT_nails', 'Acrylic nails medium length french tips'),
    ('ANMLED_nails', 'Acrylic nails medium length extra designs'),

    # Acrylic Nails - Long
    ('ANLLP_nails', 'Acrylic nails long length plain'),
    ('ANLLFT_nails', 'Acrylic nails long length french tips'),
    ('ANLLED_nails', 'Acrylic nails long length extra designs'),

    # Acrylic Nails - Extra Long
    ('ANELLP_nails', 'Acrylic nails extra long length plain'),
    ('ANELLFT_nails', 'Acrylic nails extra long length french tips'),
    ('ANELLED_nails', 'Acrylic nails extra long length extra designs'),

    # Lashes
    ('C_lashes', 'Classic Lashes'),
    ('H_lashes', 'Hybrid Lashes'),
    ('V_lashes', 'Volume Lashes'),
    ('MV_lashes', 'Mega Volume Lashes'),

    # Pedicures
    ('N_pedicure', 'Normal Pedicure'),
    ('F_pedicure', 'French Pedicure'),
    ('P_pedicure', 'Paraffin Pedicure'),

    # Others
    ('hair', 'Hair Styling'),
    ('manicure', 'Manicure'),
    ('facial', 'Facial Treatment'),
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
    reference = models.CharField(max_length=100, unique=True, default=generate_reference_code)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verification_notes = models.TextField(blank=True, null=True)
    verification_slip = models.ImageField(upload_to='verification_slips/', blank=True, null=True)
    confirmation_token = models.UUIDField(default=uuid.uuid4, editable=False, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.get_service_display()} on {self.date}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        send_verification_email = False

        if self.pk:
            previous = Booking.objects.get(pk=self.pk)
            if not previous.paid and self.paid:
                send_verification_email = True

        super().save(*args, **kwargs)

        # ✅ Send payment verification email to customer
        if send_verification_email and self.email and self.verification_slip:
            try:
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
                email.send(fail_silently=False)
            except Exception as e:
                print("❌ Failed to send payment verification email:", e)

        # 📧 Send admin notification for new bookings
        if is_new:
            send_admin_booking_notification(self)

