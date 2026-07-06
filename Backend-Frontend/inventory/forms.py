from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import Products, Ingredients, Branches, UnitMeasures, UserProfile    

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control rounded-pill border-0 shadow-sm',
        'placeholder': 'Usuario'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control rounded-pill border-0 shadow-sm',
        'placeholder': 'Contraseña'
    }))
    
class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = ['name', 'sale_price', 'production_cost', 'is_active', 'description', 'image_path']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre del plato o bebida'
            }),
            'sale_price': forms.TextInput(attrs={
                'class': 'form-control currency-input', 
                'placeholder': '0',
                'autocomplete': 'off'
            }),
            'production_cost': forms.TextInput(attrs={
                'class': 'form-control currency-input', 
                'placeholder': '0',
                'autocomplete': 'off'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Descripción breve...'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'image_path': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        
class IngredientForm(forms.ModelForm):
    class Meta:
        model = Ingredients
        fields = ['name', 'unit_measure', 'min_stock_threshold', 'category']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Soda, Tequila, Limón'
            }),
            'unit_measure': forms.Select(attrs={'class': 'form-control'}),
            'min_stock_threshold': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control',
            }),
        }
        
class BranchForm(forms.ModelForm):
    class Meta:
        model = Branches
        fields = ['name', 'address', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Sede Norte'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: Calle 100 #15-20'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ej: +57 300... El teléfono'
            }),
        }
        
class UserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=UserProfile.ROLES, 
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    branch = forms.ModelChoiceField(
        queryset=Branches.objects.all(), 
        required=False, 
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Sede Asignada"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Contraseña",
        required=False # <--- CAMBIA ESTO A FALSE
    )

    class Meta:
        model = User # Cambiamos UserProfile por User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        
