import logging
import os
import pymysql
import re
from model import DBManager, Message
from flask import render_template, request, session, redirect, url_for, Flask, jsonify
from mysql import connector
from passlib.hash import sha256_crypt
from flask_socketio import SocketIO, join_room, leave_room
from datetime import datetime


app = Flask(__name__)

# !--- For debugging switch to true ---!
app.debug = True

UPLOAD_FOLDER = '/vagrant/static/images/'

app.config["SECRET_KEY"] = "OCML3BRawWEUeaxcuKHLpw"
#toolbar = DebugToolbarExtension(app)

socketio = SocketIO(app, manage_session=False, cors_allowed_origins="*")
chatClients = dict()

def definedlog(fileHandler):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.ERROR)
    handler = logging.FileHandler(fileHandler)
    handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s : %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


@app.route('/')
def index():
    return render_template('/index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    mycursor = DBManager().getCursor()
    message = ""
    if request.method == 'POST':
        try:
            userDetails = request.form
            username = userDetails['username']
            unQuery = "SELECT username FROM users WHERE username = '" + username + "'"
            mycursor.execute(unQuery)
            username_from_db = mycursor.fetchall()
            if username_from_db:
                raise Exception('User name already Exists!')
            password = userDetails["password1"]
            password_confirm = userDetails["password2"]
            if password != password_confirm:
                raise Exception('Passwords does not match!')
            password = sha256_crypt.encrypt(userDetails["password1"])
            firstName = userDetails['firstName']
            lastName = userDetails['lastName']
            phone = userDetails['phone']
            email = userDetails['email']
            result1 = email.find('@GMAIL.COM')
            result2 = email.find('@gmail.com')
            result3 = email.find('@gmail.COM')
            result4 = email.find('@GMAIL.com')
            result5 = email.find('@Gmail.com')
            if result1 == -1 and result2 == -1 and result3 == -1 and result4 == -1 and result5 == -1:
                error = 'you have to put gmail account in order to use our app'
                raise Exception(error)
            mycursor = DBManager().getCursor()
            sql = "INSERT INTO users (username, password, firstName, lastName, phone, email) VALUES (%s, %s, %s, %s, %s, %s)"
            val = (username, password, firstName, lastName, phone, email)
            mycursor.execute(sql, val)
            DBManager.connection.commit()
            session['USERNAME'] = username
            return redirect(url_for('homepage'))
        except Exception as error:
            message = str(error)

    return render_template('/register.html', message=message)


@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ""
    if get_user_logged_in():
        return redirect('homepage')

    if request.method == "POST":
        req = request.form
        username = req.get("username")
        password = req.get("password")
        try:
            authenticate_user(username, password)
            return redirect(url_for('homepage'))
        except Exception as error:
            message = str(error)
    return render_template('/login.html', message=message)


def authenticate_user(username, password):
    maulers = DBManager().getCursor()
    Fender = "SELECT username, password FROM users WHERE username = '" + username + "'"
    maulers.execute(Fender)
    result = maulers.fetchall()
    print(result)
    for user in result:
        if sha256_crypt.verify(password, user[1]):
            session["USERNAME"] = user[0]
            return True
        else:
            raise Exception("Password doesn't match")
    raise Exception("Username not found")


def get_user_logged_in():
    if "USERNAME" in session:
        return session["USERNAME"]
    return False


@app.route("/homepage", methods=['POST', 'GET'])
def homepage():
    un = get_user_logged_in()
    if un:
        req = request.form
        filter = ""
        if request.method == 'POST':
            if req.get("filter") == 'submit':
                ge = req.get("gender")
                ar = req.get("area")
                if ge and ar:
                    filter = "gender='" + ge + "' and area ='" + ar + "'"
                elif ge:
                    filter = "gender='" + ge + "'"
                elif ar:
                    filter = "area='" + ar + "'"
        queryhomepage = "SELECT * FROM dogs"

        # add query for excluding from likes table
        queryhomepage += " WHERE dog_id NOT IN (SELECT dog_id FROM likes WHERE username='" + un + "') " +\
                        "AND username <> '" + un + "'"

        # add query for the filter in homepage
        if filter != "":
          
            queryhomepage += " AND " + filter
        mycursor = DBManager().getCursor()
        mycursor.execute(queryhomepage)
        result = mycursor.fetchall()
        return render_template('homepage.html', dogs=result)
    return redirect('login')


def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        binaryData = file.read()
    return binaryData


@app.route('/create_dog_profile/', methods=['POST', 'GET'])
def create_dog_profile():
    username = get_user_logged_in()
    if username:
        if request.method == "POST":
            try:
                details = request.form
                name = details['dog_name']

                # check if chip already exists
                chip = details['chip_number']
                mycursor = DBManager().getCursor()
                mycursor.execute("SELECT dog_id FROM dogs WHERE dog_id = '" + chip + "'")
                chip_from_db = mycursor.fetchall()
                if (chip_from_db):
                    raise Exception('Chip already Exists!')

                birth_date = details['birth_date']
                gender = details['gender']
                area = details['area']
                city = details['city']
                type = details['type']
                description = details['description']
                img1 = request.files['files']
                path1 = os.path.join('images/', img1.filename)
                img1.save(os.path.join(UPLOAD_FOLDER, img1.filename))
                photo1 = convertToBinaryData(
                    os.path.join(UPLOAD_FOLDER, img1.filename))
                img2 = request.files['img2']
                if img2.filename != '':
                    img2.save(os.path.join(UPLOAD_FOLDER, img2.filename))
                    path2 = os.path.join('images/', img2.filename)
                    photo2 = convertToBinaryData(
                        os.path.join(UPLOAD_FOLDER, img2.filename))
                else:
                    photo2 = ''
                    path2 = ''
                img3 = request.files['img3']
                if img3.filename != '':
                    path3 = os.path.join('images/', img3.filename)
                    img3.save(os.path.join(UPLOAD_FOLDER, img3.filename))
                    photo3 = convertToBinaryData(
                        os.path.join(UPLOAD_FOLDER, img3.filename))
                else:
                    photo3 = ''
                    path3 = ''

                mycursor.execute(
                    "INSERT INTO dogs(dog_id,name,bday,gender,area,city, type,details,pic1,path1,pic2,path2,pic3,path3,username) VALUES (%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (chip, name, birth_date, gender, area, city, type, description, photo1, path1, photo2, path2, photo3, path3,
                    username))
                DBManager().connection.commit()
                message = "Dog added successfully"
            except Exception as error:
                message = str(error)
        else:
            message = " "

        return render_template('create_dog_profile.html', message=message)
    return redirect('/login')


