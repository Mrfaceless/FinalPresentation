from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from detector.models import MusicianProducer  # Assuming detector app holds the model

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # Load first_name/last_name from form

            # Create linked MusicianProducer
            MusicianProducer.objects.create(
                MusicianID=user,
                Name=f"{user.first_name} {user.last_name}",
                Email=user.email
            )

            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})
