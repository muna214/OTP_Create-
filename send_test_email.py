from django.core.mail import send_mail

send_mail(
    subject='SMTP Test',
    message='SMTP connection and email test successful.',
    from_email='ummemuna14@gmail.com',        #Use your own mail 
    recipient_list=['ummemuna14@gmail.com'],  #Use your own mail
    fail_silently=False,
)
