import mysql.connector as mysqlcon
from flask import Flask, render_template, request, redirect
from verify import *

app = Flask(__name__)

connection = mysqlcon.connect(
    host="localhost",
    database="onlinebanksystem",
    user="root",
    password="mysql"
)


def fetch(username):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM user_details WHERE user_name = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        result = [ele for ele in result]
        return result
    else:
        return False


def fetch_history(username):
    cursor = connection.cursor()
    cursor.execute("SELECT login_timestamp, logout_timestamp, locked, lock_limit FROM login"
                   " WHERE user_name = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result
    else:
        return False


def login(username):
    details = fetch(username)
    cursor = connection.cursor()
    cursor.execute('UPDATE login set login_timestamp = current_timestamp, lock_limit = %s where user_name = %s',
                   (3, username))
    connection.commit()
    cursor.close()
    send_mobile(str(details[4]), f"You Logged into the TMBL bank system.\n\nUser name : {username}")
    send_email(details[5], "TMBL Logs", f"You Logged into the TMBL bank system.\n\nUser name : {username}")


def logout(username):
    details = fetch(username)
    cursor = connection.cursor()
    cursor.execute('UPDATE login set logout_timestamp = current_timestamp where user_name = %s',
                   (username,))
    connection.commit()
    cursor.close()
    send_mobile(str(details[4]), f"You Logged out from TMBL bank system.\n\nUser name : {username}")
    send_email(details[5], "TMBL Logs", f"You Logged out from TMBL bank system.\n\nUser name : {username}")


@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('/www.tmbl.banking.net.com/')


@app.route('/www.tmbl.banking.net.com/', methods=['GET', 'POST'])
def main():
    if request.method == "GET":
        if connection.is_connected():
            return render_template('login.html')
        else:
            return render_template('login.html', error="Server is Busy Try again Later.")
    else:
        cursor = connection.cursor()
        user_name = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT user_id FROM login WHERE user_name = %s AND password = %s", (user_name, password))
        user = cursor.fetchone()
        lock_limit = fetch_history(user_name)
        exist_user = fetch(user_name)
        if user:
            details = fetch(user_name)
            if details[7] == 'Y':
                if details[10] == 'Y':
                    pass
                else:
                    return redirect_verification(user_name)
            else:
                return redirect_verification(user_name)
        elif not exist_user:
            return render_template('login.html', message=f"Login was unsuccessful! Username is incorrect!")
        elif lock_limit[-1] != 0:
            cursor.execute('UPDATE login set lock_limit = %s where user_name = %s', (lock_limit[-1] - 1, user_name,))
            connection.commit()
            cursor.close()
            return render_template('login.html', message=f"Login was unsuccessful! Password is incorrect! "
                                                         f"You have {lock_limit[-1]} attempts left",
                                   forgot=True, username=user_name)
        else:
            if lock_limit[-2] == 'Y':
                cursor.execute("SELECT user_id FROM login WHERE user_name = %s AND password = %s",
                               (user_name, password))
                user = cursor.fetchone()
                cursor.close()
                if user:
                    return render_template('login.html', message="Please Unlock Your Account!",
                                           unlock=True, username=user_name)
                return render_template('login.html', message="Incorrect password! Please Unlock "
                                                             "your Account first.", unlock=True, username=user_name)
            else:
                cursor.execute('UPDATE login set locked = %s where user_name = %s', ('Y', user_name))
                connection.commit()
                cursor.close()
                return render_template('login.html', message="Account is Locked! due to incorrect password attempts",
                                       unlock=True, username=user_name)
        if lock_limit[-2] == 'Y':
            cursor.close()
            return render_template('login.html', message="Please Unlock Your Account!", unlock=True, username=user_name)
        else:
            login(user_name)
            cursor.close()
            return redirect(f'/www.tmbl.banking.net.com/home/{user_name}')


@app.route('/www.tmbl.banking.net.com/password_reset/<username>', methods=['GET', 'POST'])
def password_reset(username):
    details = fetch(str(username))
    contact = str(details[4])
    if request.method == "GET":
        otp = send_mobile(contact)
        return render_template('password_reset.html', contact=contact, username=username, otp=otp)
    else:
        new_password = request.form['signup-password']
        confirm = request.form['confirm']
        if confirm == 'N':
            otp = send_mobile(contact)
            return render_template('password_reset.html', contact=contact, username=username, otp=otp)
        else:
            send_mobile(contact, "Your password reset was done successfully.")
            send_email(details[5], 'Reset Successful', "Your password reset was done successfully.")
            cursor = connection.cursor()
            cursor.execute('UPDATE login SET password = %s where user_name = %s', (new_password, username))
            connection.commit()
            cursor.close()
            return redirect('/www.tmbl.banking.net.com/')


def generate_wallet_id():
    cursor = connection.cursor()
    cursor.execute("SELECT wallet_id from wallet;")
    wallet_list = list(cursor.fetchall())
    code = str(random.randint(100000, 999999))
    if code in wallet_list:
        return generate_wallet_id()
    else:
        return code


def generate_user_id():
    cursor = connection.cursor()
    cursor.execute("SELECT user_id from login;")
    user_list = list(cursor.fetchall())
    code = str(random.randint(1000000000, 9999999999))
    if code in user_list:
        return generate_user_id()
    else:
        return code


@app.route('/www.tmbl.banking.net.com/sign_up', methods=['GET', 'POST'])
def sign_up():
    cursor = connection.cursor()
    if request.method == 'POST':
        cursor = connection.cursor()
        user_id = generate_user_id()
        wallet_id = generate_wallet_id()

        user_name = request.form['signup-username']
        first_name = request.form['firstname']
        last_name = request.form['lastname']

        email = request.form['email']

        password = request.form['signup-password']
        contact = request.form['phone']
        date_of_birth = request.form['dob']

        cursor.execute("INSERT INTO user_details VALUES (%s, %s, %s, %s, %s, %s, %s, %s, current_timestamp, '+91', %s)",
                       (user_name, first_name, last_name, wallet_id, contact, email, date_of_birth, "N", 'N'))
        connection.commit()

        cursor.execute("INSERT INTO login VALUES (%s, %s, %s, %s, %s, %s, %s)",
                       (user_id, user_name, password, None, None, "N", 3))
        connection.commit()

        cursor.close()

        return redirect_verification(user_name)

    cursor.execute("SELECT user_name FROM user_details")
    list_user = [str(ele[0]) for ele in cursor.fetchall()]

    cursor.execute("SELECT email FROM user_details")
    list_email = [str(ele[0]) for ele in cursor.fetchall()]

    cursor.close()

    return render_template('sign_up.html', list_user=list_user, list_email=list_email)


def redirect_verification(username):
    details = fetch(username)
    if details[7] == 'Y' and details[10] == 'Y':
        return redirect('/www.tmbl.banking.net.com/')
    elif details[7] == 'Y':
        return redirect(f'/www.tmbl.banking.net.com/verify_mail/{username}')
    else:
        return redirect(f'/www.tmbl.banking.net.com/verify_mobile/{username}')


@app.route('/www.tmbl.banking.net.com/verify_mobile/<username>', methods=['GET', 'POST'])
def verify_mobile(username):
    details = fetch(str(username))
    contact = str(details[4])
    if request.method == "GET":
        otp = send_mobile(contact)
        return render_template('verify_mobile.html', disabled=False, contact=contact, otp=otp)
    else:
        confirm = request.form['confirm']
        if confirm == 'N':
            otp = send_mobile(contact)
            return render_template('verify_mobile.html', disabled=False, contact=contact, otp=otp)
        else:
            send_mobile(contact, "Your mobile verification was done successfully.")
            cursor = connection.cursor()
            cursor.execute('UPDATE user_details SET verified_mobile = "Y" where user_name = %s', (username,))
            connection.commit()
            cursor.close()
            return redirect_verification(username)


@app.route('/www.tmbl.banking.net.com/verify_mail/<username>', methods=['GET', 'POST'])
def verify_mail(username):
    details = fetch(str(username))
    email = str(details[5])
    if request.method == "GET":
        otp = send_email(email)
        return render_template('verify_mail.html', disabled=False, email=email, otp=otp)
    else:
        confirm = request.form['confirm']
        if confirm == 'N':
            otp = send_email(email)
            return render_template('verify_mail.html', disabled=False, email=email, otp=otp)
        else:
            cursor = connection.cursor()
            cursor.execute('UPDATE user_details SET verified_mail = "Y" where user_name = %s', (username,))
            connection.commit()
            cursor.close()
            email = str(details[5])
            send_email(email, "Registration Successful", "Your email verification was done successfully.")
            return redirect_verification(username)


@app.route('/www.tmbl.banking.net.com/lock/<username>', methods=['GET', 'POST'])
def lock(username):
    details = fetch(str(username))
    contact = str(details[4])
    if request.method == "GET":
        otp = send_mobile(contact, 'Enter the otp only if you want to lock your account')
        return render_template('lock.html', contact=contact, username=username, otp=otp)
    else:
        confirm = request.form['confirm']
        if confirm == 'N':
            otp = send_mobile(contact)
            return render_template('lock.html', contact=contact, username=username, otp=otp)
        else:
            send_mobile(contact, f"Your Account {username} locked successfully.")
            send_email(details[5], 'Locked Successfully', f"Your Account {username} locked successfully.")
            cursor = connection.cursor()
            cursor.execute('UPDATE login SET locked = "Y", lock_limit = 0 where user_name = %s', (username,))
            connection.commit()
            cursor.close()
            return redirect('/www.tmbl.banking.net.com/')


@app.route('/www.tmbl.banking.net.com/unlock/<username>', methods=['GET', 'POST'])
def unlock(username):
    details = fetch(str(username))
    contact = str(details[4])
    if request.method == "GET":
        otp = send_mobile(contact, 'Enter the otp only if you want to unlock your account')
        return render_template('unlock.html', contact=contact, username=username, otp=otp)
    else:
        confirm = request.form['confirm']
        if confirm == 'N':
            otp = send_mobile(contact)
            return render_template('unlock.html', contact=contact, username=username, otp=otp)
        else:
            send_mobile(contact, f"Your Account {username} unlocked successfully.")
            send_email(details[5], 'Unlocked Successfully', f"Your Account {username} unlocked successfully.")
            cursor = connection.cursor()
            cursor.execute('UPDATE login SET locked = "N", lock_limit = 3 where user_name = %s', (username,))
            connection.commit()
            cursor.close()
            return redirect('/www.tmbl.banking.net.com/')


@app.route('/www.tmbl.banking.net.com/home/<username>', methods=['GET', 'POST'])
def home(username):
    details = fetch(username)
    logins = fetch_history(username)
    if request.method == "GET":
        return render_template('home.html', details=details, logins=logins)
    else:
        logout(username)
        return redirect('/www.tmbl.banking.net.com/')


def fetch_transactions(username, transaction_id=False):
    cursor = connection.cursor()
    if not transaction_id:
        cursor.execute("SELECT wallet_id FROM user_details WHERE user_name = %s", (username,))
        result = cursor.fetchone()[0]
        cursor.execute("SELECT * FROM transactions WHERE from_wallet_id = %s OR to_wallet_id = %s order by "
                       "transaction_timestamp desc", (result, result))
        transaction_history = cursor.fetchall()
    else:
        cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", (transaction_id,))
        transaction_history = [ele for ele in cursor.fetchone()]
        cursor.execute("SELECT remarks FROM transaction_details WHERE transaction_id = %s", (transaction_id,))
        if transaction_history[5] == 'N':
            transaction_history.append('green')
        else:
            transaction_history.append('red')
        transaction_history[5] = cursor.fetchone()[0]
    cursor.close()
    if transaction_history:
        return transaction_history
    else:
        return False


def fetch_username_by_wallet_id(wallet_id):
    cursor = connection.cursor()
    cursor.execute("SELECT user_name FROM user_details WHERE wallet_id = %s", (wallet_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result[0]
    else:
        return False


def fetch_wallet_information(wallet_id):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM wallet WHERE wallet_id = %s", (wallet_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return result
    else:
        return False


def generate_transaction_id():
    cursor = connection.cursor()
    cursor.execute("SELECT transaction_id from transactions")
    transaction_list = list(cursor.fetchall())
    code = str(random.randint(10000000, 99999999))
    if code in transaction_list:
        return generate_transaction_id()
    else:
        return code


@app.route('/www.tmbl.banking.net.com/account/<username>', methods=['GET', 'POST'])
def account(username):
    details = fetch(username)
    wallet_information = fetch_wallet_information(details[3])
    balance = wallet_information[2]
    table_transaction = []
    transaction_history = fetch_transactions(username)
    if transaction_history:
        for item in transaction_history:
            transaction_id = item[0]
            from_account = fetch_username_by_wallet_id(item[1])
            to_account = fetch_username_by_wallet_id(item[3])
            if not to_account:
                to_account = 'Invalid Account'
            amount = '₹' + str(item[2])
            color = 'red'
            if from_account == username and to_account != username and item[5] == 'N':
                amount = '- ' + amount
            elif to_account == username and item[5] == 'N':
                amount = '+ ' + amount
                color = 'green'
            else:
                amount = '🚫 ' + amount
            if from_account == to_account:
                from_account = '+91 ' + str(details[4])
            time = item[4]
            table_transaction.append([transaction_id, from_account, amount, to_account, time, color])
    else:
        table_transaction = False
        return render_template('account.html', table=table_transaction, username=username, balance=balance)
    return render_template('account.html', table=table_transaction, username=username,
                           balance=balance)


@app.route('/www.tmbl.banking.net.com/transaction_query/<username>?<transaction_id>', methods=['GET', 'POST'])
def transaction_query(username, transaction_id):
    transaction_details = fetch_transactions(username, transaction_id)
    details = fetch(fetch_username_by_wallet_id(transaction_details[1]))
    to_user = fetch_username_by_wallet_id(transaction_details[3])
    if not to_user:
        to_user = ['Invalid Account', '', '', '', 'XXXXXXXXXX']
    else:
        to_user = fetch(to_user)
    return render_template('transaction_query.html', username=username, details=details,
                           to_user=to_user, transactions=transaction_details)


def transaction_details_update(transaction_id, error=False):
    cursor = connection.cursor()
    if error:
        error = 'Transaction was terminated ' + str(error)
        cursor.execute('INSERT into transaction_details values(%s, %s)', (transaction_id, error))
    else:
        cursor.execute('INSERT into transaction_details(transaction_id) values(%s)', (transaction_id,))
    connection.commit()
    cursor.close()


@app.route('/www.tmbl.banking.net.com/add_money/<username>', methods=['GET', 'POST'])
def add_money(username):
    details = fetch(username)
    wallet_information = fetch_wallet_information(details[3])
    if request.method == "GET":
        return render_template('add_money.html', username=username, wallet_id=details[3],
                               timing=0, transaction=['', ''])
    confirm = request.form['confirm']
    if confirm == 'N':
        amount = request.form['amount']
        otp = send_mobile(str(details[4]), 'OTP for Transaction Fund on TMBL Online Bank System', True)
        return render_template('add_money.html', username=username, wallet_id=details[3], timing=1, display=True,
                               otp=otp, transaction=[amount, ])
    else:
        amount = request.form['amount']
        cursor = connection.cursor()
        transaction_id = generate_transaction_id()
        cursor.execute('INSERT into transactions values(%s, %s, %s, %s, current_timestamp, "N")',
                       (transaction_id, details[3], amount, details[3]))
        cursor.execute('UPDATE wallet SET amount = amount + %s where wallet_id = %s', (amount, details[3]))
        connection.commit()
        cursor.close()
        transaction_details_update(transaction_id)
        balance = int(amount) + wallet_information[2]
        send_mobile(str(details[4]),
                    f"Credited Rs.{amount} to your Wallet XXX{str(details[3])[3:]}\n\nTransaction id: {transaction_id}"
                    f"\nBalance: Rs.{balance}")
        send_email(details[5], "Transaction Credit",
                   f"Credited Rs.{amount} from your Wallet XXX{str(details[3])[3:]}\n\nTransaction id: {transaction_id}"
                   f"\nBalance: Rs.{balance}")
        return redirect(f'/www.tmbl.banking.net.com/account/{username}')


@app.route('/www.tmbl.banking.net.com/transfer/<username>', methods=['GET', 'POST'])
def transfer(username):
    details = fetch(username)
    if request.method == "GET":
        return render_template('transfer.html', username=username, wallet_id=details[3], timing=0, transaction=['', ''])
    confirm = request.form['confirm']
    if confirm == 'N':
        amount = request.form['amount']
        to_account = request.form['toAccount']
        otp = send_mobile(str(details[4]), 'OTP for Transaction Fund on TMBL Online Bank System', True)
        return render_template('transfer.html', username=username, wallet_id=details[3], timing=1, display=True,
                               otp=otp, transaction=[to_account, amount])
    else:
        amount = request.form['amount']
        to_account = request.form['toAccount']
        to_user = fetch(to_account)
        wallet_information = fetch_wallet_information(details[3])
        balance = wallet_information[2]
        error = False
        cursor = connection.cursor()
        transaction_id = generate_transaction_id()
        if not to_user:
            error = 'due to Invalid Account Details'
            to_user = ['', '', '', '1111111']
        if int(amount) > balance and error:
            error += ' and Insufficient balance'
        elif int(amount) > balance and not error:
            error = 'due to Insufficient balance'
        if error:
            send_mobile(str(details[4]),
                        f"Last Transaction was cancelled {error} for your Wallet XXX{str(details[3])[3:]}")
            send_email(details[5], "Transaction Cancelled",
                       f"Last Transaction was cancelled {error} for your Wallet XXX{str(details[3])[3:]}")
            cursor.execute('UPDATE wallet SET amount = amount + %s where wallet_id = %s', (amount, details[3]))
            cursor.execute('UPDATE wallet SET amount = amount - %s where wallet_id = %s', (amount, to_user[3]))
            cursor.execute('INSERT into transactions values(%s, %s, %s, %s, current_timestamp, "Y")',
                           (transaction_id, details[3], amount, to_user[3]))
            transaction_details_update(transaction_id, error)
            connection.commit()
            cursor.close()
            return render_template('transfer.html', username=username, wallet_id=details[3], timing=0,
                                   transaction=['', ''], error=error)
        cursor.execute('INSERT into transactions values(%s, %s, %s, %s, current_timestamp, "N")',
                       (transaction_id, details[3], amount, to_user[3]))
        transaction_details_update(transaction_id)
        connection.commit()
        cursor.close()

        balance = balance - int(amount)
        to_balance = fetch_wallet_information(to_user[3])[2]

        send_mobile(str(details[4]),
                    f"Debited Rs.{amount} from your Wallet XXX{str(details[3])[3:]} to Wallet XXX{str(to_user[3])[3:]}"
                    f" with user name : {to_user[0]}\n\nTransaction id: {transaction_id}"
                    f"\nBalance: Rs.{balance}\nIf you did not Then Contact us immediately."
                    "\nContact: +91 8610357516\nContact: +91 9491234506")
        send_email(details[5], "Transaction Debit",
                   f"Debited Rs.{amount} from your Wallet XXX{str(details[3])[3:]} to Wallet XXX{str(to_user[3])[3:]}"
                   f" with user name : {to_user[0]}\n\nTransaction id: {transaction_id}"
                   f"\nBalance: Rs.{balance}\nIf you did not Then Contact us immediately."
                   "\nContact: +91 8610357516\nContact: +91 9491234506")
        send_mobile(str(to_user[4]),
                    f"Credited Rs.{amount} to your Wallet XXX{str(to_user[3])[3:]}\n\nTransaction id: {transaction_id}"
                    f"\nBalance: Rs.{to_balance}")
        send_email(to_user[5], "Transaction Credit",
                   f"Credited Rs.{amount} from your Wallet XXX{str(to_user[3])[3:]}\n\nTransaction id: {transaction_id}"
                   f"\nBalance: Rs.{to_balance}")
        return redirect(f'/www.tmbl.banking.net.com/account/{username}')


@app.route('/www.tmbl.banking.net.com/update/<username>', methods=['GET', 'POST'])
def update(username):
    details = fetch(username)
    details.append(False)
    cursor = connection.cursor()
    cursor.execute("SELECT email FROM user_details")
    list_email = [str(ele[0]) for ele in cursor.fetchall()]
    cursor.execute("SELECT contact FROM user_details")
    list_contact = [str(ele[0]) for ele in cursor.fetchall()]
    if request.method == 'POST':
        email = request.form['email']
        current_password = request.form['current_password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        contact = int(request.form['contact'])
        wallet_id: int = details[3]
        new_password = request.form['new_password']
        given_details = [username, first_name, last_name, wallet_id, contact, email]
        cursor.execute('select password from login where user_name=%s', (username,))
        password = cursor.fetchone()[0]
        details.pop()
        if current_password == password:
            if details[0:6] != given_details or new_password:
                turnover = False
                cursor.execute("UPDATE user_details SET email = %s, first_name = %s, last_name = %s, contact = %s"
                               " WHERE user_name = %s", (email, first_name, last_name, contact, username))
                if email != details[5]:
                    send_email(details[5], 'Account Update', f'Unlinking your email from TMBL user : {username}')
                    cursor.execute("UPDATE user_details SET verified_mail = 'N' where user_name = %s", (username,))
                    turnover = True
                if contact != details[4]:
                    send_mobile(details[4], f'Unlinking your Contact from TMBL user : {username}')
                    cursor.execute("UPDATE user_details SET verified_mobile = 'N' where user_name = %s", (username,))
                    turnover = True
                if new_password:
                    if turnover:
                        send_mobile(details[4], 'Password was changed Successfully.\nCheck your '
                                                f'mail for Accounts unlinked from TMBL user : {username}')
                    else:
                        send_mobile(details[4], f'Password was changed Successfully for TMBL user : {username}')
                    cursor.execute("UPDATE login SET password = %s WHERE user_name = %s", (new_password, username))
                connection.commit()
                cursor.close()
                if turnover:
                    logout(username)
                    return redirect_verification(username)
                return redirect(f'/www.tmbl.banking.net.com/home/{details[0]}')
            else:
                details.append('Oops! Same Data, No Updates done.')
                cursor.close()
                return render_template('update.html', details=details, list_email=list_email, list_contact=list_contact)
        else:
            details.append('Oops! Check Your Password')
            cursor.close()
            return render_template('update.html', details=details, list_email=list_email, list_contact=list_contact)
    cursor.close()
    return render_template('update.html', details=details, list_email=list_email, list_contact=list_contact)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=1000, load_dotenv=False)