@app.route("/dogProfile/<dog_id>")
def dogProfile(dog_id):
    mycursor = DBManager().getCursor()
    uname = get_user_logged_in()
    if uname:
        queryDogProfile = "select * from dogs where dog_id=" + dog_id
        mycursor.execute(queryDogProfile)
        result = mycursor.fetchall()
        return render_template('dogProfile.html', dog=result)
    return redirect('login')


@app.route("/favorites/add", methods=['POST'])
def yes_button():
    username = get_user_logged_in()
    if username and 'dog_id' in request.form:
        details = request.form
        dog_id = details['dog_id']
        answer = details['answer']
        if answer == 'yes' or answer == 'no':
            mycursor = DBManager().getCursor()
            mycursor.execute(
                "INSERT INTO likes VALUES (%s, %s,%s)",
                (username, dog_id, answer))

        DBManager().connection.commit()
        return 'success'
    return 'fail'


@app.route("/favorites/", methods=['POST', 'GET'])
def favorites():
    username = get_user_logged_in()
    if username:
        if request.method == 'POST':
            details = request.form
            clear_but = details['clear']
            if clear_but == 'yes':
                clearChoices(username)
                return redirect('/homepage')
        query_favorites = "select * from dogs left join likes on likes.dog_id = dogs.dog_id where likes.username='" + \
            username + "' AND answer='yes' AND dogs.username <> '" + username + "'"
        mycursor = DBManager().getCursor()
        mycursor.execute(query_favorites)
        dogs = mycursor.fetchall()
        DBManager().connection.commit()
        DBManager().closeConnection()
        return render_template('favorites.html', dogs=dogs)
    return redirect('/login')




@app.route('/new_meeting', methods=['GET', 'POST'])
def new_meeting():
    '''
    :return: new_meeting template
    '''
    return render_template('/new_meeting.html')

