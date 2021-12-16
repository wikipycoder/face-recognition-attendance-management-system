from django.shortcuts import render, redirect
from django.http import HttpResponse, StreamingHttpResponse
from django.core.mail import BadHeaderError, send_mass_mail
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import Student, Attendence
from .filters import AttendenceFilter

# from django.views.decorators import gzip

from .recognizer import Recognizer
from datetime import date




@login_required(login_url = 'login')
def home(request):
    studentForm = CreateStudentForm()

    if request.method == 'POST':
        studentForm = CreateStudentForm(request.POST, files=request.FILES)
        # print(request.POST)
        stat = False 
        try:
            student = Student.objects.get(registration_id = request.POST['registration_id'])
            stat = True
        except:
            stat = False
        if studentForm.is_valid() and (stat == False):
            studentForm.save()
            name = studentForm.cleaned_data.get('firstname') +" " +studentForm.cleaned_data.get('lastname')
            messages.success(request, 'Student ' + name + ' was successfully added.')
            return redirect('home')
        else:
            messages.error(request, 'Student with Registration Id '+request.POST['registration_id']+' already exists.')
            return redirect('home')

    context = {'studentForm':studentForm}
    return render(request, 'attendence_sys/home.html', context)


def loginPage(request):

    if request.session.get("user", None):
        return redirect("home")
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username = username, password = password)

        if user is not None:
            login(request, user)
            request.session["user"] = True
            return redirect('home')
        else:
            messages.info(request, 'Username or Password is incorrect')

    context = {}
    return render(request, 'attendence_sys/login.html', context)

@login_required(login_url = 'login')
def logoutUser(request):

    logout(request)
    return redirect('login')

@login_required(login_url = 'login')
def updateStudentRedirect(request):

    context = {}
    if request.method == 'GET':
        try:
            student = Student.objects.get(id=request.session.get("update_student_id", None))
            reg_id = student.registration_id
            updateStudentForm = CreateStudentForm(instance=student)
        except:
            messages.error(request, 'Student Not Found')
            return redirect('home')
        
        context = {'form':updateStudentForm, 'prev_reg_id':reg_id, 'student':student}
        return render(request, 'attendence_sys/student_update.html', context)

    if request.method == 'POST':
        try:
            reg_id = request.POST['reg_id']
            branch = request.POST['branch']
            student = Student.objects.get(registration_id = reg_id, branch = branch)
            updateStudentForm = CreateStudentForm(instance=student)
            request.session["update_student_id"] = student.id

            context = {'form':updateStudentForm, 'prev_reg_id':reg_id, 'student':student}
        except:
            messages.error(request, 'Student Not Found')
            return redirect('home')
    return render(request, 'attendence_sys/student_update.html', context)

@login_required(login_url = 'login')
def updateStudent(request):

    if request.method == 'GET':
        return redirect("home")    

    if request.method == 'POST':
        context = {}
        try:
            student = Student.objects.get(registration_id = request.POST['prev_reg_id'])
            updateStudentForm = CreateStudentForm(data=request.POST, files=request.FILES, instance=student)

            if updateStudentForm.is_valid():
                updateStudentForm.save()
                messages.success(request, 'Updation Success')
                HttpResponse("should print this")
                return redirect('home')
        except:
            messages.error(request, 'Updation Unsucessfull')
            return redirect('home')
    return render(request, 'attendence_sys/student_update.html', context)


