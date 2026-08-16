from django.db.models import Avg


class ReviewUtils:
    @staticmethod
    def calculate_item_name(review):
        if review.content_object:
            return review.content_object.name

    @staticmethod
    def calculate_item_average_rating(object_id, content_type):
        from review.models import Reviews

        average_rating_for_item = Reviews.objects.filter(
            object_id=object_id, content_type=content_type
        ).aggregate(Avg("rating"))
        item_avg_rating = round(average_rating_for_item.get("rating__avg", 0), 2)

        return item_avg_rating

    @staticmethod
    def calculate_review_count(review):
        from review.models import Reviews

        total_count = Reviews.objects.count()
        return total_count


class ReviewAnalyticsUtils:
    @staticmethod
    def calculate_total_customers():
        from accounts.models import CustomUser

        profile_numbers = CustomUser.objects.count()
        return profile_numbers

    @staticmethod
    def calculate_total_average_rating():
        from review.models import Reviews

        average_rating = Reviews.objects.all().aggregate(Avg("rating"))
        total_avg_rating = round(average_rating.get("rating__avg", 0), 2)
        return total_avg_rating

    @staticmethod
    def calculate_satisfacton_rate():
        from review.models import Reviews

        total_review_counts = Reviews.objects.count()
        filtered_reviews = Reviews.objects.filter(rating__gte=4).count()
        happy_reviews = (
            ((filtered_reviews / total_review_counts) * 100)
            if total_review_counts > 0
            else 0
        )
        return happy_reviews
