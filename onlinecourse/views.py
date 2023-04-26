from django.shortcuts import render
from django.http import HttpResponseRedirect
# <HINT> Import any new Models here
from .models import Course, Enrollment, Question, Choice, Submission
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.contrib.auth import login, logout, authenticate
import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)
# Create your views here.


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        # Check if user exists
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.error("New user")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("onlinecourse:index")
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        # Check if user enrolled
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        if num_results > 0:
            is_enrolled = True
    return is_enrolled


# CourseListView
class CourseListView(generic.ListView):
    template_name = 'onlinecourse/course_list_bootstrap.html'
    context_object_name = 'course_list'

    def get_queryset(self):
        user = self.request.user
        courses = Course.objects.order_by('-total_enrollment')[:10]
        for course in courses:
            if user.is_authenticated:
                course.is_enrolled = check_if_enrolled(user, course)
        return courses


class CourseDetailView(generic.DetailView):
    model = Course
    template_name = 'onlinecourse/course_detail_bootstrap.html'


def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        # Create an enrollment
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse(viewname='onlinecourse:course_details', args=(course.id,)))


# <HINT> Create a submit view to create an exam submission record for a course enrollment,
# you may implement it based on following logic:
         # Add each selected choice object to the submission object
         # Redirect to show_exam_result with the submission id
def submit(request, course_id):
    # Get user and course object, then get the associated enrollment object created when the user enrolled the course
    user = request.user
    course = get_object_or_404(Course, pk=course_id)
    enrollment = get_object_or_404(Enrollment, user=user, course=course)
    # Create a submission object referring to the enrollment
    submission = Submission.objects.create(enrollment=enrollment)
    if request.method == 'POST':
        # Collect the selected choices from exam form
        for item in request.POST.items():
          #  console.log(choice_id)
          #  choice_id = choice_id.replace('choice_', '')
            if item[0].startswith('choice_'):
                choice = get_object_or_404(Choice, pk=int(item[1]))
                submission.choices.add(choice)
        submission.save()
   
    return HttpResponseRedirect(reverse(viewname='onlinecourse:show_exam_result', args=(course.id, submission.id)))



# <HINT> A example method to collect the selected choices from the exam form from the request object
def extract_answers(request):
    submitted_anwsers = []
    for key in request.POST:
        if key.startswith('choice'):
            value = request.POST[key]
            choice_id = int(value)
            submitted_anwsers.append(choice_id)
    return submitted_anwsers


# <HINT> Create an exam result view to check if learner passed exam and show their question results and result for each question,
# you may implement it based on the following logic:
        # Get course and submission based on their ids
        # Get the selected choice ids from the submission record
        # For each selected choice, check if it is a correct answer or not
        # Calculate the total score
def show_exam_result(request, course_id, submission_id):
    # Get course and submission based on their ids
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    
    # Get the selected choice ids from the submission record
    selected_choice_ids = submission.choices.values_list('id', flat=True)
    
    # For each selected choice, check if it is a correct answer or not
    total_score = 0
    question_results = {}
    """
    for choice in submission.choices.all():
        is_correct = choice.is_correct
        if is_correct:
#            question_results.append({'question': choice.question, 'choice_id': choice.id})
            total_score += choice.question.grade
    """
    """
    for question in course.question_set.all():
        score_flag = True
        for choice in question.choice_set.filter(is_correct=True):
            sub_choices = submission.choices.filter(question_id = question.id)
            if sub_choices.filter(id__in = choice.id) == None:
                score_flag = False
                break

            if score_flag:
                total_score += question.grade

            #question_results[question_id](choice.id)
    """
    for question in course.question_set.all():
        score_flag = True
        #for choice in question.choice_set.filter(is_correct=True):
        sub_choice = submission.choices.filter(question_id=question.id)
        for choice in question.choice_set.all():
            value = 0
            exists = sub_choice.filter(id=choice.id).exists()
            if choice.is_correct:
                value = 1 if exists else -1
            else:
                value = -1 if exists else 0            
                
            if value == -1:
                score_flag = False
            question_results[choice.id] = value

        if score_flag:
            total_score += question.grade


    # Calculate the total score
   #max_score = submission.enrollment.exam.total_points
    #percentage = (total_score / max_score) * 100
    #passed = percentage >= submission.enrollment.exam.passing_percentage
    
    # Render the exam result template with the results
    return render(request, 'onlinecourse/exam_result_bootstrap.html', {
        'course': course,
        'submission': submission,
        'grade' : total_score,
       # 'total_score': total_score,
       # 'max_score': max_score,
       # 'percentage': percentage,
       # 'passed': passed,
        'question_results': question_results,
    })


