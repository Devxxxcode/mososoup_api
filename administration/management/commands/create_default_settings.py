from django.core.management.base import BaseCommand
from administration.models import Settings

class Command(BaseCommand):
    help = "Create the default settings instance if it doesn't exist."

    def handle(self, *args, **kwargs):
        if not Settings.objects.exists():
            Settings.objects.create(
                percentage_of_sponsors=50,
                bonus_when_registering=20.00,
                service_availability_start_time="00:00:00",
                service_availability_end_time="23:59:59",
                token_validity_period_hours=500,
                whatsapp_contact="+1(323) 552-4662",
                telegram_contact="@ADSupportService",
                telegram_username="@support_user",
                online_chat_url="https://tawk.to/chat/example",
                erc_address="0x028353a46...",
                trc_address="TTXVm4X...",
                minimum_balance_for_submissions=100.00,
                timezone="America/Los_Angeles"
            )
            self.stdout.write(self.style.SUCCESS("Default settings instance created."))
        else:
            self.stdout.write(self.style.WARNING("Settings instance already exists."))
