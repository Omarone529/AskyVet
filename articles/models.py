import uuid

from django.db import models
from django.utils.text import slugify

from users.models import User


class Category(models.Model):
    """Represents an article category."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorie"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        """Auto generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Represents a tag that can be applied to multiple articles."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)

    class Meta:
        verbose_name = "Tag"
        verbose_name_plural = "Tag"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Article(models.Model):
    """
    Represents a published or draft article on AskyVet.

    Articles can contain a cover image and rich text body with embedded images.
    Only admins can create, edit, and publish articles.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Bozza"
        PUBLISHED = "published", "Pubblicato"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, max_length=255)
    body = models.TextField()
    cover_image = models.ImageField(upload_to="articles/covers/", null=True, blank=True)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, related_name="articles"
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="articles")
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.DRAFT
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Articolo"
        verbose_name_plural = "Articoli"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
