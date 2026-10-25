import pytest

from apps.blogs.factories import (
    CategoryFactory,
    CommentFactory,
    PostFactory,
    TagFactory,
)


@pytest.mark.django_db
class TestCategoryModel:
    def test_create_category(self):
        category = CategoryFactory()

        assert category.name is not None
        assert category.slug is not None
        assert str(category) == category.name

    def test_category_string_representation(self):
        category = CategoryFactory(name="Technology")

        assert str(category) == "Technology"


@pytest.mark.django_db
class TestTagModel:
    def test_create_tag(self):
        tag = TagFactory()

        assert tag.name is not None
        assert tag.slug is not None
        assert str(tag) == tag.name

    def test_tag_string_representation(self):
        tag = TagFactory(name="python")

        assert str(tag) == "python"


@pytest.mark.django_db
class TestPostModel:
    def test_create_post(self):
        post = PostFactory()

        assert post.title is not None
        assert post.slug is not None
        assert post.author is not None
        assert post.category is not None
        assert post.status in ["draft", "published", "archived"]

    def test_post_string_representation(self):
        post = PostFactory(title="Test Post")

        assert str(post) == post.title

    def test_post_with_tags(self):
        post = PostFactory()
        tag1 = TagFactory()
        tag2 = TagFactory()
        post.tags.add(tag1, tag2)

        assert post.tags.count() == 2

    def test_post_mark_as_read(self):
        post = PostFactory()
        initial_views = post.view_count
        post.increment_view()

        assert post.view_count == initial_views + 1


@pytest.mark.django_db
class TestCommentModel:
    def test_create_comment(self):
        comment = CommentFactory()

        assert comment.content is not None
        assert comment.post is not None
        assert comment.author is not None
        assert comment.is_approved is not None

    def test_comment_string_representation(self):
        comment = CommentFactory(content="Great post!")

        assert str(comment) == f"{comment.author.email} - Great post!"

    def test_comment_approval(self):
        comment = CommentFactory(is_approved=False)
        comment.approve()

        assert comment.is_approved is True
