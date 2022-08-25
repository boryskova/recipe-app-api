"""
Tests for tags APIs.
"""
from venv import create
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient
from rest_framework import status

from core.models import Tag

from recipe.serializers import TagSerializer


TAGS_URLS = reverse('recipe:tag-list')


def tag_details(tag_id):
    """Create and return a tag detail URL."""
    return reverse('recipe:tag-detail', args=[tag_id])


def create_user(email='user@example.com', password='test123'):
    """Create and return new user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITests(TestCase):
    """Tests unauthenticated API reuests."""
    
    def setUp(self):
        self.client = APIClient()

    def test_auth_is_required(self):
        """Test that auth is required to get tag list."""
        res = self.client.get(TAGS_URLS)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
    

class PrivatTagsAPITests(TestCase):
    """Tests for authenticated API reuests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        """Test retrieving tags list is successful."""
        Tag.objects.create(user=self.user, name='Oils')
        Tag.objects.create(user=self.user, name='Fruits')

        res = self.client.get(TAGS_URLS)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_tags_limited_to_user(self):
        """Test that retrieved tags are limited to authenticated user."""
        new_user = create_user(email='user2@example.com')
        Tag.objects.create(user=new_user, name='Meat')
        new_tag = Tag.objects.create(user=self.user, name='Veggies')

        res = self.client.get(TAGS_URLS)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], new_tag.name)
        self.assertEqual(res.data[0]['id'], new_tag.id)

    def test_update_tag(self):
        """Test updating the tag."""
        tag = Tag.objects.create(user=self.user, name='Tag name')

        payload = {'name': 'New tag name'}
        url = tag_details(tag.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag.refresh_from_db()
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        """Test deleting taf is successful."""
        tag = Tag.objects.create(user=self.user, name='Brakfest')

        url = tag_details(tag.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Tag.objects.filter(id=tag.id).exists())
