"""
Tests for ingredient APIs.
"""
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Ingredient,
    Recipe,
)

from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(ingredient_id):
    """Create and return a ingredient detail URL."""
    return reverse('recipe:ingredient-detail', args=[ingredient_id])

def create_user(email='user@example.com', password='test123'):
    """Create and return new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITests(TestCase):
    """Tests unauthenticated API reuests."""
    
    def setUp(self):
        self.client = APIClient()

    def test_auth_is_required(self):
        """Test that auth is required to get ingredient list."""
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivatsAPITests(TestCase):
    """Tests for authenticated API reuests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        """Test retrieving tags list is successful."""
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Vanilla')

        res = self.client.get(INGREDIENTS_URL)

        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_ingredients_limited_to_user(self):
        """Test that retrieved ingredients are limited to authenticated user."""
        new_user = create_user(email='user2@example.com')
        Ingredient.objects.create(user=new_user, name='Sault')
        new_ingredient = Ingredient.objects.create(user=self.user, name='Pepper')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], new_ingredient.name)
        self.assertEqual(res.data[0]['id'], new_ingredient.id)

    def test_update_ingredient(self):
        """Test updating the ingredient."""
        ingredient = Ingredient.objects.create(user=self.user, name='Coriander')

        payload = {'name': 'Coriander new'}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload['name'])

    def test_delete_ingredient(self):
        """Test deleting ingredient is successful."""
        ingredient = Ingredient.objects.create(user=self.user, name='Cinnamon')

        url = detail_url(ingredient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingredients = Ingredient.objects.filter(id=ingredient.id)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        """Test listing ingredients by those assigned to recipes."""
        ing1 = Ingredient.objects.create(user=self.user, name='Eggs')
        ing2 = Ingredient.objects.create(user=self.user, name='Lemon')
        recipe = Recipe.objects.create(
            user=self.user,
            title='Lemonade',
            time_minutes=20,
            price=Decimal('0.50'),
        )
        recipe.ingredients.add(ing1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(ing1)
        s2 = IngredientSerializer(ing2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        """Test filtered ingredients return a unique list."""
        ing = Ingredient.objects.create(user=self.user, name='Potato')
        Ingredient.objects.create(user=self.user, name='Murshmallow')
        recipe1 = Recipe.objects.create(
            user=self.user,
            title='Mashed potatoes',
            time_minutes=30,
            price=Decimal('10.00'),
        )
        recipe2 = Recipe.objects.create(
            user=self.user,
            title='French fri',
            time_minutes=40,
            price=Decimal('13.50'),
        )
        recipe1.ingredients.add(ing)
        recipe2.ingredients.add(ing)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