@app.route("/favorites/add_meeting", methods=['POST'])
def add_meeting():
    '''
    send a proposal for a meeting to dog owner
    :return: homepage template
    '''
    mycursor = DBManager().getCursor()
    details = request.form
    username = get_user_logged_in()
    mycursor.execute("select username from dogs where dog_id=" + details['dog'])
    owner_username = mycursor.fetchone()
    mycursor.execute("select name from dogs where dog_id=" + details['dog'])
    dog_name = mycursor.fetchone()
    DBManager().connection.commit()
    sending_date = datetime.now()
    sending_date_formated = sending_date.strftime('%Y-%m-%d %H:%M:%S')
    date_time = details['time'].split('T')
    # the template massage: 'Can I meet {} in {} in {} at {}?\nYes/No'
    add_message_to_db(Message(username, owner_username[0], 'Can I meet ' + dog_name[0] + ' in ' + date_time[0] + ' in ' + date_time[1] + ' at ' + details['place'] + '?\nYes/No', sending_date_formated, 'True'))
    return redirect('/homepage')


def clearChoices(username):
    queryClear = "DELETE FROM likes WHERE username='" + username + "'"
    mycursor = DBManager().getCursor()
    mycursor.execute(queryClear)
    DBManager().connection.commit()


@app.route('/help')
def help():
    uname = get_user_logged_in()
    if uname:
        return render_template('/help.html')
    return redirect('login')


@app.route('/updateUser', methods=['POST', 'GET'])
def updateUser():
    mycursor = DBManager().getCursor()
    uname = get_user_logged_in()
    if uname:
        mycursor.execute(
            "SELECT * FROM users WHERE username = '" + uname + "'")
        user = mycursor.fetchall()
        if request.method == 'POST':
            try:
                formDetails = request.form
                name = formDetails['name']
                if name != "":
                    sql = "UPDATE users SET firstName = '" + \
                        name + "'  WHERE username = '" + uname + "'"
                    mycursor.execute(sql)
                    DBManager().connection.commit()

                lastname = formDetails['lastname']
                if lastname != "":
                    sql = "UPDATE users SET lastName = '" + \
                        lastname + "'  WHERE username = '" + uname + "'"
                    mycursor.execute(sql)
                    DBManager().connection.commit()

                phone = formDetails["tel"]
                if phone != "":
                    sql = "UPDATE users SET phone = '" + phone + \
                        "'  WHERE username = '" + uname + "'"
                    mycursor.execute(sql)
                    DBManager().connection.commit()

                mail = formDetails['mail']
                if mail != "":
                    result1 = mail.find('@GMAIL.COM')
                    result2 = mail.find('@gmail.com')
                    result3 = mail.find('@gmail.COM')
                    result4 = mail.find('@GMAIL.com')
                    result5 = mail.find('@Gmail.com')
                    if result1 == -1 and result2 == -1 and result3 == -1 and result4 == -1 and result5 == -1 :
                        error = 'you have to put gmail account in order to use our app'
                        raise Exception(error)
                    else:
                        sql = "UPDATE users SET email = '" + mail + "' where username = '" + uname + "'"
                        mycursor.execute(sql)
                        DBManager().connection.commit()
                        message = "your details were updates successfully"

                newpass = formDetails["newpass"]
                renewpass = formDetails["confirm"]

                if (newpass != "") & (renewpass != ""):
                    if newpass == renewpass:
                        newpass = sha256_crypt.encrypt(newpass)
                        sql = "UPDATE users SET password='" + newpass + "' where username='" + uname + "'"
                        mycursor.execute(sql)
                        DBManager().connection.commit()
                        message = "your details were updates successfully"
                    else:
                        message = "new password does NOT match to confirm password"

                mycursor.execute(
                    "SELECT * FROM users WHERE username = '" + uname + "'")
                user = mycursor.fetchall()
            except Exception as error:
                message = str(error)
        else:
            message = ""

        return render_template("updateUser.html", dogs=showDogs(), user=user, m=message)
    return redirect('login')


