from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
from .restapis import get_dealer_by_id, get_dealers_from_cf, get_dealers_by_state, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Getting an instance of a logger
logger = logging.getLogger(__name__)

def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://9bebcb01.eu-de.apigw.appdomain.cloud/api/dealership"
        context["dealerships"] = get_dealers_from_cf(url)
        return render(request, 'djangoapp/index.html', context)

def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)

def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/contact.html', context)

def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'djangoapp/login.html', context)
    else:
        return render(request, 'djangoapp/login.html', context)

def logout_request(request):
    print("Logging out `{}`...".format(request.user.username))
    logout(request)
    return redirect('djangoapp:index')

def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.debug("{} is new user".format(username))
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("/djangoapp/")
        else:
            return render(request, 'djangoapp/registration.html', context)

def get_dealer_details(request, dealer_id):
    context = {}
    if request.method == "GET":
        url = 'https://9bebcb01.eu-de.apigw.appdomain.cloud/api/review'
        reviews = get_dealer_reviews_from_cf(url, dealer_id=dealer_id)
        context = {
            "reviews":  reviews, 
            "dealer_id": dealer_id
        }

        return render(request, 'djangoapp/dealer_details.html', context)

def add_review(request, dealer_id):
    if request.user.is_authenticated:
        if request.method == "GET":
            url = f"https://5b93346d.us-south.apigw.appdomain.cloud/dealerships/dealer-get?dealerId={dealer_id}"
            context = {
                "cars": CarModel.objects.all(),
                "dealer": get_dealer_by_id(url, dealer_id=dealer_id),
            }
            return render(request, 'djangoapp/add_review.html', context)

        if request.method == "POST":
            form = request.POST
            review = dict()
            review["name"] = f"{request.user.first_name} {request.user.last_name}"
            review["dealership"] = dealer_id
            review["review"] = form["content"]
            review["purchase"] = form.get("purchasecheck")
            if review["purchase"]:
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            car = CarModel.objects.get(pk=form["car"])
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.year
            
            if form.get("purchasecheck"):
                review["purchase_date"] = datetime.strptime(form.get("purchasedate"), "%m/%d/%Y").isoformat()
            else: 
                review["purchase_date"] = None

            url = "https://9bebcb01.eu-de.apigw.appdomain.cloud/api/review"
            json_payload = {"review": review}

            result = post_request(url, json_payload, dealerId=dealer_id)
            if int(result.status_code) == 200:
                print("Review posted successfully.")

            return redirect("djangoapp:dealer_details", dealer_id=dealer_id)

    else:
        print("User must be authenticated before posting a review. Please log in.")
        return redirect("/djangoapp/login")