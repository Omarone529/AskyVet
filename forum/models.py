from django.db import models
from django.utils.text import slugify

from users.models import User


class ForumCategory(models.Model):
    """Categories for organizing forum threads."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Categoria Forum"
        verbose_name_plural = "Categorie Forum"
        ordering = ["order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Thread(models.Model):
    """Forum thread started by a user."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True, max_length=200)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="threads")
    category = models.ForeignKey(
        ForumCategory, on_delete=models.SET_NULL, null=True, related_name="threads"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Thread"
        verbose_name_plural = "Thread"
        ordering = ["-is_pinned", "-updated_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class Post(models.Model):
    """Individual reply inside a thread."""

    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="posts")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    likes = models.ManyToManyField(User, related_name="liked_posts", blank=True)

    class Meta:
        verbose_name = "Post"
        verbose_name_plural = "Post"
        ordering = ["created_at"]

    def __str__(self):
        return f"Post by {self.author.username} on {self.thread.title}"


class Reply(models.Model):
    """A reply to a post inside a thread. One level deep only."""

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="replies")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="replies")
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name="liked_replies", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Risposta"
        verbose_name_plural = "Risposte"
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author.username} on post {self.post.id}"


class PinnedPost(models.Model):
    """Represents a post pinned by the thread author inside a thread."""

    post = models.OneToOneField(
        Post, on_delete=models.CASCADE, related_name="pinned_entry"
    )
    thread = models.ForeignKey(
        Thread, on_delete=models.CASCADE, related_name="pinned_posts"
    )
    pinned_at = models.DateTimeField(auto_now_add=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Post Pinnato"
        verbose_name_plural = "Post Pinnati"
        ordering = ["order", "pinned_at"]
        unique_together = ["post", "thread"]

    def __str__(self):
        return f"Pinned post {self.post.id} in thread {self.thread.id}"
