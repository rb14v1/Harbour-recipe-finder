"""
Idempotent data migration seeding a demo user and a handful of varied
recipes, each with an embedding computed via apps.common.ai.get_embedding
at seed time (stub vectors when OPENAI_API_KEY is unset, which is expected
and fine for demo/dev purposes).

Safe to run repeatedly: looks up the demo user/recipes by natural key
(email / title) before inserting, so `migrate` never duplicates rows.
"""
from django.conf import settings
from django.db import migrations

DEMO_EMAIL = "demo@example.com"
DEMO_PASSWORD = "demo12345"

RECIPES = [
    {
        "title": "Classic Margherita Pizza",
        "ingredients": "pizza dough, tomato sauce, fresh mozzarella, basil leaves, olive oil, salt",
        "instructions": (
            "Preheat oven to 475F with a pizza stone if available. Stretch dough into a "
            "12-inch round. Spread a thin layer of tomato sauce, leaving a 1-inch border. "
            "Tear mozzarella and scatter over the sauce. Bake for 10-12 minutes until the "
            "crust is golden and cheese bubbles. Top with fresh basil and a drizzle of "
            "olive oil before serving."
        ),
    },
    {
        "title": "Chicken and Broccoli Stir-Fry",
        "ingredients": "chicken breast, broccoli florets, garlic, soy sauce, ginger, cornstarch, vegetable oil, rice",
        "instructions": (
            "Slice chicken into thin strips and toss with cornstarch. Heat oil in a wok "
            "over high heat and stir-fry chicken until golden, about 4 minutes. Remove and "
            "set aside. Add broccoli, garlic, and ginger to the wok, stir-fry for 3 minutes. "
            "Return chicken to the wok, add soy sauce, and toss everything together for 2 "
            "more minutes. Serve over steamed rice."
        ),
    },
    {
        "title": "Spaghetti Carbonara",
        "ingredients": "spaghetti, pancetta, eggs, pecorino romano, black pepper, garlic",
        "instructions": (
            "Cook spaghetti in salted boiling water until al dente. Meanwhile, render "
            "pancetta in a skillet until crisp. Whisk eggs with grated pecorino and black "
            "pepper. Drain pasta, reserving some pasta water, and toss immediately with the "
            "pancetta off the heat. Add the egg mixture, stirring quickly to create a creamy "
            "sauce, loosening with reserved pasta water as needed."
        ),
    },
    {
        "title": "Thai Green Curry",
        "ingredients": "green curry paste, coconut milk, chicken thigh, thai eggplant, bamboo shoots, basil, fish sauce, palm sugar",
        "instructions": (
            "Fry green curry paste in a splash of coconut milk until fragrant. Add the rest "
            "of the coconut milk and bring to a simmer. Add sliced chicken thigh and cook "
            "through. Stir in eggplant and bamboo shoots, simmer until tender. Season with "
            "fish sauce and palm sugar, finish with Thai basil leaves."
        ),
    },
    {
        "title": "Vegetable Fried Rice",
        "ingredients": "cooked rice, carrots, peas, eggs, green onion, soy sauce, sesame oil, garlic",
        "instructions": (
            "Scramble eggs in a hot wok and set aside. Saute garlic, carrots, and peas until "
            "tender. Add day-old rice, breaking up clumps, and stir-fry until heated through. "
            "Return eggs to the wok, add soy sauce and sesame oil, and toss with chopped "
            "green onion before serving."
        ),
    },
    {
        "title": "Black Bean Tacos",
        "ingredients": "black beans, corn tortillas, onion, lime, cilantro, cumin, avocado, queso fresco",
        "instructions": (
            "Saute diced onion until soft, add black beans and cumin, mash lightly and heat "
            "through. Warm corn tortillas on a dry skillet. Fill tortillas with the bean "
            "mixture and top with sliced avocado, crumbled queso fresco, chopped cilantro, "
            "and a squeeze of lime."
        ),
    },
    {
        "title": "Beef Bourguignon",
        "ingredients": "beef chuck, red wine, bacon lardons, pearl onions, mushrooms, carrots, thyme, garlic, flour",
        "instructions": (
            "Brown beef chuck cubes in rendered bacon fat, then set aside. Saute pearl "
            "onions, carrots, and mushrooms. Stir in flour, then deglaze with red wine. "
            "Return beef and bacon to the pot, add thyme and garlic, and braise covered for "
            "2.5 hours until the beef is fork-tender."
        ),
    },
    {
        "title": "Greek Salad",
        "ingredients": "cucumber, tomato, red onion, kalamata olives, feta cheese, olive oil, oregano, red wine vinegar",
        "instructions": (
            "Chop cucumber, tomato, and red onion into bite-sized pieces. Combine in a bowl "
            "with olives and a block of feta on top. Whisk olive oil, red wine vinegar, and "
            "oregano, and drizzle over the salad just before serving."
        ),
    },
    {
        "title": "Lentil Soup",
        "ingredients": "red lentils, onion, carrot, celery, cumin, turmeric, vegetable broth, lemon",
        "instructions": (
            "Saute onion, carrot, and celery until softened. Add cumin and turmeric and "
            "toast briefly. Stir in red lentils and vegetable broth, simmer for 25 minutes "
            "until the lentils break down. Finish with a squeeze of lemon juice before "
            "serving."
        ),
    },
    {
        "title": "Shrimp Pad Thai",
        "ingredients": "rice noodles, shrimp, eggs, bean sprouts, tofu, tamarind paste, fish sauce, peanuts, lime",
        "instructions": (
            "Soak rice noodles until pliable. Stir-fry shrimp and tofu until shrimp turns "
            "pink. Push aside, scramble eggs in the same pan. Add noodles and a sauce of "
            "tamarind paste, fish sauce, and sugar, tossing to coat. Fold in bean sprouts, "
            "top with crushed peanuts and lime wedges."
        ),
    },
    {
        "title": "Mushroom Risotto",
        "ingredients": "arborio rice, mixed mushrooms, white wine, parmesan, vegetable stock, onion, butter",
        "instructions": (
            "Saute onion in butter until translucent, add mushrooms and cook until golden. "
            "Stir in arborio rice to toast briefly, then deglaze with white wine. Add warm "
            "stock one ladle at a time, stirring constantly until absorbed before adding "
            "more. Finish with grated parmesan and a knob of butter."
        ),
    },
    {
        "title": "Baked Salmon with Asparagus",
        "ingredients": "salmon fillet, asparagus, lemon, garlic, olive oil, dill, salt, pepper",
        "instructions": (
            "Preheat oven to 400F. Arrange salmon and trimmed asparagus on a sheet pan, "
            "drizzle with olive oil, minced garlic, salt, and pepper. Top salmon with lemon "
            "slices and fresh dill. Bake for 15-18 minutes until salmon flakes easily."
        ),
    },
    {
        "title": "Chickpea Curry (Chana Masala)",
        "ingredients": "chickpeas, onion, tomato, ginger, garlic, garam masala, cumin, coriander, cilantro",
        "instructions": (
            "Saute onion until golden, add ginger and garlic, then ground spices and cook "
            "until fragrant. Add chopped tomato and cook down into a thick sauce. Stir in "
            "chickpeas and simmer for 15 minutes, adding water as needed. Garnish with fresh "
            "cilantro and serve with rice or naan."
        ),
    },
]