def showDogs():
    mycursor = DBManager().getCursor()
    un = session["USERNAME"]
    queryShowDogs = "select dog_id,name from dogs where username='" + un + "'"
    mycursor.execute(queryShowDogs)
    result = mycursor.fetchall()
    return result


@app.route("/updateUser/<dog_id>", methods=['POST', 'GET'])
def updateDog(dog_id):
    if request.method == 'POST':
        formDetails = request.form
        if 'delete' in formDetails:
            deleteDog(dog_id)
        elif 'adopt' in formDetails:
            adopted(dog_id)
    return redirect('/updateUser')


def deleteDog(dog_id):
    mycursor = DBManager().getCursor()
    queryDeleteDog = "DELETE FROM dogs WHERE dog_id =" + dog_id
    mycursor.execute(queryDeleteDog)
    DBManager().connection.commit() 
    queryDeleteDog = "DELETE FROM likes WHERE dog_id =" + dog_id
    mycursor.execute(queryDeleteDog)
    DBManager().connection.commit()
    return True
     

def adopted(dog_id):
    mycursor = DBManager().getCursor()
    mycursor.execute(
        "INSERT INTO adopted SELECT d.* FROM dogs AS d WHERE dog_id = " + dog_id)
    DBManager().connection.commit()
    deleteDog(dog_id)
    return True


#region chat_logic
def add_message_to_db(msg: Message) -> bool:
    message_id = None
    if msg.receiver and msg.content.strip() != '':
        mycursor = DBManager.getCursor()
        sql = "INSERT INTO messages (sender_username, receiver_username, content, sending_date, meeting_proposal) VALUES (%s, %s, %s, %s, %s)"
        val = (msg.sender, msg.receiver, msg.content, msg.date, msg.meeting_proposal)
        mycursor.execute('select * from messages where sender_username="' + msg.receiver + '" and receiver_username="' + msg.sender + '" order by sending_date Limit 1')
        last_massage= mycursor.fetchone()
        print(last_massage)
        # check if the last message was a meeting proposal and the owner replied yes
        if last_massage is not None and msg.content.lower() == 'yes' and last_massage[5] == 'True':
            mycursor.execute("select email from users where username='" + msg.sender + "'")
            owner_email = mycursor.fetchone()
            mycursor.execute("select email from users where username='" + msg.receiver + "'")
            username_email = mycursor.fetchone()
            # extract name place and time from the meeting proposal message
            matches = re.findall(r'Can I meet (\S+) in (\S+) in (\S+) at (.*?)\?\nYes/No', last_massage[3])[0]
            os.system('python meeting\\create_meeting.py "' + matches[0] +'" "' + matches[3] + '" ' + matches[1] + 'T' + matches[2] + ' ' + owner_email[0] + ' ' + username_email[0])
        try:
            mycursor.execute(sql, val)
            DBManager.connection.commit()
            message_id = mycursor.lastrowid
            print(f'inserted message with id {message_id}')
        except Exception as error:
            print(f'error in add_message_to_db: {str(error)}')
    return message_id


def get_all_chats(sender_username):
    view = []
    try:
        mycursor = DBManager.getCursor()
        mycursor.execute("SELECT d.username FROM dogs d " +
                            "INNER JOIN likes l ON l.dog_id = d.dog_id " +
                            "WHERE l.username=%(sender)s " +
                            "AND d.dog_id NOT IN (SELECT dog_id FROM adopted) " +
                            "AND d.username <> %(sender)s " +
                            "AND l.answer='yes'" + 
                            "UNION " +
                            "SELECT l.username FROM dogs d " +
                            "INNER JOIN likes l ON l.dog_id = d.dog_id " +
                            "WHERE d.username=%(sender)s " +
                            "AND l.username <> %(sender)s " +
                            "AND l.answer='yes'" +
                            "AND d.dog_id NOT IN (SELECT dog_id FROM adopted) " +
                        "ORDER BY 1 ASC", { 'sender': sender_username, })
        view = mycursor.fetchall()
        DBManager.closeConnection()
    except Exception as error:
        print(f'error in get_all_chats: {str(error)}')
    return view

