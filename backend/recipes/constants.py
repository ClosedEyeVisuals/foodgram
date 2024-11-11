from string import ascii_letters, digits

# Константы модели ингредиента
MAX_INGREDIENT_NAME_LENGTH = 128
MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH = 64
MIN_INGREDIENT_AMOUNT = 1

# Константы модели рецепта
MAX_RECIPE_NAME_LENGTH = 256
MAX_RECIPE_SHORT_URL_LENGTH = 10
MIN_RECIPE_COOKING_TIME = 1
SHORT_URL_LENGTH = 5
SHORT_URL_SYMBOLS = ascii_letters + digits + '_-'

# Константы модели тега
MAX_TAG_NAME_LENGTH = 32
MAX_TAG_SLUG_LENGTH = 32

# Константы модели пользователя
MAX_EMAIL_LENGTH = 254
MAX_FIRST_NAME_LENGTH = 150
MAX_LAST_NAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 128
MAX_USERNAME_LENGTH = 150

# Остальные константы проекта
PAGE_SIZE = 6