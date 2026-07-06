PRODUCT_CATEGORY_CHOICES = [
    ('DRESS', 'Dress'),
    ('GOWN', 'Gown'),
    ('KAFTAN', 'Kaftan'),
    ('ABAYA', 'Abaya'),
    ('BOUBOU', 'Boubou'),
    ('JUMPSUIT', 'Jumpsuit'),
    ('TWO_PIECE', 'Two Piece Set'),
    ('ACCESSORY', 'Accessory'),
]

MATERIAL_CATEGORY_CHOICES = [
    ('ANK', 'Ankara'),
    ('SLK', 'Silk'),
    ('LAC', 'Lace'),
    ('CHF', 'Chiffon'),
    ('COT', 'Cotton'),
    ('LIN', 'Linen'),
    ('JCQ', 'Jacquard'),
    ('VLV', 'Velvet'),
    ('BRC', 'Brocade'),
    ('ADR', 'Adire (Indigo Tie-Dye)'),
    ('KMP', 'Kampala (Multi-color Tie-Dye)'),
    ('ASO', 'Aso Oke'),
    ('GRG', 'George Fabric'),
    ('AOC', 'Akwa Ocha'),
    ('LAC', 'Lace'),
    ('SEN', 'Senator Cashmere'),
]



PATTERN_CHOICES = [
    ('PLN', 'Plain / Solid'),
    ('FLR', 'Floral'),
    ('STP', 'Striped'),
    ('CHK', 'Checked / Plaid'),
    ('DOT', 'Polka Dot'),
    ('ABS', 'Abstract'),
    ('EMB', 'Embroidered'),
    ('PTN', 'Patterned'),
]



PRODUCT_SIZE_CHOICES = [
    ('XS', 'Extra Small'),
    ('S', 'Small'),
    ('M', 'Medium'),
    ('L', 'Large'),
    ('XL', 'Extra Large'),
    ('XXL', 'Double Extra Large'),
    ('52', 'Size 52 (52 inches)'),
    ('54', 'Size 54 (54 inches)'),
    ('56', 'Size 56 (56 inches)'),
    ('58', 'Size 58 (58 inches)'),
    ('60', 'Size 60 (60 inches)'),
]


COLOR_CHOICES = [
    ('BLK', 'Black'),
    ('WHT', 'White'),
    ('GLD', 'Gold'),
    ('SLV', 'Silver'),
    ('BGE', 'Beige'),
    ('CRM', 'Cream'),
    ('NVY', 'Navy Blue'),
    ('FGR', 'Forest Green'),
    ('MRN', 'Maroon or Wine'),
    ('BRN', 'Brown'),
    ('PNK', 'Pink'),
    ('PRP', 'Purple'),
    ('GRY', 'Grey'),
]



QUALITY_CHOICES = [   
    ('LUXURY', 'Luxury'),
    ('PREMIUM', 'Premium'),
    ('REGULAR', 'Regular'),
]




EXCELLENT = 5
VERY_GOOD = 4
GOOD = 3
FAIR = 2
POOR = 1 


RATING_CHOICES = [
    (EXCELLENT,'Excellent'),
    (VERY_GOOD,'Very Good'),
    (GOOD,'Good'),
    (FAIR,'Fair'),
    (POOR,'Poor'),
]


PAYMENT_STATUS_CHOICES = [
    ('PENDING','Pending'),
    ('SUCCESSFUL','Successful'),
    ('FAILED','Failed')
]


REFUND_STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('UNDER_REVIEW','Under Review'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Refund Completed'),
    ]


ACTION_CHOICES = [
    ('APPROVED','Approved'),
    ('REJECTED','Rejected'),
]



FABRIC_CARE_INSTRUCTIONS = {
    'ANK': 'Hand wash or gentle machine wash cold with mild detergent. Do not bleach. Hang to dry in shade to prevent fading. Iron on the reverse side with medium heat.',
    
    'SLK': 'Dry clean recommended. Or hand wash cold with silk-safe detergent. Do not wring or twist. Lay flat to dry in shade. Iron on low heat on the reverse side while slightly damp.',
    
    'LAC': 'Hand wash cold with mild soap. Do not wring or scrub. Lay flat to dry. If ironing is needed, use lowest heat setting and place a pressing cloth between the iron and lace.',
    
    'CHF': 'Hand wash cold or gentle machine wash in a mesh laundry bag. Line dry in shade. Use a steamer or iron on low/synthetic setting.',
    
    'COT': 'Machine wash cold or warm with similar colors. Tumble dry on low heat or line dry. Iron on high heat (cotton setting) while slightly damp.',
    
    'LIN': 'Machine wash cold or warm. Line dry recommended. Iron on high heat on the reverse side while the fabric is still damp to easily remove wrinkles.',
    
    'JCQ': 'Dry clean only to protect the woven patterns. Do not bleach. Iron on medium heat with a damp pressing cloth between the iron and fabric.',
    
    'VLV': 'Dry clean only. Never iron directly as it crushes the velvet fibers. Use a steamer on the reverse side or hang in a steamy bathroom to release wrinkles.',
    
    'BRC': 'Dry clean only. Avoid rubbing or brushing. Iron on medium-low heat on the reverse side using a dry pressing cloth.',
    
    'ADR': 'Hand wash cold separately for the first few washes as indigo dye may bleed. Use mild soap. Do not bleach. Line dry in the shade. Iron on reverse.',
    
    'KMP': 'Hand wash cold separately or gentle machine wash cold. Do not wring. Dry in the shade. Iron on the reverse side on medium heat.',
    
    'ASO': 'Dry clean only. Do not machine wash or submerge in water. If wrinkled, press with medium heat on the reverse side using a protective cloth.',
    
    'GRG': 'Dry clean only due to the heavy metallic embroidery and beadwork. Do not iron directly on the embroidery; use steam or press on the reverse on low heat.',
    
    'AOC': 'Dry clean only to maintain the pure white hand-loomed cotton structure. Press on medium heat with a protective white cloth.',
    
    'SEN': 'Dry clean only. Do not machine wash or tumble dry. Hang on a padded hanger to maintain shape. Iron on medium/wool setting using a pressing cloth.'
}