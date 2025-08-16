from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
import uuid
import logging

from .models import Booking

logger = logging.getLogger(__name__)

# ========== BASIC PAGES ==========
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


# ========== EMAIL HELPER ==========
def send_app_email(subject, message, recipient_email):
    """
    Simple reusable function for sending emails via Django's email backend.
    (No Brevo SDK, just uses SMTP configured in settings.py)
    """
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        logger.info(f"✅ Email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
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
        admin_msg = f"""
        New Booking Received

        Name: {name}
        Email: {email}
        Service: {service}
        Date: {date}
        Fee: ₦{fee}
        Payment Method: {payment_method}
        """
        send_app_email(f"New Booking - {service}", admin_msg, settings.ADMIN_EMAIL)

        # --- Customer confirmation ---
        customer_msg = f"""
        Hi {name},

        Thank you for booking with Lashify Artistry!

        Service: {service}
        Date: {date}
        Booking Fee: ₦{fee}

        Please confirm your booking by clicking this link:
        {confirmation_url}

        Best regards,
        Lashify Artistry
        """
        send_app_email("Your Booking Confirmation - Lashify Artistry", customer_msg, email)

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

    confirmation_msg = f"""
    Hi {booking.name},

    Your booking for {booking.service} on {booking.date} has been confirmed ✅.

    Thank you,
    Lashify Artistry
    """
    send_app_email("Booking Confirmed - Lashify Artistry", confirmation_msg, booking.email)

    return HttpResponse("Booking confirmed and email sent.")
