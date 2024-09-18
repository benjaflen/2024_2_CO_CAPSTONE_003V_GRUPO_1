from django.shortcuts import render , redirect , get_object_or_404

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from app.forms import CustomUserCreationForm
from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.
def home (request):
   
    return render(request, 'app/home.html')



def registroConductor(request):
    data = {
        'form': CustomUserCreationForm()
    }
    
    if request.method == 'POST':
        formulario = CustomUserCreationForm(data=request.POST)
        if formulario.is_valid():
            user = formulario.save(commit=False)
            user.is_conductor = True  # Establecer que el usuario es un conductor
            user.save()
            login(request, user)
            messages.success(request, "Registro Exitoso como Conductor")
            return redirect('home_conductor')  # Redirigir a la página del conductor
        data["form"] = formulario
            
    return render(request, 'registration/registro_conductor.html', data)



def registroApoderado(request):
    data = {
        'form': CustomUserCreationForm()
    }
    
    if request.method == 'POST':
        formulario = CustomUserCreationForm(data=request.POST)
        if formulario.is_valid():
            user = formulario.save(commit=False)
            user.is_apoderado = True  # Establecer que el usuario es un apoderado
            user.save()
            login(request, user)
            messages.success(request, "Registro Exitoso como Apoderado")
            return redirect('home_apoderado')  # Redirigir a la página del apoderado
        data["form"] = formulario
            
    return render(request, 'registration/registro_apoderado.html', data)
def home_apoderado(request):
    return render(request, 'apoderado/home_apoderado.html')


def home_conductor(request):
    #
    return render(request, 'conductor/home_conductor.html')

def login_apoderado(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Autentica al usuario e inicia sesión
            user = form.get_user()
            login(request, user)

            # Verificar si el usuario es apoderado o conductor
            if user.is_apoderado:
                return redirect('home_apoderado')  # Redirigir al home de apoderado
            elif user.is_conductor:
                return redirect('home_conductor')  # Redirigir al home de conductor
            else:
                return redirect('home')  # Redirigir al home general si no es ninguno
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login_apoderado.html', {'form': form})




def login_conductor(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            # Autentica al usuario e inicia sesión
            user = form.get_user()
            login(request, user)

            # Verificar si el usuario es apoderado o conductor
            if user.is_apoderado:
                return redirect('home_apoderado')  # Redirigir al home de apoderado
            elif user.is_conductor:
                return redirect('home_conductor')  # Redirigir al home de conductor
            else:
                return redirect('home')  # Redirigir al home general si no es ninguno
    else:
        form = AuthenticationForm()
    
    return render(request, 'registration/login_conductor.html', {'form': form})



# Vistas  menú lateral apoderado
@login_required
def seguimiento(request):
    return render(request, 'apoderado/seguimiento.html')

@login_required
def historial(request):
    return render(request, 'apoderado/historial.html')

@login_required
def configuracion(request):
    return render(request, 'apoderado/configuracion.html')

@login_required
def conductor(request):
    return render(request, 'apoderado/conductor.html')



# Vistas  del menú lateral conductor
@login_required
def informacionPersonal(request):
    return render(request, 'conductor/informacionPersonal.html')

@login_required
def informacionVehiculo(request):
    return render(request, 'conductor/informacionVehiculo.html')

@login_required
def ingresaRuta(request):
    return render(request, 'conductor/ingresaRuta.html')

@login_required
def apoderado(request):
    return render(request, 'conductor/apoderado.html')



@login_required
def alumnos(request):
    return render(request, 'conductor/alumnos.html')