from django.apps import AppConfig


class OrderConfig(AppConfig):
    name = "order"

    def ready(self):
        import order.signal  # isort: skip
