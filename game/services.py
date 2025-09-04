from django.utils.timezone import now, timedelta
from .models import Game, Product,generate_unique_rating_no
import random
from django.db import transaction
from users.models import Invitation
from decimal import Decimal
from shared.helpers import get_settings,create_admin_notification,create_user_notification


class PlayGameService:
    """
    Service to handle the logic for playing a game and assigning the next game.
    """

    def __init__(self, user, total_number_can_play, wallet):
        self.user = user
        self.total_number_can_play = total_number_can_play
        self.wallet = wallet
        self.settings = get_settings()
        self.pack = wallet.package

    def check_can_user_play(self):
        """
        Check if the user is eligible to play a game.
        Returns a tuple: (can_play: bool, message: str)
        """
        if self.wallet.balance < 0:
            return False, "You have a negative balance, please add funds to proceed."
        # Use per-pack minimum balance if check is not removed for this user
        if not self.user.is_min_balance_for_submission_removed:
            pack_min = getattr(self.pack, 'minimum_balance_for_submissions', None)
            if pack_min is not None:
                if self.wallet.balance < pack_min:
                    return False, f"You need a minimum of {pack_min} USD balance for your current pack to review albums."
            else:
                # Fallback to global settings for backward compatibility
                min_balance = getattr(self.settings, 'minimum_balance_for_submissions', 100)
                if self.wallet.balance < min_balance:
                    return False, f"You need a minimum of {min_balance} USD balance to review albums."
        cancel_play, messgae = self.user_has_completed_all_set_or_needs_reset()
        if cancel_play:
            return False,messgae
        return True, ""
    
    def get_ordinal(self,number):
        """
        Convert an integer into its ordinal representation.
        E.g., 1 -> '1st', 2 -> '2nd', 3 -> '3rd', etc.
        """
        if 10 <= number % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        return f"{number}{suffix}"

    def user_has_completed_all_set_or_needs_reset(self):
        """
        Check if the user has completed all sets or needs to reset.
        Returns a tuple: (has_completed: bool, message: str)
        """
        set_number = self.get_ordinal(self.user.number_of_submission_set_today)
        if Game.count_games_played_today(self.user) >= self.total_number_can_play and self.pack.number_of_set > self.user.number_of_submission_set_today: 
            return True, f"Good job!!!. The {set_number} set of album reviews has been completed. Kindly request for the next sets."
        if Game.count_games_played_today(self.user) >= self.total_number_can_play and self.pack.number_of_set <= self.user.number_of_submission_set_today: 
            return True, f"Good job!!!. You have completed all {self.user.number_of_submission_set_today + 1} album review sets for today!!!"
        return False,""
    
    def check_can_user_play_pending_game(self):
        """
        Check if the user is eligible to play a pending game.
        Returns a tuple: (can_play: bool, message: str)
        """
        if self.wallet.balance < 0:
            return False, "You have a negative balance, please add funds to proceed."
        if Game.count_games_played_today(self.user) >= self.total_number_can_play:
            return False, "You have reached the maximum number of albums you can review today. Please upgrade your package for more options."
        return True, ""

    def get_active_game(self):
        """
        Retrieve the user's active game.
        Special games now take immediate priority over existing active games.
        Returns a tuple: (game: Game or None, error: str)
        """
        # HIGHEST PRIORITY: Check for pending special games first
        pending_special_game = Game.objects.filter(user=self.user, played=False, pending=True, is_active=True, special_product=True).first()
        if pending_special_game:
            return pending_special_game, ""
        
        # SECOND PRIORITY: Check for new special games that should be activated immediately
        target_game_number = Game.count_games_played_today(self.user) + 1
        
        # Get the first available special game for this appearance
        special_game = Game.objects.filter(
            user=self.user, 
            played=False, 
            special_product=True, 
            game_number=target_game_number, 
            is_active=True
        ).order_by('created_at').first()  # Order by creation time to pick the first one
        
        if special_game:
            try:
                hold_value = special_game.on_hold
                if not hold_value:
                    return special_game, ""
                
                min_value = float(hold_value.min_amount)  # Convert to float
                max_value = float(hold_value.max_amount)  # Convert to float
                balance = self.user.wallet.balance

                random_amount = Decimal(random.uniform(min_value, max_value))  # Generate a random float and convert to Decimal
                amount = balance + random_amount
                amount = Decimal(round(amount, 2))  # Round to 2 decimal places
                special_game.amount = amount
                special_game.pending = True
                
                # Use debit method for consistency - this will handle balance and on_hold correctly
                self.wallet.debit(amount)
                
                special_game.save()
                self.wallet.save()

                return special_game, ""
            except Exception as e:
                # If there's an error, still return the special game but without processing
                return special_game, ""
        
        # THIRD PRIORITY: Check for pending regular games
        pending_regular_game = Game.objects.filter(user=self.user, played=False, pending=True, is_active=True, special_product=False).first()
        if pending_regular_game:
            return pending_regular_game, ""
        
        # FOURTH PRIORITY: Check for active regular games
        active_game = Game.objects.filter(user=self.user, played=False, is_active=True, special_product=False).first()
        if active_game:
            active_game.pending = True
            active_game.save()
            return active_game, ""

        # If no active game exists, try to assign a new one
        game, message = self.assign_next_game()
        if game:
            return game, None  # Return game with no error
        else:
            return None, message  # Return error message if assignment failed

    def mark_game_as_played(self, game, rating_score, comment):
        """
        Mark the current active game as played and update it with a rating and comment.
        """
        amount = game.amount
        commission = game.commission

        if game.pending:
            self.wallet.credit(commission)
            self.wallet.credit_commission(commission)
        else:
            if self.wallet.balance < amount and game.special_product:
                game.pending = True
                game.save()
                
                # Use debit method for consistency - this will handle balance and on_hold correctly
                self.wallet.debit(amount)
                
                return False, "Insufficient balance to review this album."

            self.wallet.credit(commission)
            self.wallet.credit_commission(commission)

        game.rating_score = rating_score
        game.comment = comment
        game.played = True
        game.pending = False
        
        # Check if this was a special game and if there are more special games for the same appearance
        should_increment_submission = True
        if game.special_product:
            # Check if there are more unplayed special games for the same appearance
            remaining_special_games = Game.objects.filter(
                user=self.user,
                special_product=True,
                played=False,
                is_active=True,
                game_number=game.game_number
            ).exclude(pk=game.pk).exists()
            
            if remaining_special_games:
                # Don't increment submission count - user stays at same appearance
                should_increment_submission = False
        
        if should_increment_submission:
            self.user.number_of_submission_today += 1
            self.user.today_profit += commission
            self.user.save()
            self.handle_referral_bonus(commission)

            if self.user.number_of_submission_today >= self.total_number_can_play:
                self.user.number_of_submission_set_today += 1
                self.user.save()
                set_number = self.get_ordinal(self.user.number_of_submission_set_today)
                create_admin_notification("Worker Set Completed",f"{self.user.username} has completed all album reviews in the {set_number} set, You can proceed to reset account")
                if self.user.number_of_submission_set_today <  self.pack.number_of_set:
                    create_user_notification(self.user,"Album Review Set Completed",f"Good job!!!. The {set_number} set of album reviews has been completed. Kindly request for the next sets.")
                
            if self.user.number_of_submission_set_today >=  self.pack.number_of_set:
                create_user_notification(self.user,"Good job!!! Album Review Set Completed",f"You have completed all {self.user.number_of_submission_set_today} album review sets for today!!!!!!")
                create_admin_notification("Worker Set Completed",f"{self.user.username} has completed all {self.user.number_of_submission_set_today} album review sets for today")
        else:
            self.user.today_profit += commission
            self.user.save()
            # Still handle referral bonus for special games
            self.handle_referral_bonus(commission)
        
        self.user.save()
        game.save()

        return True, ""
    
    def handle_referral_bonus(self,commission_amount):
        """
        Give the user that referred the user a bonus balance
        """
        try:
            user = self.user
            invitation = getattr(user, "invitation", None)
            if not invitation:
                # print(f"No invitation found for user {user.username}.")
                return
            settings = self.settings
            bonus_percentage = Decimal(settings.percentage_of_sponsors)  # Ensure it's Decimal
            bonus_amount = commission_amount * (bonus_percentage / Decimal(100))  # Use Decimal for calculation
            referral = invitation.referral
            if not hasattr(referral, "wallet") or not referral.wallet:
                print(f"Referrer {referral.username} does not have a wallet.")
                return
            
            with transaction.atomic():
                referral.wallet.balance += bonus_amount
                referral.current_referral_bonus += bonus_amount
                referral.wallet.save()
                referral.save()

                if referral.current_referral_bonus >= Decimal(10):
                    referral.current_referral_bonus -= Decimal(10)
                    referral.save()
                    create_user_notification(
                    referral,
                    "Referral Bonus",
                    "You have received a total of 10 USD for referral bonus!!!!"
                    )
        except Invitation.DoesNotExist:
            print(f"No invitation found for user {user.username}.")
        except Exception as e:
            # Catch unexpected errors
            print(f"An error occurred while processing referral bonus: {str(e)}")
        

    def assign_next_game(self):
        """
        Assign the next game for the user with smart product selection based on balance.
        Prioritizes products around the user's balance, avoiding products that are too low
        when there are better options available.
        Returns a tuple: (game: Game or None, message: str)
        """
        start_of_day = now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        # Get all products the user has played today
        played_products_today = Game.objects.filter(
            user=self.user,
            is_active=True,
            created_at__gte=start_of_day,
            created_at__lt=end_of_day
        ).values_list('products__id', flat=True)

        # Get products the user hasn't played today
        available_products = Product.objects.exclude(id__in=played_products_today)

        # Smart product selection based on user balance
        selected_products = self.select_smart_products(available_products, self.wallet.balance)
        
        if not selected_products:
            return None, "No suitable albums available for your current balance. Please add funds to access more album options."

        # Calculate the total amount and commission
        total_amount = sum(product.price for product in selected_products)
        if self.wallet.package:
            commission_percentage = self.wallet.package.profit_percentage
        else:
            commission_percentage = 0.5  # Default to 20% if no package is available

        commission = (total_amount * commission_percentage) / 100

        # Create a new game instance
        new_game = Game.objects.create(
            user=self.user,
            played=False,
            pending=True,
            amount=total_amount,
            commission=commission,
            commission_percentage=commission_percentage,
            is_active=True,
            rating_no=generate_unique_rating_no()
        )

        # Associate the selected products with the new game
        new_game.products.set(selected_products)

        new_game.save()

        return new_game, "New album assigned! Review and rate to earn your commission."

    def select_smart_products(self, available_products, user_balance):
        """
        Smart product selection that prioritizes products around the user's balance.
        Selects one product, prioritizing from 100% down to 1% of user balance.
        Falls back to all products (including played ones) if no suitable products found.
        
        Args:
            available_products: QuerySet of available products
            user_balance: User's current wallet balance
            
        Returns:
            list: Selected products for the game (always one product)
        """
        if not available_products.exists():
            return []
            
        # Convert to list and sort by price for better selection
        products_list = list(available_products.order_by('price'))
        
        # Define balance ranges for smart selection (100% down to 1%)
        balance_100_percent = user_balance * Decimal('1.0')    # 100% of balance
        balance_80_percent = user_balance * Decimal('0.8')     # 80% of balance
        balance_60_percent = user_balance * Decimal('0.6')     # 60% of balance
        balance_40_percent = user_balance * Decimal('0.4')     # 40% of balance
        balance_20_percent = user_balance * Decimal('0.2')     # 20% of balance
        balance_10_percent = user_balance * Decimal('0.1')     # 10% of balance
        balance_5_percent = user_balance * Decimal('0.05')     # 5% of balance
        balance_1_percent = user_balance * Decimal('0.01')     # 1% of balance
        
        # Priority 1: Products at 100% of user balance (exact match)
        exact_balance_products = [
            p for p in products_list 
            if p.price == user_balance
        ]
        
        # Priority 2: Products around 80-100% of user balance (optimal range)
        optimal_products = [
            p for p in products_list 
            if balance_80_percent <= p.price < user_balance
        ]
        
        # Priority 3: Products around 60-80% of user balance (good range)
        good_products = [
            p for p in products_list 
            if balance_60_percent <= p.price < balance_80_percent
        ]
        
        # Priority 4: Products around 40-60% of user balance (acceptable range)
        acceptable_products = [
            p for p in products_list 
            if balance_40_percent <= p.price < balance_60_percent
        ]
        
        # Priority 5: Products around 20-40% of user balance (low range)
        low_products = [
            p for p in products_list 
            if balance_20_percent <= p.price < balance_40_percent
        ]
        
        # Priority 6: Products around 10-20% of user balance (very low range)
        very_low_products = [
            p for p in products_list 
            if balance_10_percent <= p.price < balance_20_percent
        ]
        
        # Priority 7: Products around 5-10% of user balance (minimal range)
        minimal_products = [
            p for p in products_list 
            if balance_5_percent <= p.price < balance_10_percent
        ]
        
        # Priority 8: Products around 1-5% of user balance (fallback range)
        fallback_products = [
            p for p in products_list 
            if balance_1_percent <= p.price < balance_5_percent
        ]
        
        # Smart selection logic - always select ONE product
        selected_product = None
        
        # Try to select from highest priority ranges first
        if exact_balance_products:
            selected_product = random.choice(exact_balance_products)
        elif optimal_products:
            selected_product = random.choice(optimal_products)
        elif good_products:
            selected_product = random.choice(good_products)
        elif acceptable_products:
            selected_product = random.choice(acceptable_products)
        elif low_products:
            selected_product = random.choice(low_products)
        elif very_low_products:
            selected_product = random.choice(very_low_products)
        elif minimal_products:
            selected_product = random.choice(minimal_products)
        elif fallback_products:
            selected_product = random.choice(fallback_products)
        
        # If still no product selected, fallback to ALL products (including played ones)
        if not selected_product:
            all_products = list(Product.objects.all().order_by('price'))
            
            # Find products that fit within user balance
            affordable_all_products = [
                p for p in all_products 
                if p.price <= user_balance
            ]
            
            if affordable_all_products:
                # Select the highest priced product that fits
                selected_product = max(affordable_all_products, key=lambda x: x.price)
            else:
                # If no products fit at all, select the lowest priced product
                selected_product = all_products[0] if all_products else None
        
        # Return as list (always one product)
        return [selected_product] if selected_product else []

    def play_game(self, rating_score, comment):
        """
        Main method to mark the active game as played and assign the next game.
        Returns a tuple: (game: Game or None, message: str)
        """

        # Retrieve the active game or assign a new one
        active_game, error = self.get_active_game()
        if not active_game:
            return None, error
        
        if active_game.pending:
            # Check if the user is eligible to play
            can_play, message = self.check_can_user_play()
            if not can_play:
                return None, message
        else:
            # Check if the user is eligible to play
            can_play, message = self.check_can_user_play()
            if not can_play:
                return None, message

        # Mark the current active game as played with rating and comment
        played,error_playing = self.mark_game_as_played(active_game, rating_score, comment)

        # Assign the next game
        # next_game, error = self.get_active_game()
        if error:
            return None, error

        return active_game, "Album reviewed successfully!" if played else error_playing

    def play_pending_game(self, rating_score, comment):
        """
        Main method to mark the active game as played and assign the next game.
        Returns a tuple: (game: Game or None, message: str)
        """
        # Check if the user is eligible to play
        can_play, message = self.check_can_user_play_pending_game()
        if not can_play:
            return None, message

        # Retrieve the active game or assign a new one
        active_game, error = self.get_active_game()
        if error:
            return None, error

        # Mark the current active game as played with rating and comment
        played,error_playing = self.mark_game_as_played(active_game, rating_score, comment)

        # Assign the next game
        # next_game, error = self.get_active_game()
        if error:
            return None, error

        return active_game, "Album reviewed successfully!" if played else error_playing

