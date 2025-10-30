from random import sample
from urllib.parse import unquote
from django.shortcuts import get_list_or_404, render
from django.views.generic import ListView
from django.db.models import Count
from images.models import Images, Users
from images.external_ops import get_images_external
from main.settings import env

MAX_USER_PER_PAGE = 4

def get_all_admin_images():
    admin_user = Users.objects.get(slug=env("ADMIN_ID"))
    root_images = get_images_external(admin_user)
    # images in ImageKit root folder
    root_names = list(map(lambda img: img.name, root_images))
    # images elsewhere, tracked in DB
    db_images = Images.objects.filter(uploader__slug=env("ADMIN_ID")).exclude(name__in=root_names)
    images = [*root_images, *db_images]
    images.sort(key=lambda i: i.created_at, reverse=True)
    return images

class HomePageView(ListView):
    model = Images
    ordering = "uploader_id"
    template_name = "home.html"

    def get_queryset(self):
        distinct_users = list(Users.objects.all().values_list("slug", flat=True).distinct())
        non_admin_users = Users.objects.exclude(slug=env("ADMIN_ID")).annotate(image_count=Count("images")).filter(image_count__gt=0)
        admin_images = get_all_admin_images()
        other_images = []

        if distinct_users.__len__() > MAX_USER_PER_PAGE:
            random_users = sample(list(non_admin_users), MAX_USER_PER_PAGE - 1)
            other_images = Images.objects.filter(uploader__slug__in=random_users).order_by("uploader__slug")
        else:
            other_images = Images.objects.exclude(uploader__slug=env("ADMIN_ID")).order_by("uploader__slug")
        
        return [*admin_images, *other_images]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["splatters"] = [1,2,3,4,5,6]
        return context

class UserPageView(ListView):
    model = Images
    ordering = "created_at"
    template_name = "user.html"

    def dispatch(self, request, *args, **kwargs):
        self.user_slug = unquote(kwargs["user_slug"])
        self.is_admin = kwargs["user_slug"] == env("ADMIN_ID")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.is_admin:
            return get_all_admin_images()

        else: 
            return get_list_or_404(Images, uploader__slug=self.user_slug)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["splatters"] = [1,2,3,4,5,6]
        context["userName"] = Users.objects.get(slug=self.user_slug).name
        return context
    
def NotFoundView(request, exception=None):
    return render(request=request, template_name="404.html", status=404)