from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import uuid
import logging

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings

from .models import Booking

logger = logging.getLogger(__name__)

# ========== BASIC PAGES ==========
def index(request): return render(request, 'index.html')
def about(request): return render(request, 'about.html')
def services(request): return render(request, 'services.html')
def coming_soon(request): return render(request, 'coming-soon.html')
def page_404(request): return render(request, '404.html')
def contact(request): return render(request, 'contact.html')
def servicesDetails(request): return render(request, 'services-detail.html')


# ========== EMAIL HELPER ==========
def send_brevo_email(subject, html_content, recipient_email):
    """Reusable function to send transactional email via Brevo."""
    if not settings.BREVO_API_KEY:
        logger.error("❌ BREVO_API_KEY is not set in settings.py")
        return False

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender = {"name": "Lashify Artistry", "email": settings.DEFAULT_FROM_EMAIL}
    to = [{"email": recipient_email}]

    email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender=sender,
        subject=subject,
        html_content=html_content
    )

    try:
        api_instance.send_transac_email(email)
        logger.info(f"✅ Brevo email sent to {recipient_email}")
        return True
    except ApiException as e:
        logger.error(f"❌ Brevo API error: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error sending email: {e}")

    return False


# ========== BOOKINGS ==========
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

        print(f"fee received from frontend: {fee}")

        booking = Booking.objects.create(
            name=name,
            email=email,
            service=service,
            date=date,
            fee=Decimal(fee),
            payment_method=payment_method,
            created_at=timezone.now(),
            payment_proof=image_proof,
            confirmation_token=uuid.uuid4()   # ✅ generate token
        )

        # Confirmation URL for customer
        confirmation_url = request.build_absolute_uri(f"/confirm/{booking.confirmation_token}/")

        # --- Admin notification ---
        admin_html = f"""
        <h3>New Booking Received</h3>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Service:</strong> {service}</p>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>Fee:</strong> ₦{fee}</p>
        <p><strong>Payment Method:</strong> {payment_method}</p>
        """
        send_brevo_email(f"New Booking - {service}", admin_html, settings.ADMIN_EMAIL)

        # --- Customer confirmation ---
        customer_html = f"""
        <h3>Hi {name},</h3>
        <p>Thank you for booking with Lashify Artistry!</p>
        <p><strong>Service:</strong> {service}</p>
        <p><strong>Date:</strong> {date}</p>
        <p><strong>Booking Fee:</strong> ₦{fee}</p>
        <p>Please confirm your booking by clicking below:</p>
        <p><a href="{confirmation_url}">Confirm Booking</a></p>
        """
        send_brevo_email("Your Booking Confirmation - Lashify Artistry", customer_html, email)

        return render(request, 'booking_success.html', {'booking': booking})

    return redirect('home')


def booking_success(request, reference):
    return render(request, 'booking-success.html', {'reference': reference})


def my_bookings(request):
    bookings = Booking.objects.all().order_by('-date')
    return render(request, 'my-bookings.html', {'bookings': bookings})


def send_customer_confirmation(request, token):
    """Customer clicks confirmation link -> we mark booking + send final emails."""
    booking = get_object_or_404(Booking, confirmation_token=token)

    # Send confirmation notice
    confirmation_html = f"""
    Hi {booking.name},

    Your booking for {booking.service} on {booking.date} has been confirmed ✅.

    Thank you,
    Lashify Artistry
    """
    send_brevo_email("Booking Confirmed - Lashify Artistry", confirmation_html, booking.email)

    return HttpResponse("Booking confirmed and email sent.")
