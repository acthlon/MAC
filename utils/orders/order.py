from datetime import timedelta
from decimal import Decimal
from secrets import token_hex

from django.db.models import DecimalField, ExpressionWrapper, F, Sum
from django.utils import timezone
from rest_framework.reverse import reverse

from core.choices import DeliveryStatus, DeliveryType, OrderStatus


class OrderItemUtils:
    @staticmethod
    def calculate_sub_total(order_item):
        sub_total = order_item.quantity * order_item.unit_price
        return sub_total

    @staticmethod
    def calculate_item_total_discount(order_item):
        discount_total = order_item.discount * order_item.quantity
        return discount_total

    @staticmethod
    def calculate_total_amount(order_item):
        total_discount_amount = OrderItemUtils.calculate_item_total_discount(order_item)
        sub_total = OrderItemUtils.calculate_sub_total(order_item)

        total_amount = sub_total - total_discount_amount
        return total_amount

    @staticmethod
    def get_image(order_item):
        images = getattr(order_item.content_object, "images", None)
        image_object = images.filter(is_primary=True).first() if images else None
        image = image_object.image if image_object else None

        return image

    @staticmethod
    def catalog_name(order_item):
        catalog_item = getattr(order_item.content_object, "product", None) or getattr(
            order_item.content_object, "material", None
        )
        return getattr(catalog_item, "name", "Custom Marvelam Item")


