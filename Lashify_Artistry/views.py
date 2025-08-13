from decimal import Decimal
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.shortcuts import render, redirect, get_object_or_404
import logging
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
from .models import Booking
from django.utils import timezone

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

# ========== EMAIL FUNCTION ==========
def send_booking_email(name, email, service, date, fee, payment_method):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    # Admin notification
    admin_email = settings.ADMIN_EMAIL  # Add in settings.py
    admin_content = f"""
    New booking received:

    Name: {name}
    Email: {email}
    Service: {service}
    Date: {date}
    Fee: {fee}
    Payment Method: {payment_method}
    """

    # Customer confirmation
    customer_content = f"""
    Hi {name},

    Your booking for {service} on {date} is confirmed!

    Thank you,
    Lashify Artistry
    """

    try:
        # Send to admin
        api_instance.send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": admin_email}],
            sender={"name": "Lashify Artistry", "email": admin_email},
            subject=f"New Booking from {name}",
            text_content=admin_content
        ))

        # Send to customer
        api_instance.send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            sender={"name": "Lashify Artistry", "email": admin_email},
            subject="Booking Confirmation - Lashify Artistry",
            text_content=customer_content
        ))

        logger.info(f"Brevo emails sent to admin and {email}")
    except ApiException as e:
        logger.error(f"Brevo API error: {e}")

# ========== BOOKINGS ==========
def send_brevo_email(subject, html_content, recipient_email):
    """Send transactional email via Brevo API."""
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
        logger.info(f"Brevo email sent to {recipient_email}")
    except ApiException as e:
        logger.error(f"Brevo API error: {e}")

@csrf_exempt
def create_booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        service = request.POST.get('service')
        date = request.POST.get('date')
        fee = request.POST.get('fee').replace("₦",'')
        print(f"fee received from frontend  {fee}")
        payment_method = request.POST.get('payment_method')
        image_proof = request.FILES.get("payment_proof")

        booking = Booking.objects.create(
            name=name,
            email=email,
            service=service,
            date=date,
            fee=Decimal(fee),
            #payment_method=payment_method,
            created_at=timezone.now(),
            payment_proof=image_proof
        )
        
        try:
            configuration = sib_api_v3_sdk.Configuration()
            configuration.api_key['api-key'] = settings.BREVO_API_KEY

            api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

            # Admin notification
            admin_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": settings.ADMIN_EMAIL}],
                sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "Lashify Artistry"},
                subject=f"New Booking - {service}",
                html_content=f"""
                <h3>New Booking Received</h3>
                <p><strong>Name:</strong> {name}</p>
                <p><strong>Email:</strong> {email}</p>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Fee:</strong> ₦{fee}</p>
                <p><strong>Payment Method:</strong> {payment_method}</p>
                """
            )
            api_instance.send_transac_email(admin_email)

            # Customer confirmation
            customer_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": email}],
                sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "Lashify Artistry"},
                subject="Your Booking Confirmation",
                html_content=f"""
                <h3>Hi {name},</h3>
                <p>Thank you for booking with Lashify Artistry!</p>
                <p><strong>Service:</strong> {service}</p>
                <p><strong>Date:</strong> {date}</p>
                <p><strong>Booking Fee:</strong> ₦{fee}</p>
                <p>We look forward to seeing you.</p>
                """
            )
            api_instance.send_transac_email(customer_email)

        except ApiException as e:
            logger.error(f"Brevo API error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error while sending emails: {e}")
        
        return render(request, 'booking_success.html', {'booking': booking})

    return redirect('home')

def booking_success(request, reference):
    return render(request, 'booking-success.html', {'reference': reference})

def my_bookings(request):
    bookings = Booking.objects.all().order_by('-date')
    return render(request, 'my-bookings.html', {'bookings': bookings})

def send_customer_confirmation(request, token):
    booking = get_object_or_404(Booking, token=token)
    send_booking_email(booking.name, booking.email, booking.service, booking.date, booking.fee, booking.payment_method)
    return HttpResponse("Booking confirmed and email sent.")
def send_booking_email(name, email, service, date, fee, payment_method):
    if not settings.BREVO_API_KEY:
        logger.error("BREVO_API_KEY is not set")
        return

    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = settings.BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    admin_email = settings.ADMIN_EMAIL
    admin_content = f"""
    New booking received:

    Name: {name}
    Email: {email}
    Service: {service}
    Date: {date}
    Fee: {fee}
    Payment Method: {payment_method}
    """

    customer_content = f"""
    Hi {name},

    Your booking for {service} on {date} is confirmed!

    Thank you,
    Lashify Artistry
    """

    try:
        # Send to admin
        api_instance.send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": admin_email}],
            sender={"name": "Lashify Artistry", "email": admin_email},
            subject=f"New Booking from {name}",
            text_content=admin_content
        ))

        # Send to customer
        api_instance.send_transac_email(sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email}],
            sender={"name": "Lashify Artistry", "email": admin_email},
            subject="Booking Confirmation - Lashify Artistry",
            text_content=customer_content
        ))

        logger.info(f"Brevo emails sent to admin and {email}")

    except ApiException as e:
        logger.error(f"Brevo API error: {e}")

