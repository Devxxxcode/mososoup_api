import random
from decimal import Decimal
from itertools import combinations

# Function to select products within range
def select_products_within_range(products, min_amount, max_amount, max_products):
    """
    Select a combination of products whose total price is within the specified range
    and whose number equals max_products.

    Args:
        products (list): A list of product dictionaries with 'name' and 'price' keys.
        min_amount (Decimal): Minimum total price.
        max_amount (Decimal): Maximum total price.
        max_products (int): Exact number of products to select.

    Returns:
        list: A list of selected product instances (dictionaries), or an empty list if no combination is found.
    """
    # Randomize product order
    random.shuffle(products)

    # Use a generator to lazily produce combinations
    product_combinations = (combination for combination in combinations(products, max_products))

    # Iterate through combinations lazily
    for combination in product_combinations:
        # Calculate the total price for the combination
        total_price = sum(Decimal(product['price']) for product in combination)

        # Check if total price falls within the specified range
        if min_amount <= total_price <= max_amount:
            return list(combination)  # Return the first valid combination

    # If no valid combination is found, return an empty list
    return []

# Generate 1000 random products
products = [
    {"name": f"Product {i}", "price": str(Decimal(random.uniform(10, 300)).quantize(Decimal('0.01')))}
    for i in range(1, 1001)
]
print(products)

# Test the function
min_amount = Decimal("200.00")
max_amount = Decimal("300.00")
max_products = 2

result = select_products_within_range(products, min_amount, max_amount, max_products)

# Print the result
if result:
    print("Selected Products:")
    for product in result:
        print(product)
else:
    print("No valid combination found.")
