from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
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
📥 New Booking Received!

👤 Name: {booking.name}
💅 Service: {service_display}
📧 Email: {booking.email}
📅 Date: {booking.date}
💳 Payment Method: {payment_display}
💰 Fee: ₦{booking.fee}

Click below to verify and send confirmation to the customer:
🔗 {confirmation_url}
"""
        email_admin = EmailMessage(
            subject=admin_subject,
            body=admin_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=getattr(settings, "ADMINS_EMAILS", [settings.DEFAULT_FROM_EMAIL]),
        )

        # Attach proof if uploaded
        if booking.payment_proof:
            try:
                # Open the file safely from storage
                with booking.payment_proof.open("rb") as f:
                    email_admin.attach(
                        booking.payment_proof.name,
                        f.read(),
                        booking.payment_proof.file.content_type
                    )
            except Exception as e:
                logger.error(f"Could not attach payment proof: {e}")

        email_admin.send(fail_silently=False)

        # ---------- Customer Email ----------
        customer_subject = "Your Booking Confirmation - Lashify Artistry"
        customer_message = f"""
Hi {booking.name},

Thank you for booking with Lashify Artistry! 💖

💅 Service: {service_display}
📅 Date: {booking.date}
💰 Booking Fee: ₦{booking.fee}
💳 Payment Method: {payment_display}

Please confirm your booking by clicking below:
{confirmation_url}

With love,
Lashify Artistry
"""
        email_customer = EmailMessage(
            subject=customer_subject,
            body=customer_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[booking.email],
        )
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

    # Format service name
    if hasattr(booking, "get_service_display"):
        service_display = booking.get_service_display()
    else:
        service_display = str(booking.service).replace("_", " ").title()

    confirmation_message = f"""
Hi {booking.name},

Your booking for {service_display} on {booking.date} has been confirmed ✅.

Thank you,
Lashify Artistry
"""
    email = EmailMessage(
        subject="Booking Confirmed - Lashify Artistry",
        body=confirmation_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[booking.email],
    )
    email.send(fail_silently=False)

    return HttpResponse("Booking confirmed and email sent.")
