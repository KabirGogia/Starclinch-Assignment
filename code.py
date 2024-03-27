from django.shortcuts import render
from django.http import JsonResponse
from django.db import models
import boto3

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, unique=True)

class Expense(models.Model):
    EQUAL = 'EQUAL'
    EXACT = 'EXACT'
    PERCENT = 'PERCENT'
    TYPE_CHOICES = [
        (EQUAL, 'Equal'),
        (EXACT, 'Exact'),
        (PERCENT, 'Percent'),
    ]
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    creator = models.ForeignKey(User, related_name='expenses_created', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class ExpenseParticipant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

def add_expense(request):
    if request.method == 'POST':
        creator_id = request.POST.get('creator_id')
        amount = float(request.POST.get('amount'))
        expense_type = request.POST.get('type')
        participants = request.POST.getlist('participants')

        creator = User.objects.get(id=creator_id)
        expense = Expense.objects.create(amount=amount, type=expense_type, creator=creator)
        
        if expense_type == Expense.EQUAL:
            amount_per_person = amount / len(participants)
            for participant_id in participants:
                participant = User.objects.get(id=participant_id)
                ExpenseParticipant.objects.create(user=participant, expense=expense, amount=amount_per_person)
        # Implement similar logic for EXACT and PERCENT cases

        return JsonResponse({'status': 'success'})
    else:
        users = User.objects.all()
        return render(request, 'add_expense.html', {'users': users})

def view_balances(request, user_id):
    user = User.objects.get(id=user_id)
    balances = {}
    expenses_created = user.expenses_created.all()
    for expense in expenses_created:
        participants = expense.expenseparticipant_set.all()
        for participant in participants:
            if participant.user != user:
                balances[participant.user.name] = balances.get(participant.user.name, 0) + participant.amount

    return JsonResponse(balances)

def split_equally(amount, participants):
    return amount / len(participants)

def split_exact(amount, shares):
    total_shares = sum(shares)
    if total_shares != amount:
        raise ValueError("Total shares must equal the total amount")
    return shares

def split_percent(amount, percentages):
    total_percentage = sum(percentages)
    if total_percentage != 100:
        raise ValueError("Total percentages must equal 100")
    return [amount * p / 100 for p in percentages]

def update_user_data():
    # Fetch user data from the database
    users = User.objects.all()

    # Write data to a file
    data = '\n'.join([f'{user.name},{user.email},{user.mobile_number}' for user in users])
    
    # Upload file to Amazon S3
    s3 = boto3.client('s3')
    s3.put_object(Body=data, Bucket='your-bucket-name', Key='user_data.csv')
