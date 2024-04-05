from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid

def index(request):
    activeListings = Listing.objects.filter(isActive=True)
    allcategories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": activeListings,
        "categories": allcategories
    })

def listing(request, id):
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "isListingInWatchlist": isListingInWatchlist,
        "allComments": allComments,
        "isOwner": isOwner
    })

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    listingData.isActive = False
    listingData.save()
    isOwner = request.user.username == listingData.owner.username
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    return render(request, "auctions/listing.html", {
        "listing": listingData,
        "message": "Congrats! Auction is closed successfully.",
        "update": True,
        "isListingInWatchlist": isListingInWatchlist,
        "allComments": allComments,
        "isOwner": isOwner
    })


def removeWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    user = request.user
    listingData.watchlist.remove(user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))


def addWatchlist(request, id):
    listingData = Listing.objects.get(pk=id)
    user = request.user
    listingData.watchlist.add(user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def watchlist(request, ):
    user = request.user
    listing = user.userWatchlist.all()
    return render(request, "auctions/watchlist.html", {
        "listings": listing
    })

def addBid(request, id):
    newBid = request.POST['newBid']
    listingData = Listing.objects.get(pk=id)
    isListingInWatchlist = request.user in listingData.watchlist.all()
    allComments = Comment.objects.filter(listing=listingData)
    isOwner = request.user.username == listingData.owner.username
    if float(newBid) > listingData.price.bid:
        updateBid = Bid(user=request.user, bid=float(newBid))
        updateBid.save()
        listingData.price = updateBid
        listingData.save() 
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "Bid is updated successfuly",
            "update": True,
            "isListingInWatchlist": isListingInWatchlist,
            "allComments": allComments,
            "isOwner": isOwner
        })
    else:
        return render(request, "auctions/listing.html", {
            "listing": listingData,
            "message": "failed to update bid",
            "update": False,
            "isListingInWatchlist": isListingInWatchlist,
            "allComments": allComments,
            "isOwner": isOwner
        })
    

def addComment(request, id):
    user = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST["newComment"]
    newComment = Comment(
        author=user,
        listing=listingData, 
        message=message
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def displayCategory(request, category):
    categoryData = Category.objects.get(categoryName=category)
    activeListings = Listing.objects.filter(isActive=True, category=categoryData)
    allcategories = Category.objects.all()
    return render(request, "auctions/displayCategory.html", {
        "activeListings": activeListings,
        "categories": allcategories
    })

def createListing(request):
    if request.method == "GET":
        allcategories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": allcategories
        })
    else:
        # Get the data from the form
        title = request.POST["title"]
        description = request.POST["description"]
        imageurl = request.POST["imageurl"]
        price = request.POST["price"]
        category = request.POST["category"]
        # Who is the user
        currentUser = request.user
        # Get the particular category
        categoryData = Category.objects.get(categoryName=category)
        #Create a bid object
        bid = Bid(bid=float(price), user=currentUser)
        bid.save()
        # Create a new listing object
        newListing = Listing(
            title=title,
            description=description,
            imageUrl=imageurl,
            price=bid,
            category=categoryData,
            owner=currentUser
        )
        # insert the object in our database
        newListing.save()
        # Redirect the user to the index page
        return HttpResponseRedirect(reverse(index))


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
