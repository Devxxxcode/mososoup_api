from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from .models import Pack
from wallet.models import Wallet


def select_best_active_pack_for_balance(balance):
    """
    Select the best active pack for a given balance:
    - Highest usd_value <= balance
    - If none, fall back to the lowest usd_value active pack
    """
    packs = Pack.objects.filter(is_active=True).order_by('-usd_value')
    assigned = None
    for p in packs:
        if balance >= p.usd_value:
            assigned = p
            break
    if not assigned:
        assigned = Pack.objects.filter(is_active=True).order_by('usd_value').first()
    return assigned


@receiver(post_delete, sender=Pack)
def reassign_wallets_on_pack_delete(sender, instance: Pack, **kwargs):
    """
    When a Pack is deleted, reassign all wallets that referenced it
    to the closest suitable active pack by balance.
    """
    affected_wallets = Wallet.objects.filter(package=None) | Wallet.objects.filter(package=instance)
    for wallet in affected_wallets.select_related('user'):
        best_pack = select_best_active_pack_for_balance(wallet.balance)
        if best_pack:
            wallet.package = best_pack
            wallet.save(update_fields=['package', 'updated_at'])


@receiver(post_save, sender=Pack)
def reassign_wallets_on_pack_inactive(sender, instance: Pack, created: bool, **kwargs):
    """
    When a Pack is updated to inactive, reassign all wallets on that pack
    to the closest suitable active pack by balance.
    """
    if created:
        return
    if instance.is_active:
        return
    affected_wallets = Wallet.objects.filter(package=instance)
    for wallet in affected_wallets.select_related('user'):
        best_pack = select_best_active_pack_for_balance(wallet.balance)
        if best_pack:
            wallet.package = best_pack
            wallet.save(update_fields=['package', 'updated_at'])

