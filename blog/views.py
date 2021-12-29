from django.shortcuts import render
from blog.models import Comment, Post, Tag, User
from django.db.models import Count
from django.db.models.query import Prefetch
from django.shortcuts import get_object_or_404
from django.http import Http404


def get_related_posts_count(tag):
    return tag.posts.count()


def serialize_post(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments__count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts__count
    }


def index(request):
    most_popular_posts = Post.objects.popular().prefetch_related(
        'author',
        Prefetch('tags', queryset=Tag.objects.annotate(Count('posts')))
        ).fetch_with_comments_count()
    most_fresh_posts = Post.objects.annotate(
        Count('comments')).order_by('-published_at')[:5].prefetch_related(
            'author',
            Prefetch('tags', queryset=Tag.objects.annotate(Count('posts')))
        )
    most_popular_tags = Tag.objects.popular()

    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    try:
        post = Post.objects.select_related('author').get(slug=slug)
    except Post.DoesNotExist:
        raise Http404("post does not exist")

    comments = Comment.objects.select_related('author').filter(post=post)
    serialized_comments = []
    likes = post.likes.all()
    related_tags = (
        Tag.objects.filter(posts__slug=slug).annotate(Count('posts'))
    )
    most_popular_tags = Tag.objects.popular()
    most_popular_posts = Post.objects.popular().prefetch_related(
        'author',
        Prefetch('tags', queryset=Tag.objects.annotate(Count('posts')))
    ).fetch_with_comments_count()

    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })
    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': likes.count(),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }
    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = get_object_or_404(Tag, title=tag_title)
    most_popular_tags = Tag.objects.popular()
    most_popular_posts = Post.objects.popular().prefetch_related(
            'author',
            Prefetch('tags', queryset=Tag.objects.annotate(Count('posts')))
        ).fetch_with_comments_count()
    related_posts = (
        Tag.objects.filter(posts__title=tag_title).annotate(Count('posts'))
    )

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
