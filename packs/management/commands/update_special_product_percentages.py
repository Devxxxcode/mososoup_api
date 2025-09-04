from django.core.management.base import BaseCommand
from packs.models import Pack


class Command(BaseCommand):
    help = "Update existing packs with default special product percentages (5x their profit_percentage)"

    def handle(self, *args, **kwargs):
        updated_count = 0
        
        for pack in Pack.objects.all():
            if pack.special_product_percentage == 0:
                # Set special product percentage to 5x the profit percentage
                pack.special_product_percentage = pack.profit_percentage * 5
                pack.save()
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Updated pack '{pack.name}' with special_product_percentage: {pack.special_product_percentage}%"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Pack '{pack.name}' already has special_product_percentage: {pack.special_product_percentage}%"
                    )
                )
        
        if updated_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated {updated_count} pack(s) with default special product percentages."
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING("No packs were updated. All packs already have special product percentages set.")
            )
