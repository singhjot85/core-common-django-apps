# Integrations (`core.apps.integrations`)

The `integrations` app provides a multi-tenant gateway to manage, configure, and execute third-party services (Email, SMS, Payments, etc.) uniformly across tenants.

## Architecture

```
core/apps/integrations/
├── __init__.py                     # Exports app_settings, get_integration_model, get_credentials_manager_model
├── apps.py                         # AppConfig (name="core.apps.integrations", label="integrations")
├── app_settings.py                 # BaseSettings configuration
├── constants.py                    # IntegrationKeyChoices, CredentialsNameChoices
├── models_abstract.py              # AbstractIntegration, AbstractCredentialsManager
├── models.py                       # Swappable models
├── admin.py                        # Admin registration on private_admin_site
├── utils.py                        # Facades: send_email(), send_sms()
├── email/                          # Email sub-app (label: integrations_email)
│   ├── service/                    # Base, mock, concrete EmailService & get_email_service
│   ├── models_abstract.py          # EmailLog (BaseLogModel), EmailTemplate (BaseTemplateModel)
│   └── tasks.py                    # Asynchronous log_email_dispatch Celery task
├── sms/                            # SMS sub-app (label: integrations_sms)
│   ├── service/                    # Base, mock, concrete SMSService & get_sms_service
│   ├── models_abstract.py          # SMSLog (BaseLogModel), SMSTemplate (BaseTemplateModel)
│   └── tasks.py                    # Asynchronous log_sms_dispatch Celery task
└── payments/                       # Payments sub-app (label: integrations_payments)
    ├── service/                    # Base, mock, concrete PaymentService & get_payment_service
    ├── models_abstract.py          # PaymentLog (BaseLogModel)
    └── tasks.py                    # Asynchronous log_payment_dispatch Celery task
```

## Models & Swappability Keys

| Model | Sub-App | Swappable Setting Key | Description |
| :-- | :-- | :-- | :-- |
| `Integration` | `integrations` | `INTEGRATIONS_INTEGRATION_MODEL` | Active service instance binding keys, label, webhooks, and mock toggle |
| `CredentialsManager` | `integrations` | `INTEGRATIONS_CREDENTIALS_MANAGER_MODEL` | Provider credentials, JSON details, and optional certificate/key files |
| `EmailLog` | `integrations_email` | `INTEGRATIONS_EMAIL_EMAIL_LOG_MODEL` | Email audit log tracking delivery, recipient, and backend |
| `EmailTemplate` | `integrations_email` | `INTEGRATIONS_EMAIL_EMAIL_TEMPLATE_MODEL` | Semantic versioned email template with Django template rendering |
| `SMSLog` | `integrations_sms` | `INTEGRATIONS_SMS_SMS_LOG_MODEL` | SMS delivery audit log |
| `SMSTemplate` | `integrations_sms` | `INTEGRATIONS_SMS_SMS_TEMPLATE_MODEL` | Semantic versioned SMS text template |
| `PaymentLog` | `integrations_payments` | `INTEGRATIONS_PAYMENTS_PAYMENT_LOG_MODEL` | Payment operation audit log (charges, refunds) |

## Usage Examples

### Unified Facades
```python
from core.apps.integrations.utils import send_email, send_sms

# Dispatch an email (logs asynchronously via Celery queue_task)
send_email(
    to="driver@example.com",
    subject="Welcome to RideShare",
    plain_body="Your account is ready.",
)

# Dispatch an SMS
send_sms(
    to="+15551234567",
    message="Your OTP code is 482910",
)
```

### Dynamic Service Resolution
```python
from core.apps.integrations.email.service import get_email_service

# Automatically routes to MockEmailService when integration.mock is True
email_service = get_email_service()
email_service.send(to="test@example.com", subject="Hi", plain_body="Hello")
```