def get_all_messages(sender, receiver):
    view = []
    try:
        mycursor = DBManager.getCursor()
        mycursor.execute("SELECT * FROM messages WHERE (sender_username = %(sender)s AND receiver_username = %(receiver)s) " +
                        "OR (receiver_username = %(sender)s AND sender_username = %(receiver)s)" +
                        "ORDER BY sending_date ASC", { 'sender': sender, 
                                                        'receiver': receiver})
        view = mycursor.fetchall()
        DBManager.closeConnection()
    except Exception as error:
        print(f'error in get_all_messages: {str(error)}')
    return view


def join_chat(chatRoom):
    uname = get_user_logged_in()
    if uname not in chatClients or chatClients[uname] != chatRoom:
        # leave last room before connecting to another
        if uname in chatClients:
            leave_room(chatClients[uname])
        
        chatClients[uname] = chatRoom
        join_room(chatRoom)
        print(uname + ' has entered the room ' + chatRoom) 


@app.route("/chat/<receiver_username>", methods=['GET', 'POST'])
@app.route("/chat/", defaults={'receiver_username':''})
def chat(receiver_username=None):
    username = get_user_logged_in()
    if username:
        chatsList = get_all_chats(username)
        return render_template('chat.html', chats=chatsList)
    return redirect('/login')


@app.route("/chat_messages/<receiver_username>", methods=['GET', 'POST'])
def chat_messages(receiver_username):
    messagesList = []
    username = get_user_logged_in()

    if username and receiver_username:
        chatsList = get_all_chats(username)

        # make sure chat exists before getting messages
        if receiver_username and (f'{receiver_username}',) in chatsList:
            messagesList = get_all_messages(username, receiver_username)
            return render_template('chatMessages.html', messages=messagesList)
    raise Exception(f'Failed when trying to fetch chat messages for {receiver_username}')


@socketio.on('connection')
def handle_connection(data):
    uname = get_user_logged_in()
    print(f'{uname} has connected')
    
@socketio.on('disconnect')
def handle_disconnect():
    uname = get_user_logged_in()
    print(f'{uname} has disconnected')


@socketio.on('join_chat')
def on_join(data):
    if data and 'receiver' in data:
        receiver_username = data['receiver']
        chatRoom = f'{request.sid}#{receiver_username}'
        join_chat(chatRoom)

@socketio.on('leave_chat')
def on_leave(data):
    uname = get_user_logged_in()
    if uname and uname in chatClients:
        del chatClients[uname]
    if uname and 'CHAT_ROOM' in session: 
        receiver_username = session['CHAT_ROOM']
        chatRoom = f'{request.sid}#{receiver_username}'
        leave_room(chatRoom)

        print(uname + ' has left the room ' + chatRoom)

@socketio.on('send_message')
def send_message(json, methods=['GET', 'POST']):
    print('received my event: ' + str(json))
    sender_username = get_user_logged_in()
    # check if there is a receiver for the message before sending
    #if 'CHAT_ROOM' in session:
    #  receiver_username = session.get('CHAT_ROOM', None)
    if sender_username in chatClients:
        receiver_username = chatClients[sender_username].split("#")[1]
        content = json['message']
        sending_date = datetime.now()
        sending_date_formated = sending_date.strftime('%Y-%m-%d %H:%M:%S')
                
        print(f'message: {content} from { sender_username } to { receiver_username }')
        
        # insert message to db
        msg = Message(sender_username, receiver_username, content, sending_date_formated, 'False')
        msg.id = add_message_to_db(msg)

        if msg.id:
            print(f'Message {msg.id} was inserted')

            # get template of message
            msgArray = [[msg.id, msg.sender, msg.receiver, msg.content, sending_date]]
            # approve message was sent to the client
            # if sender_username in chatClients and chatClients[sender_username].split("#")[1] == receiver_username:
            socketio.emit('message_received', render_template('chatMessages.html', messages=msgArray), room=chatClients[sender_username])

            # make sure receiver is in chat room with the sender
            if receiver_username in chatClients and chatClients[receiver_username].split("#")[1] == sender_username:
                socketio.emit('message_received', render_template('chatMessages.html', messages=msgArray, logged_in_user=msg.receiver), room=chatClients[receiver_username])
        else:
            print('insertion failed')
    else:
        print('chat room wasnt open with the receiver')
#endregion

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
     socketio.run(app, host='0.0.0.0', debug=True)
     pass
