"""
Tests for ingredient APIs.
"""
import django
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

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
