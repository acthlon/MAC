from decimal import Decimal


class CartUtils:
    @staticmethod
    def calculate_cart_total_item_count(cart):
        return cart.items.count()

    @staticmethod
    def cart_total_actual_price(cart):
        total_actual_price = 0
        for cartitem in cart.items.all():
            total_actual_price += (
                cartitem.content_object.calculate_variant_actual_unit_price
                * cartitem.quantity
                if cartitem.content_object
                else 0
            )

        return total_actual_price if total_actual_price else Decimal("0.00")

    @staticmethod
    def cart_total_discount(cart):

        # NOTE: Method 1
        total_discount = 0
        for cartitem in cart.items.all():
            sub_discount_total = (
                (cartitem.content_object.calculate_variant_discount * cartitem.quantity)
                if cartitem.content_object
                else 0
            )
            total_discount += sub_discount_total

        # # NOTE: method 2
        # total_discount = cart.items.content_object.aggregate(Sum("calculate_variant_discount" * ))[
        #     "discount__sum"
        # ]
        return total_discount if total_discount else Decimal("0.00")

    @staticmethod
    def cart_total_discounted_price(cart):

        total_discounted_price = 0
        for cartitem in cart.items.all():
            total_discounted_price += (
                (
                    cartitem.content_object.calculate_variant_discounted_price
                    * cartitem.quantity
                )
                if cartitem.content_object
                else 0
            )

        return total_discounted_price if total_discounted_price else Decimal("0.00")


class CartItemUtils:
    @staticmethod
    def calculate_item_subtotal(cartitem):

        sub_total = Decimal("0.00")

        if cartitem.content_type and cartitem.content_object:
            item = cartitem.content_object
            quantity = Decimal(str(cartitem.quantity or 1))
            discounted_price = getattr(
                cartitem.content_object, "calculate_variant_discounted_price", 0
            )
            sub_total = Decimal(str(discounted_price)) * quantity

        return sub_total.quantize(Decimal("0.00"))

    # @staticmethod
    # def calculate_percent_discount(item):

    #     percent_discount = (item.discount / item.price) * 100
    #     return percent_discount.quantize(Decimal("0.00"))

    # @staticmethod
    # def calculate_discount(item):
    #     catalog_item = getattr(item,"product",None) or getattr(item,"material",None)
    #     return catalog_item.discount


# class CartViewUtils:

#     def
