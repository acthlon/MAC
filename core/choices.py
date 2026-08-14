from django.db import models

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

IS_PRIMARY_CHOICES = (
    (True, "True"),
    (False, "False"),
)


class Status(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class ProductCategory(models.TextChoices):
    DRESS = "DRESS", "Dress"
    GOWN = "GOWN", "Gown"
    KAFTAN = "KAFTAN", "Kaftan"
    ABAYA = "ABAYA", "Abaya"
    BOUBOU = "BOUBOU", "Boubou"
    JUMPSUIT = "JUMPSUIT", "Jumpsuit"
    TWO_PIECE = "TWO_PIECE", "Two Piece Set"
    ACCESSORY = "ACCESSORY", "Accessory"


class MaterialCategory(models.TextChoices):
    ANK = "ANK", "Ankara"
    SLK = "SLK", "Silk"
    LAC = "LAC", "Lace"
    CHF = "CHF", "Chiffon"
    COT = "COT", "Cotton"
    LIN = "LIN", "Linen"
    JCQ = "JCQ", "Jacquard"
    VLV = "VLV", "Velvet"
    BRC = "BRC", "Brocade"
    ADR = "ADR", "Adire (Indigo Tie-Dye)"
    KMP = "KMP", "Kampala (Multi-color Tie-Dye)"
    ASO = "ASO", "Aso Oke"
    GRG = "GRG", "George Fabric"
    AOC = "AOC", "Akwa Ocha"
    SEN = "SEN", "Senator Cashmere"


class Pattern(models.TextChoices):
    PLN = "PLN", "Plain / Solid"
    FLR = "FLR", "Floral"
    STP = "STP", "Striped"
    CHK = "CHK", "Checked / Plaid"
    DOT = "DOT", "Polka Dot"
    ABS = "ABS", "Abstract"
    EMB = "EMB", "Embroidered"
    PTN = "PTN", "Patterned"


class ProductSize(models.TextChoices):
    XS = "XS", "Extra Small"
    S = "S", "Small"
    M = "M", "Medium"
    L = "L", "Large"
    XL = "XL", "Extra Large"
    XXL = "XXL", "Double Extra Large"
    SIZE_52 = "52", "Size 52 (52 inches)"
    SIZE_54 = "54", "Size 54 (54 inches)"
    SIZE_56 = "56", "Size 56 (56 inches)"
    SIZE_58 = "58", "Size 58 (58 inches)"
    SIZE_60 = "60", "Size 60 (60 inches)"


class Color(models.TextChoices):
    BLK = "BLK", "Black"
    WHT = "WHT", "White"
    GLD = "GLD", "Gold"
    SLV = "SLV", "Silver"
    BGE = "BGE", "Beige"
    CRM = "CRM", "Cream"
    NVY = "NVY", "Navy Blue"
    FGR = "FGR", "Forest Green"
    MRN = "MRN", "Maroon or Wine"
    BRN = "BRN", "Brown"
    PNK = "PNK", "Pink"
    PRP = "PRP", "Purple"
    GRY = "GRY", "Grey"


class Quality(models.TextChoices):
    LUXURY = "LUXURY", "Luxury"
    PREMIUM = "PREMIUM", "Premium"
    REGULAR = "REGULAR", "Regular"


class Rating(models.IntegerChoices):
    POOR = 1, "Poor"
    FAIR = 2, "Fair"
    GOOD = 3, "Good"
    VERY_GOOD = 4, "Very Good"
    EXCELLENT = 5, "Excellent"


POOR, FAIR, GOOD, VERY_GOOD, EXCELLENT = (
    Rating.POOR,
    Rating.FAIR,
    Rating.GOOD,
    Rating.VERY_GOOD,
    Rating.EXCELLENT,
)


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESSFUL = "SUCCESSFUL", "Successful"
    FAILED = "FAILED", "Failed"


class RefundStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Review"
    UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"
    COMPLETED = "COMPLETED", "Refund Completed"


class ActionStatus(models.TextChoices):
    APPROVED = "APPROVED", "Approved"
    REJECTED = "REJECTED", "Rejected"


FABRIC_CARE_INSTRUCTIONS = {
    MaterialCategory.ANK: "Hand wash or gentle machine wash cold with mild detergent. Do not bleach. Hang to dry in shade to prevent fading. Iron on the reverse side with medium heat.",
    MaterialCategory.SLK: "Dry clean recommended. Or hand wash cold with silk-safe detergent. Do not wring or twist. Lay flat to dry in shade. Iron on low heat on the reverse side while slightly damp.",
    MaterialCategory.LAC: "Hand wash cold with mild soap. Do not wring or scrub. Lay flat to dry. If ironing is needed, use lowest heat setting and place a pressing cloth between the iron and lace.",
    MaterialCategory.CHF: "Hand wash cold or gentle machine wash in a mesh laundry bag. Line dry in shade. Use a steamer or iron on low/synthetic setting.",
    MaterialCategory.COT: "Machine wash cold or warm with similar colors. Tumble dry on low heat or line dry. Iron on high heat (cotton setting) while slightly damp.",
    MaterialCategory.LIN: "Machine wash cold or warm. Line dry recommended. Iron on high heat on the reverse side while the fabric is still damp to easily remove wrinkles.",
    MaterialCategory.JCQ: "Dry clean only to protect the woven patterns. Do not bleach. Iron on medium heat with a damp pressing cloth between the iron and fabric.",
    MaterialCategory.VLV: "Dry clean only. Never iron directly as it crushes the velvet fibers. Use a steamer on the reverse side or hang in a steamy bathroom to release wrinkles.",
    MaterialCategory.BRC: "Dry clean only. Avoid rubbing or brushing. Iron on medium-low heat on the reverse side using a dry pressing cloth.",
    MaterialCategory.ADR: "Hand wash cold separately for the first few washes as indigo dye may bleed. Use mild soap. Do not bleach. Line dry in the shade. Iron on reverse.",
    MaterialCategory.KMP: "Hand wash cold separately or gentle machine wash cold. Do not wring. Dry in the shade. Iron on the reverse side on medium heat.",
    MaterialCategory.ASO: "Dry clean only. Do not machine wash or submerge in water. If wrinkled, press with medium heat on the reverse side using a protective cloth.",
    MaterialCategory.GRG: "Dry clean only due to the heavy metallic embroidery and beadwork. Do not iron directly on the embroidery; use steam or press on the reverse on low heat.",
    MaterialCategory.AOC: "Dry clean only to maintain the pure white hand-loomed cotton structure. Press on medium heat with a protective white cloth.",
    MaterialCategory.SEN: "Dry clean only. Do not machine wash or tumble dry. Hang on a padded hanger to maintain shape. Iron on medium/wool setting using a pressing cloth.",
}