@login_required(login_url = 'login')
def takeAttendence(request):

    if request.method == 'GET':
        return redirect("home")

    if request.method == 'POST':
        try:
            faculty = request.user.faculty
        except:
            if request.user.is_superuser:
                faculty = "superuser"
            else:
                messages.error(request, "User is not a faculty memeber")
                return redirect("home")


        details = {
            'branch':request.POST['branch'],
            'year': request.POST['year'],
            'section':request.POST['section'],
            'period':request.POST['period'],
            'faculty':faculty
            }
        if Attendence.objects.filter(date = str(date.today()),branch = details['branch'], year = details['year'], section = details['section'],period = details['period']).count() != 0 :
            messages.error(request, "Attendence already recorded.")
            return redirect('home')

        else:
            students = Student.objects.filter(branch = details['branch'], year = details['year'], section = details['section'])
            print(students)
            names = Recognizer(details)
            print("names -> ", names)
            for student in students:
                if str(student.registration_id) in names:
                    attendence = Attendence(Faculty_Name = faculty, 
                    Student_ID = str(student.registration_id), 
                    period = details['period'], 
                    branch = details['branch'], 
                    year = details['year'], 
                    section = details['section'],
                    status = 'Present')
                    attendence.save()
                else:
                    attendence = Attendence(Faculty_Name = faculty, 
                    Student_ID = str(student.registration_id), 
                    period = details['period'],
                    branch = details['branch'], 
                    year = details['year'], 
                    section = details['section'])
                    attendence.save()
            attendences = Attendence.objects.filter(date = str(date.today()),branch = details['branch'], year = details['year'], section = details['section'],period = details['period'])
            context = {"attendences":attendences, "ta":True}
            messages.success(request, "Attendence taking Success")
            return render(request, 'attendence_sys/attendence.html', context)        
    context = {}
    return render(request, 'attendence_sys/home.html', context)

def searchAttendence(request):

    attendences = Attendence.objects.all()
    myFilter = AttendenceFilter(request.GET, queryset=attendences)
    attendences = myFilter.qs
    context = {'myFilter':myFilter, 'attendences': attendences, 'ta':False}
    return render(request, 'attendence_sys/attendence.html', context)


def facultyProfile(request):
    try:
        faculty = request.user.faculty
    except:
        messages.error(request, "user is not given the faculty privileges")
        return redirect("home")

    form = FacultyForm(instance = faculty)
    context = {'form':form}
    return render(request, 'attendence_sys/facultyForm.html', context)



# class VideoCamera(object):
#     def __init__(self):
#         self.video = cv2.VideoCapture(0)
#     def __del__(self):
#         self.video.release()

#     def get_frame(self):
#         ret,image = self.video.read()
#         ret,jpeg = cv2.imencode('.jpg',image)
#         return jpeg.tobytes()


# def gen(camera):
#     while True:
#         frame = camera.get_frame()
#         yield(b'--frame\r\n'
#         b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')


# @gzip.gzip_page
# def videoFeed(request):
#     try:
#         return StreamingHttpResponse(gen(VideoCamera()),content_type="multipart/x-mixed-replace;boundary=frame")
#     except:
#         print("aborted")

# def getVideo(request):
#     return render(request, 'attendence_sys/videoFeed.html')

def get_student_attendence_performance(student):
    
    try:
        percentage = 20/student.days
        absent = 20-student.days
    except ZeroDivisionError:
        percentage = 0
        absent = 20

    performance = f"""

        Stuent Name: { student.firstname } { student.firstname }\n
        Roll No: { student.registration_id }\n
        Department: { student.branch }\n
        Year: { student.year }\n
        Attendence Percentage: { percentage }%\n
        Present Day/s: { student.days}\n
        Absent Day/s: { absent }\n  
    """

    return performance
   



@login_required(login_url = 'login')
def send_report(request):

    if request.method == 'GET':

        if date.today().day >= 16:
                
            students = Student.objects.all()
            mails = []
            for student in students:
                performance = get_student_attendence_performance(student)
                student_instance = ("Attendence Report From University of Sindh, Jamshoro", performance, 'example@gmail.com', [student.contact])
                mails.append(student_instance)    


            try:    
                send_mass_mail(tuple(mails))
            except BadHeaderError:
                messages.error(request, 'Invalid header found.')
                return redirect("home")
            except ValueError:
                messages.error(request, "Network issue")
                return redirect("home") 
            except Exception:
                messages.error(request, "SMTP sender refused...")
                return redirect("home") 
            
            else:
                messages.success(request, "Attendance Report has been sent")
                return redirect("home")
        else:
            messages.error(request, "Attendence Report is supposed to be sent by end of every month")
            return redirect('home')

    