from random import sample
from django.shortcuts import get_list_or_404, render
from django.views.generic import ListView
from images.models import Images, Users

class HomePageView(ListView):
    model = Images
    ordering = "uploader_id"
    template_name = "home.html"

    def get_queryset(self):
        distinct_users = list(Users.objects.all().values_list("slug", flat=True).distinct())
        if distinct_users.__len__() > 4:
            random_users = sample(distinct_users, 4)
            return Images.objects.filter(uploader__slug__in=random_users).order_by("uploader__slug")
        else:
            return Images.objects.all().order_by("uploader__slug")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["splatters"] = [1,2,3,4,5,6]
        return context

class UserPageView(ListView):
    model = Images
    ordering = "created_at"
    template_name = "user.html"

    def get_queryset(self):
        return get_list_or_404(Images, uploader__slug=self.kwargs["userId"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["splatters"] = [1,2,3,4,5,6]
        context["userName"] = Users.objects.get(slug=self.kwargs["userId"]).name
        return context
    
def NotFoundView(request, exception=None):
    return render(request=request, template_name="404.html", status=404)