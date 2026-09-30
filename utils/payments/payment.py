from core.choices import ReturnStatus


class PaymentUtils:
    @staticmethod
    def masked_card(payment):
        if payment.card_brand and payment.card_last4:
            return f"{payment.card_brand}******{payment.card_last4}"
        return "N/A"


class ReturnUtils:
    @staticmethod
    def generate_return_number(refund_obj):
        if not (refund_obj.order and refund_obj.order.order_number):
            from secrets import token_hex  # isort: skip

            return f"RET-{token_hex(4).upper()}"

        base_code = refund_obj.order.order_number.replace("ORD-", "")

        # 1. Full Order Return -> RET-A1B2C3D4
        if not refund_obj.order_item:
            return f"RET-{base_code}"

        # 2. Single Item Return -> Find 1-based index position of order_item in order
        item_ids = list(refund_obj.order.items.values_list("id", flat=True))

        if refund_obj.order_item.id in item_ids:
            item_position = item_ids.index(refund_obj.order_item.id) + 1
            return f"RET-{base_code}-{item_position}"

        return f"RET-{base_code}-1"

    @staticmethod
    def generate_return_tracking_id(refund_obj):
        # 1. Use order.tracking_id (e.g., "MAC-5F6E7D8C") if available
        if refund_obj.order and refund_obj.order.tracking_id:
            base_code = refund_obj.order.tracking_id.replace("MAC-", "").replace(
                "TRK-", ""
            )

            if not refund_obj.order_item:
                return f"TRK-RET-{base_code}"
            item_ids = list(refund_obj.order.items.values_list("id", flat=True))

            if refund_obj.order_item and refund_obj.order_item.id in item_ids:
                item_position = item_ids.index(refund_obj.order_item.id) + 1
                return f"TRK-RET-{base_code}-{item_position}"

            return f"TRK-RET-{base_code}-1"

        return None


class TrackingReturnRequestSerializerUtils:
    @staticmethod
    def get_timeline(return_obj):
        current_status = return_obj.status

        # 1. Base Return Steps
        steps = [
            {
                "key": ReturnStatus.PENDING,
                "title": "Return Requested",
                "timestamp": return_obj.created_at,
                "description": "Your return request has been submitted and is pending review.",
            },
            {
                "key": ReturnStatus.UNDER_REVIEW,
                "title": "Under Review",
                "timestamp": return_obj.created_at
                if current_status
                in [
                    ReturnStatus.UNDER_REVIEW,
                    ReturnStatus.APPROVED,
                    ReturnStatus.COMPLETED,
                ]
                else None,
                "description": "Our team is reviewing your return request and evidence.",
            },
            {
                "key": ReturnStatus.APPROVED,
                "title": "Return Approved",
                "timestamp": return_obj.approved_at,
                "description": f"Return approved. Tracking ID: {return_obj.return_tracking_id or 'N/A'}",
            },
            {
                "key": ReturnStatus.COMPLETED,
                "title": "Refund Completed",
                "timestamp": return_obj.processed_at,
                "description": f"Refund of {return_obj.return_amount or '0.00'} NGN processed via {return_obj.refund_method or 'original payment method'}.",
            },
        ]

        # 2. Branch for REJECTED Return Requests
        if current_status == ReturnStatus.REJECTED:
            steps = [
                {
                    "key": ReturnStatus.PENDING,
                    "title": "Return Requested",
                    "timestamp": return_obj.created_at,
                    "description": "Your return request was submitted.",
                },
                {
                    "key": ReturnStatus.UNDER_REVIEW,
                    "title": "Under Review",
                    "timestamp": return_obj.created_at
                    if current_status
                    in [
                        ReturnStatus.UNDER_REVIEW,
                        ReturnStatus.APPROVED,
                        ReturnStatus.COMPLETED,
                    ]
                    else None,
                    "description": "Our team is reviewing your return request and evidence.",
                },
                {
                    "key": ReturnStatus.REJECTED,
                    "title": "Return Request Rejected",
                    "timestamp": return_obj.updated_at,
                    "description": return_obj.rejection_reason
                    or "Your return request was reviewed and rejected.",
                },
            ]

        # 3. Build step-by-step timeline progression
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
                    "date": timestamp.strftime("%d-%m-%Y %H:%M") if timestamp else None,
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