class OrderUtils:
    @staticmethod
    def calculate_total_items(order):

        total_items = order.items.aggregate(Sum("quantity"))["quantity__sum"] or 0
        return total_items

    # @staticmethod
    # def get_payment_reference(order):

    #     ref = order.payment_method.display_name
    #     return ref

    @staticmethod
    def calculate_sub_total_amount(order):

        sub_total_amount = order.items.aggregate(total_amount=Sum("sub_total"))[
            "total_amount"
        ] or Decimal("0.00")

        return sub_total_amount

    @staticmethod
    def calculate_total_discount_amount(order):

        total_discount_sum = order.items.aggregate(
            total_discount=Sum(
                ExpressionWrapper(
                    F("discount") * F("quantity"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )["total_discount"] or Decimal("0.00")

        return total_discount_sum

    @staticmethod
    def calculate_total_amount(order):

        total = (order.sub_total_amount + order.shipping_fee) - order.total_discount
        return total

    @staticmethod
    def generate_tracking_id(order):

        if order.id:
            unique_number = token_hex(4).upper()
            tracking_number = f"MAC-{unique_number}"
            return tracking_number
        return None

    @staticmethod
    def generate_order_number(order):

        if order.id:
            unique_number = token_hex(4).upper()
            order_number = f"ORD-{unique_number}"
            return order_number
        return None

    @staticmethod
    def get_ordered_day(order):

        date = order.created_at
        formatted_date = date.strftime("%d %b, %Y")
        return formatted_date

    @staticmethod
    def get_delivered_day(order):

        date = order.delivered_at
        formatted_date = date.strftime("%d %b, %Y")
        return formatted_date


class DeliveryMethodUtils:
    @staticmethod
    def _add_business_days(start_date, days):

        current_date = start_date
        added_day = 0
        while added_day < days:
            current_date += timedelta(days=1)
            if current_date.weekday() < 5:
                added_day += 1
        return current_date

    @staticmethod
    def delivery_day(delivery_method):
        start_date = timezone.now().date()

        if delivery_method.name == DeliveryType.STANDARD_DELIVERY:
            date1 = DeliveryMethodUtils._add_business_days(start_date, days=5)
            date2 = DeliveryMethodUtils._add_business_days(start_date, days=7)
            delivery_day = f"Delivery Between {date1.strftime('%a %d, %b.')} - {date2.strftime('%a %d %b')}"
            return delivery_day

        elif delivery_method.name == DeliveryType.EXPRESS_DELIVERY:
            date1 = DeliveryMethodUtils._add_business_days(start_date, days=3)
            date2 = DeliveryMethodUtils._add_business_days(start_date, days=5)
            delivery_day = f"Delivery Between {date1.strftime('%a %d, %b.')} - {date2.strftime('%a %d %b')}"
            return delivery_day

        elif delivery_method.name == DeliveryType.PREMIUM_DELIVERY:
            date1 = DeliveryMethodUtils._add_business_days(start_date, days=2)
            date2 = DeliveryMethodUtils._add_business_days(start_date, days=3)
            delivery_day = f"Delivery Between {date1.strftime('%a %d, %b.')} - {date2.strftime('%a %d %b')}"
            return delivery_day

        return "Delivery date not available"


class OrderItemSerializerUtils:
    @staticmethod
    def get_catalog_item(order_item, order_item_obj):
        variant_obj = order_item_obj.content_object
        catalog_item = getattr(variant_obj, "product", None) or getattr(
            variant_obj, "material", None
        )
        return catalog_item

    @staticmethod
    def get_item_create_review_url(order_item, order_item_obj):
        request = order_item.context.get("request")
        catalog_item = OrderItemSerializerUtils.get_catalog_item(
            order_item, order_item_obj
        )

        model_name = order_item_obj.content_type.model
        if not catalog_item:
            return None

        slug = catalog_item.slug
        id = order_item_obj.object_id

        url = reverse(
            "review_create",
            kwargs={
                "model_name": model_name,
                "slug": slug,
                "pk": id,
            },
            request=request,
        )
        return url

    @staticmethod
    def get_refund_request_url(order_item, order_item_obj):

        request = order_item.context.get("request")
        url = reverse(
            "create_return_request",
            kwargs={"order_number": order_item_obj.order.order_number},
            request=request,
        )

        return url

    @staticmethod
    def get_tracking_order_url(order_item, order_item_obj):

        request = order_item.context.get("request")
        url = reverse(
            "track_order",
            kwargs={"order_number": order_item_obj.order.order_number},
            request=request,
        )

        return url

    @staticmethod
    def get_item_details_url(order_item, order_item_obj):

        request = order_item.context.get("request")
        catalog_item = OrderItemSerializerUtils.get_catalog_item(
            order_item, order_item_obj
        )

        if not catalog_item:
            return None

        slug = catalog_item.slug
        id = catalog_item.id

        url_name = (
            "material_details"
            if order_item_obj.content_type.model == "materialvariant"
            else "product_details"
        )

        url = reverse(url_name, kwargs={"pk": id, "slug": slug}, request=request)
        return url


class TrackingOrderSerializerUtils:
    @staticmethod
    def get_timeline(order_obj):
        current_status = order_obj.delivery_status or order_obj.status

        # 1. Base Delivery Steps
        steps = [
            {
                "key": OrderStatus.CONFIRMED,
                "title": "Order Placed",
                "timestamp": order_obj.created_at,
                "description": "Your order has been placed successfully.",
            },
            {
                "key": DeliveryStatus.PENDING,
                "title": "Pending Confirmation",
                "timestamp": order_obj.created_at,
                "description": "Order is confirmed and being prepared.",
            },
            {
                "key": DeliveryStatus.WAITING_TO_BE_SHIPPED,
                "title": "Waiting To Be Shipped",
                "timestamp": order_obj.created_at
                if order_obj.delivery_status
                in [
                    "WAITING_TO_BE_SHIPPED",
                    "SHIPPED",
                    "OUT_FOR_DELIVERY",
                    "DELIVERED",
                    "FAILED_DELIVERY",
                    "RETURNED",
                ]
                else None,
                "description": "Order is packed and waiting for courier.",
            },
            {
                "key": DeliveryStatus.SHIPPED,
                "title": "Shipped",
                "timestamp": order_obj.shipped_at,
                "description": "Package handed over to courier.",
            },
            {
                "key": DeliveryStatus.OUT_FOR_DELIVERY,
                "title": "Out For Delivery",
                "timestamp": getattr(order_obj, "out_for_delivery_at", None),
                "description": "Package is out for delivery.",
            },
            {
                "key": DeliveryStatus.DELIVERED,
                "title": "Delivered",
                "timestamp": order_obj.delivered_at,
                "description": "Your item/order has been delivered.",
            },
        ]

        if current_status in [
            DeliveryStatus.PENDING,
            OrderStatus.CONFIRMED,
            DeliveryStatus.WAITING_TO_BE_SHIPPED,
        ]:
            steps = steps[:-3]

        if current_status == DeliveryStatus.SHIPPED:
            steps = steps[:-2]

        if current_status == DeliveryStatus.OUT_FOR_DELIVERY:
            steps = steps[:-1]

        # 2. If delivery attempt FAILED, replace "Delivered" with "Failed Delivery Attempt"
        if current_status == DeliveryStatus.FAILED_DELIVERY:
            steps[-1] = {
                "key": DeliveryStatus.FAILED_DELIVERY,
                "title": "Failed Delivery Attempt",
                "timestamp": order_obj.updated_at,
                "description": "Delivery attempt failed. Rider was unable to reach recipient.",
            }

        # 2. If previously FAILED but now DELIVERED: replace last item with BOTH steps
        if (
            current_status == DeliveryStatus.DELIVERED
            and order_obj.failed_delivery_at is not None
        ):
            steps[-1:] = [
                {
                    "key": DeliveryStatus.FAILED_DELIVERY,
                    "title": "Failed Delivery Attempt",
                    "timestamp": order_obj.failed_delivery_at,
                    "description": "Delivery attempt failed. Rider was unable to reach recipient.",
                },
                {
                    "key": DeliveryStatus.DELIVERED,
                    "title": "Delivered",
                    "timestamp": order_obj.delivered_at,
                    "description": "Your item/order has been delivered.",
                },
            ]

        # 3. If RETURNED, append the Returned Step after Delivered
        elif current_status == DeliveryStatus.RETURNED:
            steps.append(
                {
                    "key": DeliveryStatus.RETURNED,
                    "title": "Returned & Refunded",
                    "timestamp": order_obj.updated_at,
                    "description": "Item was returned and refund processed successfully.",
                }
            )

        # 4. If CANCELED before shipping
        if current_status == DeliveryStatus.CANCELED:
            steps = [
                {
                    "key": OrderStatus.CONFIRMED,
                    "title": "Order Placed",
                    "timestamp": order_obj.created_at,
                    "description": "Your order was placed.",
                },
                {
                    "key": DeliveryStatus.PENDING,
                    "title": "Pending Confirmation",
                    "timestamp": order_obj.created_at,
                    "description": "Order is confirmed and being prepared.",
                },
                {
                    "key": DeliveryStatus.CANCELED,
                    "title": "Order Canceled",
                    "timestamp": order_obj.updated_at,
                    "description": getattr(order_obj, "cancellation_reason", None)
                    or "This order was canceled.",
                },
            ]

        # 5. Build standard progression timeline
        timeline = []
        found_current = False

        for step in steps:
            key = step["key"]
            timestamp = step["timestamp"]

            is_current = current_status == key
            is_completed = (timestamp is not None) or not found_current

            if is_current:
                found_current = True
                is_completed = True

            timeline.append(
                {
                    "step_key": key,
                    "title": step["title"],
                    "date": timestamp.strftime("%d-%m-%Y") if timestamp else None,
                    "is_completed": is_completed,
                    "is_current": is_current,
                    "description": step["description"]
                    if (is_current or is_completed)
                    else "",
                }
            )

            if is_current:
                found_current = False

        return timeline
