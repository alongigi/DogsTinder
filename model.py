import pymysql

class DBManager():
    connection: pymysql.Connection = None

    @classmethod
    def getConnection(cls):
        return cls.connection
    
    @classmethod
    def getCursor(cls):
        if not cls.connection or not cls.connection.open:
            cls.connection = pymysql.connect("localhost", "root", "LoginPass@@12", "DogsTinder")
        return cls.connection.cursor()

    @classmethod
    def closeConnection(cls):
        if cls.connection and cls.connection.open:
            cls.connection.close()
   
class Message:
    def __init__(self, sender, receiver, content, date, meeting_proposal):
        self.id = None
        self.sender = sender
        self.receiver = receiver
        self.content = content
        self.date = date
        self.meeting_proposal = meeting_proposal

    def serialize(self) -> dict:
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'content': self.content,
            'date': self.date
        }