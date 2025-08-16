from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from email.mime.image import MIMEImage
import uuid
import logging

from .models import Booking

logger = logging.getLogger(__name__)

# ================= BASIC PAGES =================
def index(request): 
    return render(request, 'index.html')

def about(request): 
    return render(request, 'about.html')

def services(request): 
    return render(request, 'services.html')

def coming_soon(request): 
    return render(request, 'coming-soon.html')

def page_404(request): 
    return render(request, '404.html')

def contact(request): 
    return render(request, 'contact.html')

def servicesDetails(request): 
    return render(request, 'services-detail.html')


# ================= BOOKINGS =================
@csrf_exempt
def create_booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        service = request.POST.get('service')
        date = request.POST.get('date')
        fee = request.POST.get('fee', '0').replace("₦", "").strip()
        payment_method = request.POST.get('payment_method')
        image_proof = request.FILES.get("payment_proof")

        # Create booking object
        booking = Booking.objects.create(
            name=name,
            email=email,
            service=service,
            date=date,
            fee=Decimal(fee or "0"),
            payment_method=payment_method,
            created_at=timezone.now(),
            payment_proof=image_proof,
            confirmation_token=uuid.uuid4()
        )

        # Confirmation URL
        confirmation_url = request.build_absolute_uri(
            f"/confirm/{booking.confirmation_token}/"
        )

        # Clean service name
        if hasattr(booking, "get_service_display"):
            service_display = booking.get_service_display()
        else:
            service_display = str(booking.service).replace("_", " ").title()

        # Clean payment method
        if hasattr(booking, "get_payment_method_display"):
            payment_display = booking.get_payment_method_display()
        else:
            payment_display = str(booking.payment_method).replace("_", " ").title()

        # ---------- Admin Email ----------
        admin_subject = f"New Booking - {service_display}"
        admin_message = f"""
<html>
<body>
<h2>📥 New Booking Received!</h2>
<p><strong>👤 Name:</strong> {booking.name}<br>
<strong>💅 Service:</strong> {service_display}<br>
<strong>📧 Email:</strong> {booking.email}<br>
<strong>📅 Date:</strong> {booking.date}<br>
<strong>💳 Payment Method:</strong> {payment_display}<br>
<strong>💰 Fee:</strong> ₦{booking.fee}</p>

<p>Click below to verify and send confirmation to the customer:<br>
<a href="{confirmation_url}">{confirmation_url}</a></p>
"""

        # Inline proof image if uploaded
        email_admin = EmailMessage(
            subject=admin_subject,
            body=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=getattr(settings, "ADMINS_EMAILS", [settings.DEFAULT_FROM_EMAIL]),
        )
        email_admin.content_subtype = "html"  # Enable HTML

        if booking.payment_proof:
            try:
                with booking.payment_proof.open("rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", "<proof>")
                    email_admin.attach(img)

                # add image to body
                email_admin.body += '<p><b>Payment Proof:</b><br><img src="cid:proof" style="max-width:400px;"></p>'
            except Exception as e:
                logger.error(f"Could not embed payment proof: {e}")

        email_admin.send(fail_silently=False)

        # ---------- Customer Email ----------
        customer_subject = "Your Booking Confirmation - Lashify Artistry"
        customer_message = f"""
Hi {booking.name},<br><br>

Thank you for booking with Lashify Artistry! 💖<br><br>

💅 <b>Service:</b> {service_display}<br>
📅 <b>Date:</b> {booking.date}<br>
💰 <b>Booking Fee:</b> ₦{booking.fee}<br>
💳 <b>Payment Method:</b> {payment_display}<br><br>

Please confirm your booking by clicking below:<br>
<a href="{confirmation_url}">{confirmation_url}</a><br><br>

With love,<br>
Lashify Artistry
"""
        email_customer = EmailMessage(
            subject=customer_subject,
            body=customer_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.email],
        )
        email_customer.content_subtype = "html"  # Send as HTML
        email_customer.send(fail_silently=False)

        return render(request, 'booking_success.html', {'booking': booking})

    return redirect('home')


def booking_success(request, reference):
    return render(request, 'booking-success.html', {'reference': reference})


def my_bookings(request):
    bookings = Booking.objects.all().order_by('-date')
    return render(request, 'my-bookings.html', {'bookings': bookings})


def send_customer_confirmation(request, token):
    """Customer clicks confirmation link -> mark booking + send final email."""
    booking = get_object_or_404(Booking, confirmation_token=token)

    if hasattr(booking, "get_service_display"):
        service_display = booking.get_service_display()
    else:
        service_display = str(booking.service).replace("_", " ").title()

    confirmation_message = f"""
Hi {booking.name},<br><br>

Your booking for <b>{service_display}</b> on {booking.date} has been confirmed ✅.<br><br>

Thank you,<br>
Lashify Artistry
"""
    email = EmailMessage(
        subject="Booking Confirmed - Lashify Artistry",
        body=confirmation_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email],
    )
    email.content_subtype = "html"
    email.send(fail_silently=False)

    return HttpResponse("Booking confirmed and email sent.")
