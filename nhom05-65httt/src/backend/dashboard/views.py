from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


def home_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, "dashboard/dashboard.html", {"active_menu": "dashboard"})


@login_required
def learning(request):
    return render(request, "dashboard/empty_page.html", {
        "active_menu": "learning",
        "page_title": "Quản lý và phân tích học tập",
        "page_icon": "fa-solid fa-graduation-cap",
    })


@login_required
def quality(request):
    return render(request, "dashboard/empty_page.html", {
        "active_menu": "quality",
        "page_title": "Phân tích chất lượng đào tạo",
        "page_icon": "fa-solid fa-chart-pie",
    })


@login_required
def careers(request):
    return render(request, "dashboard/empty_page.html", {
        "active_menu": "careers",
        "page_title": "Phân tích xu hướng ngành nghề",
        "page_icon": "fa-solid fa-building-columns",
    })


@login_required
def skill_gap(request):
    return render(request, "dashboard/empty_page.html", {
        "active_menu": "skill_gap",
        "page_title": "Phân tích Skill Gap",
        "page_icon": "fa-solid fa-sliders",
    })


@login_required
def recommendations(request):
    return render(request, "dashboard/empty_page.html", {
        "active_menu": "recommendations",
        "page_title": "Đề xuất chương trình đào tạo",
        "page_icon": "fa-solid fa-lightbulb",
    })
