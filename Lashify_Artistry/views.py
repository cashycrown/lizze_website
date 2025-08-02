import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import EmailMessage, send_mail
from django.contrib import messages
from django.template.loader import render_to_string
from django.conf import settings
from .models import Booking

# Static Pages
def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def services(request):
    return render(request, 'services.html')

def coming_soon(request):
    return render(request, 'coming-soon.html')

def page_404(request):
    return render(request, 'page-404.html')

def contact(request):
    return render(request, 'contact.html')

def servicesDetails(request):
    return render(request, 'services-detail.html')


# Pricing Map
SERVICE_FEES = {
    'nails': 8000,
    'pedicure': 6000,
    'manicure': 5000,
    'facial': 7000,
    'lashes': 10000,
    'tattoo': 15000,
    'hair': 9000,
}


# Booking Creation View
def create_booking(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        service = request.POST.get('service')
        custom_details = request.POST.get('custom_details', '')
        date = request.POST.get('date')
        proof = request.FILES.get('payment_proof')

        # Fee & Reference
        fee = SERVICE_FEES.get(service, 5000)
        reference = str(uuid.uuid4()).replace('-', '')[:10].upper()

        # Save Booking
        booking = Booking.objects.create(
            name=name,
            email=email,
            service=service,
            custom_details=custom_details,
            date=date,
            payment_proof=proof,
            payment_method='manual',
            fee=fee,
            reference=reference,
            paid=False
        )

        # 📨 Email to Client (Booking Acknowledgement)
        client_subject = '🎉 Booking Received - Lashify Artistry'
        client_message = render_to_string('emails/confirmation_email_old.html', {
            'booking': booking,
            'site_name': 'Lashify Artistry',
        })
        client_email = EmailMessage(client_subject, client_message, to={email})
        client_email.content_subtype = 'html'
        print('SENDING TO CLIENT')
        print(f'Email to recieve confirmation {email}')
        client_email.send(fail_silently=True)

        # 📨 Email to Admin (Notification)
        admin_subject = f'📩 New Booking - {name} | {booking.get_service_display()}'
        admin_message = render_to_string('emails/admin_notification.html', {
            'booking': booking,
        })
        admin_email = EmailMessage(admin_subject, admin_message, to=['olamideadedokun36@gmail.com'])
        admin_email.content_subtype = 'html'

        # Attach payment proof if available
        if booking.payment_proof and booking.payment_proof.path:
            try:
                admin_email.attach_file(booking.payment_proof.path)
            except Exception as e:
                print(f"Error attaching file: {e}")  # Optional: log this in production

        admin_email.send(fail_silently=False)

        return redirect('booking_success', reference=reference)

    return render(request, 'services-detail.html')


# Booking Success Page
def booking_success(request, reference):
    booking = get_object_or_404(Booking, reference=reference)
    return render(request, 'booking_success.html', {'booking': booking})


# Customer Booking Tracker
def my_bookings(request):
    email = request.GET.get('email')
    bookings = Booking.objects.filter(email=email)
    return render(request, 'my_bookings.html', {'bookings': bookings})


def send_customer_confirmation(request, token):
    booking = get_object_or_404(Booking, token=token)

    subject = "Your Booking Has Been Confirmed"
    message = f"Dear {booking.full_name},\n\nYour booking for {booking.service_type} on {booking.booking_date} has been confirmed.\n\nThank you for choosing us!"
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [booking.email]

    send_mail(subject, message, from_email, recipient_list)

    messages.success(request, f"Confirmation email sent to {booking.email}")
    return redirect('admin:index')  # Or any page you want to redirect to