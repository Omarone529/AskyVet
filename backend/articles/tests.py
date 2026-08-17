from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.tests import make_user

from .models import Article, Category, Tag


class ArticleRoutingTests(APITestCase):
    """
    The admin routes used to be unreachable.

    ``<slug:slug>/`` was declared before ``drafts/``, so Django matched the
    literal segment against the detail view and answered 404.
    """

    def setUp(self):
        self.admin = make_user("redattore", is_admin=True)
        self.category = Category.objects.create(name="Cani")

    def test_admin_can_list_drafts(self):
        Article.objects.create(
            title="Bozza", body="...", author=self.admin, status=Article.Status.DRAFT
        )
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(reverse("article-drafts"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_regular_user_cannot_list_drafts(self):
        self.client.force_authenticate(user=make_user("lettore"))
        response = self.client.get(reverse("article-drafts"))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_an_article(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.post(
            reverse("article-list"),
            {
                "title": "Come curare il gatto",
                "body": "Testo dell'articolo.",
                "category_id": self.category.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        article = Article.objects.get(title="Come curare il gatto")
        self.assertEqual(article.author, self.admin)
        self.assertEqual(article.slug, "come-curare-il-gatto")

    def test_regular_user_cannot_create_an_article(self):
        self.client.force_authenticate(user=make_user("lettore"))

        response = self.client.post(
            reverse("article-list"), {"title": "Abusivo", "body": "..."}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Article.objects.filter(title="Abusivo").exists())

    def test_anonymous_cannot_create_an_article(self):
        response = self.client.post(
            reverse("article-list"), {"title": "Abusivo", "body": "..."}
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ArticleSlugTests(APITestCase):
    """Duplicate titles used to raise IntegrityError and return a 500."""

    def setUp(self):
        self.admin = make_user("redattore", is_admin=True)

    def test_two_articles_may_share_a_title(self):
        first = Article.objects.create(title="Vaccini", body="a", author=self.admin)
        second = Article.objects.create(title="Vaccini", body="b", author=self.admin)
        third = Article.objects.create(title="Vaccini", body="c", author=self.admin)

        self.assertEqual(first.slug, "vaccini")
        self.assertEqual(second.slug, "vaccini-2")
        self.assertEqual(third.slug, "vaccini-3")

    def test_categories_with_colliding_names_get_distinct_slugs(self):
        first = Category.objects.create(name="Gatti")
        second = Category.objects.create(name="Gatti!")

        self.assertNotEqual(first.slug, second.slug)

    def test_saving_an_article_twice_keeps_its_slug(self):
        article = Article.objects.create(title="Vaccini", body="a", author=self.admin)
        article.body = "aggiornato"
        article.save()

        self.assertEqual(article.slug, "vaccini")


class ArticleVisibilityTests(APITestCase):
    def setUp(self):
        self.admin = make_user("redattore", is_admin=True)
        self.published = Article.objects.create(
            title="Pubblicato",
            body="...",
            author=self.admin,
            status=Article.Status.PUBLISHED,
        )
        self.draft = Article.objects.create(
            title="Bozza", body="...", author=self.admin, status=Article.Status.DRAFT
        )

    def test_list_shows_only_published_articles_to_the_public(self):
        response = self.client.get(reverse("article-list"))

        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "Pubblicato")

    def test_public_cannot_read_a_draft_by_slug(self):
        response = self.client.get(reverse("article-detail", args=[self.draft.slug]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_read_a_draft_by_slug(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(reverse("article-detail", args=[self.draft.slug]))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_can_be_filtered_by_tag(self):
        tag = Tag.objects.create(name="Alimentazione")
        self.published.tags.add(tag)

        response = self.client.get(reverse("article-list"), {"tag": tag.slug})

        self.assertEqual(response.data["count"], 1)

    def test_results_are_paginated(self):
        response = self.client.get(reverse("article-list"))
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)


class ArticlePublishTests(APITestCase):
    def setUp(self):
        self.admin = make_user("redattore", is_admin=True)
        self.article = Article.objects.create(
            title="Bozza", body="...", author=self.admin, status=Article.Status.DRAFT
        )
        self.client.force_authenticate(user=self.admin)

    def test_publishing_stamps_published_at(self):
        response = self.client.patch(
            reverse("article-publish", args=[self.article.slug]), {"published": True}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.Status.PUBLISHED)
        self.assertIsNotNone(self.article.published_at)

    def test_publishing_twice_does_not_unpublish(self):
        url = reverse("article-publish", args=[self.article.slug])
        self.client.patch(url, {"published": True})
        self.client.patch(url, {"published": True})

        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.Status.PUBLISHED)

    def test_unpublishing_clears_published_at(self):
        url = reverse("article-publish", args=[self.article.slug])
        self.client.patch(url, {"published": True})
        self.client.patch(url, {"published": False})

        self.article.refresh_from_db()
        self.assertEqual(self.article.status, Article.Status.DRAFT)
        self.assertIsNone(self.article.published_at)

    def test_update_to_published_also_stamps_published_at(self):
        """
        Regression: only create() set published_at, so an article promoted
        through PATCH stayed with published_at = None.
        """
        response = self.client.patch(
            reverse("article-detail", args=[self.article.slug]),
            {"status": Article.Status.PUBLISHED},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertIsNotNone(self.article.published_at)

    def test_regular_user_cannot_publish(self):
        self.client.force_authenticate(user=make_user("lettore"))
        response = self.client.patch(
            reverse("article-publish", args=[self.article.slug]), {"published": True}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_an_article(self):
        response = self.client.delete(
            reverse("article-detail", args=[self.article.slug])
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(pk=self.article.pk).exists())

    def test_regular_user_cannot_delete_an_article(self):
        self.client.force_authenticate(user=make_user("lettore"))
        response = self.client.delete(
            reverse("article-detail", args=[self.article.slug])
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Article.objects.filter(pk=self.article.pk).exists())


class CategoryPermissionTests(APITestCase):
    def test_anyone_can_list_categories(self):
        Category.objects.create(name="Cani")
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_only_admin_creates_categories(self):
        self.client.force_authenticate(user=make_user("lettore"))
        response = self.client.post(reverse("category-list"), {"name": "Abusiva"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(Category.objects.filter(name="Abusiva").exists())

    def test_admin_creates_categories(self):
        self.client.force_authenticate(user=make_user("capo", is_admin=True))
        response = self.client.post(reverse("category-list"), {"name": "Rettili"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.get(name="Rettili").slug, "rettili")
