from django.shortcuts import render_to_response, get_object_or_404
from blog.models import *
from django.views.generic import ListView, DetailView, View
from blog.forms import *
from django.views import View
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.contrib import auth
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.template.context_processors import csrf
from django.db.models import F
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from .forms import SignupForm
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .token import account_activation_token
from django.core.mail import EmailMessage
from django.core.validators import FileExtensionValidator
from rest_framework import generics
from .serializers import PostSerializer


def handle_page_not_found_404(request):
    return redirect('/')


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your blog account.'
            message = render_to_string('registration/acc_activate_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                mail_subject, message, to=[to_email]
            )
            email.send()
            return render(request, 'registration/confirmation.html', {'form': form})
    else:
        form = SignupForm()
    return render(request, 'registration/signup.html', {'form': form})


class PostsView(ListView):
    template_name = 'blog/post_list.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super(PostsView, self).get_context_data(**kwargs)
        context['posts'] = Post.objects.all().order_by('-rating')

        context['posts'] = sorted(list(context['posts']),
                                  key=lambda x: -(
                                          x.rating * (1 / (timezone.now() - x.published_date).total_seconds())))

        user = auth.get_user(self.request)
        if user.is_authenticated:
            context['form'] = NewPost
        return context


class ArticleDetailView(DetailView):
    model = Post
    comment_form = CommentForm
    like = LikeDislike

    def get_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = Comments.objects.filter(post=self.object)
        try:
            like = LikeDislike.objects.filter(post=self.object, user=self.request.user)
            context['like'] = like[0].vote if like else 0
        except TypeError:
            context['like'] = 0

        return context

    def get(self, request, *args, **kwargs):
        user = auth.get_user(request)
        self.object = self.get_object()
        context = self.get_data(object=self.object)
        context.update(csrf(request))
        if user.is_authenticated:
            context['form'] = self.comment_form
        return self.render_to_response(context)


@login_required
@require_http_methods(["POST"])
def add_comment(request, pk):
    form = CommentForm(request.POST, request.FILES)
    post = get_object_or_404(Post, id=pk)

    if form.is_valid():
        comment = Comments()
        comment.post = post
        comment.author = auth.get_user(request)
        comment.text = form.cleaned_data['text']
        comment.published_date = timezone.now()
        comment.picture = form.cleaned_data['picture']
        comment.save()

    return redirect(post.get_absolute_url())


@login_required
@require_http_methods(["POST"])
def add_post(request):
    form = NewPost(request.POST, request.FILES)

    if form.is_valid():
        post = Post()
        post.author = auth.get_user(request)
        post.title = form.cleaned_data['title']
        post.text = form.cleaned_data['text']
        post.published_date = timezone.now()
        post.picture = form.cleaned_data['picture']
        post.save()

    return redirect('/')


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        # return redirect('home')
        return render(request, 'registration/activate.html')
    else:
        return HttpResponse('Activation link is invalid!')


@login_required
def update_profile(request):
    args = {}

    if request.method == 'POST':
        form = UpdateProfile(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('/')
    else:
        form = UpdateProfile(initial={'username': request.user.username, 'email': request.user.email})

    args['form'] = form
    return render(request, 'registration/email_change.html', args)


@login_required
def add_like(request, pk):
    likes = LikeDislike.objects.filter(user=request.user, post=pk)
    post = get_object_or_404(Post, id=pk)

    if not likes:
        LikeDislike.objects.create(user=request.user, post=post, vote=1)
        rate = Post.objects.get(pk=pk)
        rate.rating = F('rating') + 1
        rate.save()

    return redirect(post.get_absolute_url())


@login_required
def add_dislike(request, pk):
    likes = LikeDislike.objects.filter(user=request.user, post=pk)
    post = get_object_or_404(Post, id=pk)

    if not likes:
        LikeDislike.objects.create(user=request.user, post=post, vote=-1)
        rate = Post.objects.get(pk=pk)
        rate.rating = F('rating') - 1
        rate.save()

    return redirect(post.get_absolute_url())


class ListPostView(generics.ListAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
