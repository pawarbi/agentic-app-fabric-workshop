import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Category and merchant data for realistic transactions
TRANSACTION_CATEGORIES = {
    'payment': [
        ('Groceries', ['Whole Foods', 'Trader Joe\'s', 'Safeway', 'Kroger', 'Target']),
        ('Restaurants', ['Starbucks', 'Chipotle', 'McDonald\'s', 'Subway', 'Pizza Hut']),
        ('Shopping', ['Amazon', 'Walmart', 'Best Buy', 'Target', 'Costco']),
        ('Entertainment', ['Netflix', 'Spotify', 'AMC Theaters', 'PlayStation Store']),
        ('Utilities', ['PG&E', 'Comcast', 'AT&T', 'Water District', 'Electric Co']),
        ('Transportation', ['Shell', 'Chevron', 'Uber', 'Lyft', 'Metro Transit']),
        ('Healthcare', ['CVS Pharmacy', 'Walgreens', 'Medical Center', 'Dental Care']),
    ],
    'deposit': [
        ('Salary', ['Direct Deposit - Payroll', 'Monthly Salary']),
        ('Refund', ['Tax Refund', 'Purchase Refund']),
        ('Transfer', ['External Transfer', 'Wire Transfer']),
    ]
}

def generate_user_data():
    """Generate a complete fake user with accounts and transactions"""
    
    user_id = f"user_{uuid.uuid4()}"
    
    # Generate user
    user = {
        'id': user_id,
        'name': fake.name(),
        'email': fake.email(),
        'created_at': datetime.utcnow()
    }
    
    # Generate 2-4 accounts
    num_accounts = random.randint(2, 4)
    accounts = []
    account_types_available = ['checking', 'savings', 'credit']
    
    # Always create at least one checking and one savings
    mandatory_accounts = [
        {
            'id': f"acc_{uuid.uuid4()}",
            'user_id': user_id,
            'account_number': str(uuid.uuid4().int)[:12],
            'account_type': 'checking',
            'balance': round(random.uniform(500, 5000), 2),
            'name': f"{fake.word().capitalize()} Checking",
            'created_at': datetime.utcnow() - timedelta(days=random.randint(365, 1095))
        },
        {
            'id': f"acc_{uuid.uuid4()}",
            'user_id': user_id,
            'account_number': str(uuid.uuid4().int)[:12],
            'account_type': 'savings',
            'balance': round(random.uniform(1000, 20000), 2),
            'name': f"{fake.word().capitalize()} Savings",
            'created_at': datetime.utcnow() - timedelta(days=random.randint(365, 1095))
        }
    ]
    
    accounts.extend(mandatory_accounts)
    
    # Add additional random accounts
    for _ in range(num_accounts - 2):
        account_type = random.choice(account_types_available)
        if account_type == 'credit':
            balance = round(random.uniform(-2000, -100), 2)  # Negative for credit
        elif account_type == 'savings':
            balance = round(random.uniform(1000, 30000), 2)
        else:
            balance = round(random.uniform(100, 8000), 2)
            
        accounts.append({
            'id': f"acc_{uuid.uuid4()}",
            'user_id': user_id,
            'account_number': str(uuid.uuid4().int)[:12],
            'account_type': account_type,
            'balance': balance,
            'name': f"{fake.word().capitalize()} {account_type.capitalize()}",
            'created_at': datetime.utcnow() - timedelta(days=random.randint(30, 730))
        })
    
    # Generate 20-50 transactions
    num_transactions = random.randint(20, 50)
    transactions = []
    
    # --- CHANGE: Removed the checking_accounts and savings_accounts lists here ---
    
    for i in range(num_transactions):
        transaction_type = random.choices(
            ['payment', 'deposit', 'transfer'],
            weights=[0.6, 0.2, 0.2]
        )[0]
        
        if transaction_type == 'payment':
            category, merchants = random.choice(TRANSACTION_CATEGORIES['payment'])
            merchant = random.choice(merchants)
            
            # --- CHANGE: Filter for payment-capable accounts directly from master 'accounts' list ---
            payment_accounts = [acc for acc in accounts if acc['account_type'] != 'credit']
            
            # This check *should* be redundant, but it adds safety
            if not payment_accounts:
                continue
                
            from_account = random.choice(payment_accounts)
            
            transactions.append({
                'id': f"txn_{uuid.uuid4()}",
                'from_account_id': from_account['id'],
                'to_account_id': None,
                'amount': round(random.uniform(5, 500), 2),
                'type': 'payment',
                'description': f"Payment to {merchant}",
                'category': category,
                'status': 'completed',
                'created_at': datetime.utcnow() - timedelta(days=random.randint(0, 180))
            })
            
        elif transaction_type == 'deposit':
            category, descriptions = random.choice(TRANSACTION_CATEGORIES['deposit'])
            description = random.choice(descriptions)

            # --- CHANGE: Filter for deposit-capable accounts directly from master 'accounts' list ---
            deposit_accounts = [acc for acc in accounts if acc['account_type'] == 'checking']

            # This check *should* be redundant, but it adds safety
            if not deposit_accounts:
                continue

            to_account = random.choice(deposit_accounts)
            
            transactions.append({
                'id': f"txn_{uuid.uuid4()}",
                'from_account_id': None,
                'to_account_id': to_account['id'],
                'amount': round(random.uniform(100, 3000), 2),
                'type': 'deposit',
                'description': description,
                'category': category,
                'status': 'completed',
                'created_at': datetime.utcnow() - timedelta(days=random.randint(0, 180))
            })
            
        else:  # transfer
            if len(accounts) >= 2:
                from_account = random.choice(accounts)
                to_account = random.choice([acc for acc in accounts if acc['id'] != from_account['id']])
                
                transactions.append({
                    'id': f"txn_{uuid.uuid4()}",
                    'from_account_id': from_account['id'],
                    'to_account_id': to_account['id'],
                    'amount': round(random.uniform(50, 1000), 2),
                    'type': 'transfer',
                    'description': f"Transfer from {from_account['name']} to {to_account['name']}",
                    'category': 'Transfer',
                    'status': 'completed',
                    'created_at': datetime.utcnow() - timedelta(days=random.randint(0, 180))
                })
    
    # Sort transactions by date (newest first)
    transactions.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        'user': user,
        'accounts': accounts,
        'transactions': transactions
    }