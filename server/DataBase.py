from time import time
import boto3
import hashlib
from collections import defaultdict
from itertools import combinations

def get(response):
    return 'Item' in response.keys()

def getMembers(start: str):
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Phone')
    response = table.get_item(
        Key = {
            'Number': start
        }
    )
    if not get(response):
        return []
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    root = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']
    return root['members']

def getMaster(start: str):
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Phone')
    response = table.get_item(
        Key = {
            'Number': start
        }
    )
    if not get(response):
        return []
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    root = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']
    return root['master']

def MakeNewGroup(master, code):
    hashcode = hashlib.sha256(master.encode()).hexdigest()
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Groups')
    response = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )
    if get(response):
        return False
    table.put_item(
        Item = {
            'Hash': hashcode,
            'master': master,
            'members': [master],
            'trans': [],
            'active': 0
        }
    )
    table = dynamodb.Table('Phone')
    table.put_item(
        Item = {
            'Number': master,
            'Group': hashcode
        }
    )
    table = dynamodb.Table('Code')
    table.put_item(
        Item = {
            'Code': code,
            'Group': hashcode,
            'Expire': int(time()) + 10 * 60
        }
    )
    return True

def AddMember(member, code: int) -> bool:
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Code')
    try:
        response = table.get_item(
            Key = {
                'Code': code
            }
        )
    except ClientError:
        return False
    if not get(response):
        return False
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    origin = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']['members']
    if member not in origin:
        origin.append(member)
    table.update_item(
        Key = {
            'Hash': hashcode
        },
        UpdateExpression = 'set members = :m',
        ExpressionAttributeValues = {
            ':m': origin
        }
    )
    table = dynamodb.Table('Phone')
    table.put_item(
        Item = {
            'Number': member,
            'Group': hashcode
        }
    )
    return True

def used(code: str) -> bool:
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Code')
    response = table.get_item(
        Key = {
            'Code': code
        }
    )
    return get(response)

def AddTrans(master: str, amount: str):
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Phone')
    response = table.get_item(
        Key = {
            'Number': master
        }
    )
    if not get(response):
        return False
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    root = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']
    origin = root['trans']
    origin.append(
        {
            'receiver': master,
            'payer': root['members'],
            'amount': amount
        }
    )
    table.update_item(
        Key = {
            'Hash': hashcode
        },
        UpdateExpression = 'set trans = :t, active = :a',
        ExpressionAttributeValues = {
            ':t': origin,
            ':a': int(time()) + 10 * 60
        }
    )
    return True

def Deny(master: str):
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Phone')
    response = table.get_item(
        Key = {
            'Number': master
        }
    )
    if not get(response):
        return False
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    root = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']
    if int(time()) >= root['active']:
        return False
    origin = root['trans']
    origin[-1]['payer'].remove(master)
    table.update_item(
        Key = {
            'Hash': hashcode
        },
        UpdateExpression = 'set trans = :t',
        ExpressionAttributeValues = {
            ':t': origin
        }
    )
    return True

def summary(master):
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Phone')
    response = table.get_item(
        Key = {
            'Number': master
        }
    )
    if not get(response):
        return False
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    root = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']
    if master != root['master']:
        return False
    trans = root['trans']
    actions = []
    for tran in trans:
        portion = len(tran['payer'])
        total = float(tran['amount'])
        for pay in tran['payer']:
            if pay != tran['receiver']:
                actions.append((pay, tran['receiver'], round(total / portion, 2)))
    members = getMembers(master)
    result = defaultdict(dict)
    for member in members:
        for payto in members:
            if payto != member:
                result[member][payto] = 0.0
    for action in actions:
        result[action[0]][action[1]] += action[2]
    combines = [tuple(i) for i in combinations(members, 2)]
    final = []
    for payer, receiver in combines:
        temp = 0.0
        temp += result[payer][receiver]
        temp -= result[receiver][payer]
        final.append((payer, receiver, temp))
    finale = []
    for payer, receiver, amount in final:
        if amount > 0:
            finale.append((payer, receiver, amount))
        elif amount < 0:
            finale.append((receiver, payer, -amount))
    finaldict = defaultdict(dict)
    for payer, receiver, amount in finale:
        finaldict[payer][receiver] = round(amount, 2)
    return finaldict

def clear(master):
    dynamodb = boto3.resource('dynamodb', region_name = 'us-west-1')
    table = dynamodb.Table('Phone')
    response = table.get_item(
        Key = {
            'Number': master
        }
    )
    if not get(response):
        return False
    hashcode = response['Item']['Group']
    table = dynamodb.Table('Groups')
    root = table.get_item(
        Key = {
            'Hash': hashcode
        }
    )['Item']
    members = root['members']
    table.delete_item(
        Key = {
            'Hash': hashcode
        }
    )
    table = dynamodb.Table('Phone')
    for i in members:
        table.delete_item(
            Key = {
                'Number': i
            }
        )