def seed_demo_data(apps, schema_editor):
    from django.contrib.auth.hashers import make_password

    from apps.common.ai import get_embedding

    User = apps.get_model(settings.AUTH_USER_MODEL)
    Recipe = apps.get_model("recipes", "Recipe")

    user, created = User.objects.get_or_create(
        email=DEMO_EMAIL,
        defaults={
            "username": DEMO_EMAIL,
            "password": make_password(DEMO_PASSWORD),
            "first_name": "Demo",
            "last_name": "User",
            "is_active": True,
        },
    )

    for recipe_data in RECIPES:
        if Recipe.objects.filter(user=user, title=recipe_data["title"]).exists():
            continue
        source_text = (
            f"{recipe_data['title']}\n{recipe_data['ingredients']}\n{recipe_data['instructions']}"
        )
        Recipe.objects.create(
            user=user,
            title=recipe_data["title"],
            ingredients=recipe_data["ingredients"],
            instructions=recipe_data["instructions"],
            embedding=get_embedding(source_text),
        )


def unseed_demo_data(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    Recipe = apps.get_model("recipes", "Recipe")
    try:
        user = User.objects.get(email=DEMO_EMAIL)
    except User.DoesNotExist:
        return
    Recipe.objects.filter(user=user, title__in=[r["title"] for r in RECIPES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
