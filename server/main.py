from twilio.rest import Client
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import DataBase
import re
from random import choices

account_sid = ''
auth_token = ''
twilio_num = ''
client = Client(account_sid, auth_token)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-length', 0))
        data = self.rfile.read(length).decode()
        try:
            determineMessage(parse_qs(data)['Body'][0], parse_qs(data)['From'][0])
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
        except:
            rawPhone = parse_qs(data)['From'][0]
            a = '+1'
            b = rawPhone[1:4]
            c = rawPhone[6:9]
            d = rawPhone[10:14]
            finalPhone = a + b + c + d
            groupNum = determineMessage('new', finalPhone)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            web_content_template = '''
            <!DOCTYPE html>
            <head>
            <title>Raccoon</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://use.fontawesome.com/164ef8ddf8.js"></script>
            <link rel="stylesheet" href="http://raccoonpay.me/static/css/info.css">
            </head>
            <body>
            <div id="main">
            {}
            <a href="http://raccoonpay.me">
            <img id="logo" src="http://raccoonpay.me/static/imgs/logo.png">
            </a>
            </div>
            <script src="https://use.typekit.net/iwb0frs.js"></script>
            <script src="http://raccoonpay.me/static/js/info.js"></script>
            </body>
            '''
            if groupNum != 'ERRORONNEW':
                web_content = web_content_template.format('<p id="group-label">YOUR GROUP NUMBER IS</p><p id="group-number">' + str(groupNum) + '</p><p id="group-intro">Share this number with your friends and have them send to (949) 835-5128 within 10 minutes.</p>')
            else:
                web_content = web_content_template.format('<p id="group-intro">You are already in a group. Please check out that group before you create a new one.</p>')
            self.wfile.write(web_content.encode())

def send_sms(messageToSend, numToSend):
    message = client.messages.create(
        body = messageToSend,
        to = numToSend,
        from_ = twilio_num
    )

def generateCode():
    while True:
        Dights = [str(i) for i in range(10)]
        strnum = ''.join(choices(Dights, k = 6))
        if not DataBase.used(strnum):
            return strnum

def typeisint(target):
    try:
        int(target)
    except:
        return False
    else:
        return True

def determineMessage(receivedMessage: str, phoneNum: str):
    receivedMessage = receivedMessage.strip()
    if receivedMessage.lower() == 'new':
        groupNum = generateCode()
        if not DataBase.MakeNewGroup(phoneNum, groupNum):
            messageToSend = 'You are already in a group. Please check out that group before you create a new one.'
            send_sms(messageToSend, phoneNum)
            return 'ERRORONNEW'
        messageToSend = 'You have successfully created a group. The code of the group is ' + str(groupNum) + '. Share this code with your friends and have them send it to (949) 835-5128 within 10 minutes.'
        send_sms(messageToSend, phoneNum)
        return groupNum
    elif (typeisint(receivedMessage) and len(receivedMessage) == 6):
        if DataBase.AddMember(phoneNum, receivedMessage):
            messageToSend = 'You have successfully entered the group ' + str(receivedMessage) + '. To request money from this group, simply reply the amount of it.'
        else:
            messageToSend = 'Sorry, the group code you entered ({}) is invalid.'.format(receivedMessage)
        send_sms(messageToSend, phoneNum)
    elif re.match(r'^\$?(\d+(\.\d{1,2})?)$', receivedMessage) != None:
        messageToSend = 'We have got your split request of ${} in this group. All the friends in this group will be notified.'.format(receivedMessage)
        DataBase.AddTrans(phoneNum, re.match(r'^\$?(\d+(\.\d{1,2})?)$', receivedMessage).group(1))
        send_sms(messageToSend, phoneNum)
        receiver = DataBase.getMembers(phoneNum)
        receiver.remove(phoneNum)
        comfirm = '{} just requested a ${} bill split from the group. Reply \'N\' within 10 minutes to withdraw from the split.'.format(phoneNum, receivedMessage)
        for num in receiver:
            send_sms(comfirm, num)
    elif re.match(r'^\d+[+\-\*//]\d+([+\-\*//]\d+)*$', receivedMessage) != None:
        total = str(round(eval(receivedMessage), 2))
        messageToSend = 'We have got your split request of ${} in this group. All the friends in this group will be notified.'.format(total)
        DataBase.AddTrans(phoneNum, total)
        send_sms(messageToSend, phoneNum)
        receiver = DataBase.getMembers(phoneNum)
        receiver.remove(phoneNum)
        comfirm = '{} just requested a ${} bill split from the group. Reply \'N\' within 10 minutes to withdraw from the split.'.format(phoneNum, total)
        for num in receiver:
            send_sms(comfirm, num)
    elif receivedMessage.lower() == 'n':
        messageToSend = 'You have successfully quit from the last bill split.'
        if DataBase.Deny(phoneNum):
            send_sms(messageToSend, phoneNum)
        else:
            messageToSend = 'The 10-minute time limit has been exeeded and you are unable to quit from the last bill split.'
            send_sms(messageToSend, phoneNum)
    elif receivedMessage.lower() == 'checkout':
        result = DataBase.summary(phoneNum)
        if result == False:
            messageToSend = 'Your check out request is not accepted: only the creater of the group ({}) can make the check out request.'.format(DataBase.getMaster(phoneNum))
            send_sms(messageToSend, phoneNum)
        else:
            for payer, topay in result.items():
                messageToSend = 'User {} need pay to follwing person(s):\n'.format(payer)
                for receiver, amount in topay.items():
                    messageToSend += '{}: ${}\n'.format(receiver, amount)
                send_sms(messageToSend, payer)
            DataBase.clear(phoneNum)
            messageToSend = 'Group Deleted. See you next time!'
            send_sms(messageToSend, phoneNum)
    else:
        messageToSend = 'We are unable to recognize this command. To request money from this group, reply the amount of it.'
        send_sms(messageToSend, phoneNum)

if __name__ == '__main__':
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()
