from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from articles.models import Article
from users.tests import make_user

from .models import ForumCategory, PinnedPost, Post, Reply, Thread


class ThreadCreationTests(APITestCase):
    def setUp(self):
        self.user = make_user("mario")
        self.category = ForumCategory.objects.create(name="Generale")

    def test_authenticated_user_opens_a_thread_with_its_first_post(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("thread-list"),
            {
                "title": "Il mio cane non mangia",
                "content": "Da due giorni rifiuta il cibo.",
                "category_id": self.category.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        thread = Thread.objects.get(title="Il mio cane non mangia")
        self.assertEqual(thread.author, self.user)
        self.assertEqual(thread.posts.count(), 1)
        self.assertEqual(thread.posts.first().content, "Da due giorni rifiuta il cibo.")

    def test_anonymous_cannot_open_a_thread(self):
        response = self.client.post(
            reverse("thread-list"), {"title": "Abusivo", "content": "..."}
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(Thread.objects.exists())

    def test_threads_may_share_a_title(self):
        """Regression: duplicate titles collided on the unique slug."""
        first = Thread.objects.create(title="Aiuto", author=self.user)
        second = Thread.objects.create(title="Aiuto", author=self.user)

        self.assertEqual(first.slug, "aiuto")
        self.assertEqual(second.slug, "aiuto-2")

    def test_thread_can_quote_a_published_article(self):
        article = Article.objects.create(
            title="Alimentazione del cane",
            body="...",
            author=self.user,
            status=Article.Status.PUBLISHED,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("thread-list"),
            {
                "title": "Ne discutiamo",
                "content": "Che ne pensate?",
                "article_id": str(article.id),
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Thread.objects.get(title="Ne discutiamo").article, article)

    def test_thread_cannot_quote_a_draft(self):
        draft = Article.objects.create(
            title="Non pronto",
            body="...",
            author=self.user,
            status=Article.Status.DRAFT,
        )
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("thread-list"),
            {"title": "x", "content": "y", "article_id": str(draft.id)},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_article_detail_links_back_to_its_discussion(self):
        article = Article.objects.create(
            title="Alimentazione",
            body="...",
            author=self.user,
            status=Article.Status.PUBLISHED,
        )
        thread = Thread.objects.create(
            title="Discussione", author=self.user, article=article
        )

        response = self.client.get(reverse("article-detail", args=[article.slug]))

        self.assertEqual(response.data["discussion"]["slug"], thread.slug)

    def test_article_without_discussion_reports_none(self):
        article = Article.objects.create(
            title="Solitario",
            body="...",
            author=self.user,
            status=Article.Status.PUBLISHED,
        )

        response = self.client.get(reverse("article-detail", args=[article.slug]))

        self.assertIsNone(response.data["discussion"])


class PostPinPermissionTests(APITestCase):
    """
    The pin endpoint used to enforce nothing at all.

    IsThreadAuthorOrAdmin only implemented has_object_permission, which a plain
    APIView never calls, so has_permission defaulted to True and anonymous
    callers got a 200.
    """

    def setUp(self):
        self.owner = make_user("proprietario")
        self.stranger = make_user("estraneo")
        self.admin = make_user("capo", is_admin=True)
        self.thread = Thread.objects.create(title="Discussione", author=self.owner)
        self.post = Post.objects.create(
            thread=self.thread, author=self.owner, content="ciao"
        )
        self.url = reverse("post-pin", args=[self.post.id])

    def test_anonymous_cannot_pin(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(PinnedPost.objects.exists())

    def test_unrelated_user_cannot_pin(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(PinnedPost.objects.exists())

    def test_thread_author_can_pin(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PinnedPost.objects.filter(post=self.post).exists())

    def test_admin_can_pin(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(PinnedPost.objects.filter(post=self.post).exists())

    def test_pinning_twice_unpins(self):
        self.client.force_authenticate(user=self.owner)
        self.client.post(self.url)
        response = self.client.post(self.url)

        self.assertFalse(response.data["pinned"])
        self.assertFalse(PinnedPost.objects.exists())

    def test_pinned_entry_takes_its_thread_from_the_post(self):
        other_thread = Thread.objects.create(title="Altro", author=self.owner)
        entry = PinnedPost.objects.create(post=self.post, thread=other_thread)

        entry.refresh_from_db()
        self.assertEqual(entry.thread, self.thread)


class PostOwnershipTests(APITestCase):
    """An author must be able to edit and delete their own contributions."""

    def setUp(self):
        self.author = make_user("autore")
        self.stranger = make_user("estraneo")
        self.admin = make_user("capo", is_admin=True)
        self.thread = Thread.objects.create(title="Discussione", author=self.author)
        self.post = Post.objects.create(
            thread=self.thread, author=self.author, content="testo originale"
        )
        self.url = reverse("post-detail", args=[self.post.id])

    def test_author_can_edit_own_post(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.patch(self.url, {"content": "testo corretto"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "testo corretto")

    def test_stranger_cannot_edit_someone_elses_post(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.patch(self.url, {"content": "vandalismo"})

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.post.refresh_from_db()
        self.assertEqual(self.post.content, "testo originale")

    def test_author_can_delete_own_post(self):
        self.client.force_authenticate(user=self.author)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.post.pk).exists())

    def test_admin_can_delete_any_post(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_stranger_cannot_delete_someone_elses_post(self):
        self.client.force_authenticate(user=self.stranger)
        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Post.objects.filter(pk=self.post.pk).exists())

    def test_anonymous_read_of_a_post_does_not_crash(self):
        """Regression: permissions read AnonymousUser.is_admin and raised 500."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LikeTests(APITestCase):
    def setUp(self):
        self.user = make_user("mario")
        self.thread = Thread.objects.create(title="Discussione", author=self.user)
        self.post = Post.objects.create(
            thread=self.thread, author=self.user, content="ciao"
        )
        self.reply = Reply.objects.create(
            post=self.post, author=self.user, content="risposta"
        )

    def test_like_and_unlike_a_post(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("post-like", args=[self.post.id])

        first = self.client.post(url)
        self.assertTrue(first.data["liked"])
        self.assertEqual(first.data["likes_count"], 1)

        second = self.client.post(url)
        self.assertFalse(second.data["liked"])
        self.assertEqual(second.data["likes_count"], 0)

    def test_anonymous_cannot_like(self):
        response = self.client.post(reverse("post-like", args=[self.post.id]))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_like_and_unlike_a_reply(self):
        self.client.force_authenticate(user=self.user)
        url = reverse("reply-like", args=[self.reply.id])

        self.assertTrue(self.client.post(url).data["liked"])
        self.assertFalse(self.client.post(url).data["liked"])

    def test_thread_detail_reports_like_state(self):
        self.post.likes.add(self.user)
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("thread-detail", args=[self.thread.slug]))

        post = response.data["posts"][0]
        self.assertEqual(post["likes_count"], 1)
        self.assertTrue(post["is_liked"])

    def test_thread_detail_hides_like_state_from_anonymous(self):
        self.post.likes.add(self.user)

        response = self.client.get(reverse("thread-detail", args=[self.thread.slug]))

        self.assertFalse(response.data["posts"][0]["is_liked"])


class ClosedThreadTests(APITestCase):
    def setUp(self):
        self.user = make_user("mario")
        self.admin = make_user("capo", is_admin=True)
        self.thread = Thread.objects.create(
            title="Chiusa", author=self.user, is_closed=True
        )
        self.post = Post.objects.create(
            thread=self.thread, author=self.user, content="ciao"
        )

    def test_cannot_post_on_a_closed_thread(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("post-list", args=[self.thread.slug]), {"content": "nuovo"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(self.thread.posts.count(), 1)

    def test_cannot_reply_on_a_closed_thread(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            reverse("reply-list", args=[self.post.id]), {"content": "nuova"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_reopens_a_thread(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(
            reverse("thread-close", args=[self.thread.slug]), {"closed": False}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.thread.refresh_from_db()
        self.assertFalse(self.thread.is_closed)

    def test_regular_user_cannot_close_a_thread(self):
        open_thread = Thread.objects.create(title="Aperta", author=self.user)
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse("thread-close", args=[open_thread.slug]), {"closed": True}
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MutedUserTests(APITestCase):
    """A mute blocks publishing but leaves reading and liking alone."""

    def setUp(self):
        self.muted = make_user("silenziato")
        self.muted.muted_until = timezone.now() + timezone.timedelta(hours=6)
        self.muted.save(update_fields=["muted_until"])

        self.thread = Thread.objects.create(title="Discussione", author=self.muted)
        self.post = Post.objects.create(
            thread=self.thread, author=self.muted, content="vecchio"
        )
        self.client.force_authenticate(user=self.muted)

    def test_muted_user_cannot_open_a_thread(self):
        response = self.client.post(
            reverse("thread-list"), {"title": "Nuovo", "content": "..."}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_muted_user_cannot_post(self):
        response = self.client.post(
            reverse("post-list", args=[self.thread.slug]), {"content": "nuovo"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_muted_user_cannot_reply(self):
        response = self.client.post(
            reverse("reply-list", args=[self.post.id]), {"content": "nuova"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_muted_user_can_still_read(self):
        response = self.client.get(reverse("thread-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_muted_user_can_still_like(self):
        response = self.client.post(reverse("post-like", args=[self.post.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_with_expired_mute_can_post_again(self):
        self.muted.muted_until = timezone.now() - timezone.timedelta(hours=1)
        self.muted.save(update_fields=["muted_until"])

        response = self.client.post(
            reverse("post-list", args=[self.thread.slug]), {"content": "di nuovo"}
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class ThreadListingTests(APITestCase):
    def setUp(self):
        self.user = make_user("mario")

    def test_list_reports_post_count_and_last_activity(self):
        thread = Thread.objects.create(title="Discussione", author=self.user)
        Post.objects.create(thread=thread, author=self.user, content="primo")
        Post.objects.create(thread=thread, author=self.user, content="secondo")

        response = self.client.get(reverse("thread-list"))
        result = response.data["results"][0]

        self.assertEqual(result["posts_count"], 2)
        self.assertEqual(result["last_post"]["author"], self.user.username)

    def test_list_of_a_thread_without_posts_has_no_last_post(self):
        Thread.objects.create(title="Vuota", author=self.user)

        response = self.client.get(reverse("thread-list"))

        self.assertIsNone(response.data["results"][0]["last_post"])

    def test_thread_list_stays_at_a_constant_query_count(self):
        """
        Guards the N+1 fix: adding threads must not add queries.

        posts_count and last_post are resolved with a Count and two Subqueries
        rather than by walking the relation in Python.
        """
        for index in range(3):
            thread = Thread.objects.create(title=f"Thread {index}", author=self.user)
            Post.objects.create(thread=thread, author=self.user, content="x")

        with self.assertNumQueries(2):  # COUNT for pagination + the page itself
            self.client.get(reverse("thread-list"))

        for index in range(3, 10):
            thread = Thread.objects.create(title=f"Thread {index}", author=self.user)
            Post.objects.create(thread=thread, author=self.user, content="x")

        with self.assertNumQueries(2):
            self.client.get(reverse("thread-list"))

    def test_viewing_a_thread_increments_and_returns_the_view_count(self):
        thread = Thread.objects.create(title="Discussione", author=self.user)

        response = self.client.get(reverse("thread-detail", args=[thread.slug]))

        self.assertEqual(response.data["views"], 1)
        thread.refresh_from_db()
        self.assertEqual(thread.views, 1)
