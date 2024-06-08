from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import json
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .forms import UserSignInForm, UserSignUpForm
from profiles.forms import UpdatePersonalInformationForm
from profiles.models import Profile, PersonalInformation,  AddressInformation
from .data_validator import ValidateIdNumber

from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator

#  Create your views here.
# from django.core
# .mail import send_mail
# from django.conf import settings
# def send_welcome_email(user_email):
#     subject = 'Welcome to Our Website'
#     message = 'Thank you for signing up for our website. We are excited to have you!'
#     email_from = settings.DEFAULT_FROM_EMAIL
#     recipient_list = [user_email]
    
#     send_mail(subject, message, email_from, recipient_list)

@csrf_exempt
def sign_in(request):
	if request.user.is_authenticated:
		return JsonResponse({'message':f"Already logged in as {request.user.username}",'status':'warning'}, status=200)
	if request.method == "POST":
		try:
			json_data = json.loads(request.body)
		except Exception :
			return JsonResponse({'errors':'Supply a json oject: check documentation for more info ', 'status':'error'},status=400)
		email = json_data.get('email')
		password = json_data.get('password')
		data = {
			'email':email,
			'password': password
		}
		for key, value in data.items():
			if key == None or value == None:
				return JsonResponse({'errors': f'{key} field is required ', 'status':'error'}, status=404)
		form = UserSignInForm(data)
		if form.is_valid() :
			user = User.objects.get(email=email)
			print(user)
			print(password)
			print(user.password)
			user = authenticate(request, username=user.username, password=password)
			print(user)
			if user is not None:
				login(request, user)
				return JsonResponse({'message':f'Welcome back {user.username}', 'status':'success'}, status=200)
				#return JsonResponse({'message':f"Logged in as : {user.username} " , 'status':'success'}, status=200)
			else:
				return JsonResponse({'errors':{'password':['Password is incorrect']}, 'status':'error'}, status=400)
		else:
			return JsonResponse({'errors': form.errors, 'status':'error'}, status=400)
	else:
		return JsonResponse({'errors': 'Forbidden 403', 'status':'error'}, status=400)

@csrf_exempt
def render_auth_page(request):
	if request.user.is_authenticated:
		return redirect('home')
	return render(request, "auth.html")

@csrf_exempt
def sign_up(request):
	if request.user.is_authenticated:
		return redirect('home')
	if request.method == 'POST':
		try:
			json_data = json.loads(request.body)
		except Exception :
			return JsonResponse({'errors':'Supply a json oject: check documentation for more info ', 'status':'error'})
		print(json_data)
		data = {
		'username' : json_data.get('username'),
		# 'first_name' : json_data.get('first_name'),
		# 'last_name' : json_data.get('last_name'),
		# 'phone' : json_data.get('phone'),
		'email' : json_data.get('email'),
		'idnumber': json_data.get('idnumber'),
		'password' : json_data.get('password'),
		'password2' : json_data.get('password2'),
		}


		# address_data = {
		# 'street_address_line' : json_data.get('street_address_line'),
		# 'street_address_line1' : json_data.get('street_address_line1'),
		# 'city'  : json_data.get('city'),
		# 'province' : json_data.get('province'),
		# 'postal_code' : json_data.get('postal_code')
		# }

		for key, value in data.items():
			if key == None or value == None:
				return JsonResponse({'errors': {f"{key}":[f'{key} is required ']}, 'status':'error'}, status=404)
		form = UserSignUpForm(data)

		if form.is_valid() : 
			if data['password'] != data['password2']:
				return JsonResponse({'errors':{'password':['password no match ']}, 'status':'error'}, status=400)
			
			user = authenticate(request, email=data['email'], password=data['password'])
			if user is None:
				new_user = User.objects.create_user( email=data['email'], password=data['password'], username=data['username'])
				new_user.save()
				profile = Profile.objects.create(user=new_user, idnumber=data['idnumber'], age=ValidateIdNumber(data['idnumber']).get_age(), gender=ValidateIdNumber(data['idnumber']).get_gender() )
				profile.save()
				return JsonResponse({'message':f'User profile for {new_user.username} is created successfuly', 'status':'success'}, status=201)

		else:
			if form.errors:
				return JsonResponse({'errors': form.errors, 'status': 'error'}, status=403)
			elif personal_data_form.errors:
				return JsonResponse({'errors': personal_data_form.errors, 'status': 'error'}, status=403)
			# elif personal_data_form.errors:
			# 	return JsonResponse({'errors': personal_data_form.errors, 'status': 'error'}, status=403)
	else:
		return JsonResponse({'errors': 'Forbidden 403', 'status':'error'}, status=400)
		
	



@csrf_exempt
@login_required(login_url='render_auth_page')
def log_out(request):
	logout(request)
	return redirect('render_auth_page')


@csrf_exempt
def reset_password_link(request):
	if request.method == "POST":
		data = json.loads(request.body)
		email = data['email']
		try:
			user = User.objects.get(email=email)
		except Exception :
			user = False
		if user:
			token = default_token_generator.make_token(user)
			reset_link = f"http://127.0.0.1:8000/auth/reset_password/{user.id}/{token}/"
			
			return JsonResponse({"message":"link generated successfuly","link":reset_link, "status":"success"}, status=201)
		else:
			return JsonResponse({"errors":{"email":["Not Found"]}, "status":"error"}, status=404)
	else:
		return JsonResponse({'errors':"Forbidden 403" , "status":"error"}, status=403)

@csrf_exempt
def find_account(request):
	return render(request, 'reset_password.html')
@csrf_exempt
def reset_link(request):
	return render(request, 'reset_link.html')


@csrf_exempt
def reset_password(request, uidb64, token):
	try:
		uid = int(uidb64)
		user = User.objects.get(pk=uid)
	
	except(TypeError, ValueError, OverflowError, User.DoesNotExist):
		user = None

	if user is not None and default_token_generator.check_token(user, token):
		if request.method == 'POST':
			data = request.POST
			password = data['password']
			re_password = data['re-password']
			print(re_password)
			if password != re_password:
				return render(request, 'reset_password.html')
			else:	
				user.password = password
				user.save()
				return render(request,'complete_reset.html')
	return render(request, 'reset_password.html')