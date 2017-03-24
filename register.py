import requests
import json
import socket
import getopt
import sys
import getpass
import re
import utils

def register(server_config_file_name):
    try:
        f = open(server_config_file_name, "r")
        confs = json.load(f)
        f.close()
        return registerFromFile(server_config_file_name ,confs)
    except:
        return registerFromScratch(server_config_file_name)

def registerFromFile(server_config_file_name, confs):
    data = {}
    data["address"] = confs["address"]
    data["name"] = confs["name"]

    email = confs["email"]
    password = confs["password"]

    login_url = 'http://127.0.0.1:8000/login/'
    server_regist_url = 'http://127.0.0.1:8000/servers/'

    client = requests.session()

    try:
        # Retrieve the CSRF token first
        resp = client.get(login_url)  # sets cookie
        csrftoken = resp.cookies['csrftoken']
    except:
        print "ERROR: You don't have connection to the internet or the main server is down"
        return False

    headers = {'Accept':'application/json',
                'Content-Type':'application/json', 
                'X-CSRFToken':csrftoken}

    try:
        resp = client.get(server_regist_url+str(confs["id"])+"/", 
                                headers=headers, auth=(email, password))
    except:
        print "ERROR: You don't have connection to the internet or the main server is down"
        return False

    if resp.status_code == 200:
        f = open(server_config_file_name, "w")
        js = json.loads(resp.text)
        js["email"] = email
        js["password"] = password
        json.dump(js, f)
        f.close()
        print 'Server Info Retrieved Successfully'
        return True
    else:  
        try:
            resp = client.post(server_regist_url, 
                            data=json.dumps(data), 
                            headers=headers, auth=(email, password))
        except:
            print "ERROR: You don't have connection to the internet or the main server is down"
            return False

        if resp.status_code == 201:
            print 'Server Registed Successfully'
            return True
        else:
            js = json.loads(resp.text)
            if "address" in js.keys():
                print "ERROR ("+ str(resp.status_code)+"): "+str(js["address"][0])

            if "name" in js.keys():
                print "ERROR ("+ str(resp.status_code)+"): "+str(js["name"][0])

            if "detail" in js.keys():
                print "ERROR ("+ str(resp.status_code)+"): "+str(js["detail"][0])
            
            print "Please check if data on 'serverconf.json' file is correct."
            print "If you prefer you can delete that file to register from scratch."
            return False

def registerFromScratch(server_config_file_name):

    print "\nStarting Server Configuration from Scratch\n" 

    login_url = 'http://127.0.0.1:8000/login/'
    server_regist_url = 'http://127.0.0.1:8000/servers/'

    client = requests.session()

    try:
        # Retrieve the CSRF token first
        resp = client.get(login_url)  # sets cookie
        csrftoken = resp.cookies['csrftoken']
    except:
        print "ERROR: You don't have connection to the internet or the main server is down"
        return False
    
    EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")

    headers = {'Accept':'application/json',
                'Content-Type':'application/json', 
                'X-CSRFToken':csrftoken}

    data = {}
    reg_ok = False
    ip_ok = False
    name_ok = False
    cred_ok = False
    email_ok = False
    while not reg_ok:
        while not ip_ok:
            # ip_addr = raw_input('Enter your server IP address: ')
            # ip_addr = ip_addr.strip()
            ip_addr = utils.get_my_ip()

            if utils.validate_IPv4(ip_addr):
                data['address'] = ip_addr
                ip_ok = True
            else:
                print 'Invalid IP address'


        while not name_ok:
            name = raw_input('Choose your server name: ')
            name = name.strip()
            if name != "":
                data['name'] = name
                name_ok = True
            else:
                print "Name can't be blank"

        while not cred_ok:
            while not email_ok:
                email = raw_input('Enter your email address: ')
                email = email.strip()

                if not EMAIL_REGEX.match(email):
                    print 'Invalid email formatting. Try again.'
                else:
                    email_ok = True

            password = getpass.getpass(prompt='Enter your password: ')
            password = password.strip()

            cred_ok = True

        try:
            resp = client.post(server_regist_url, 
                            data=json.dumps(data), 
                            headers=headers, auth=(email, password))
        except:
            print "ERROR: You don't have connection to the internet or the main server is down"
            return False

        if resp.status_code == 201:
            print 'Server Registed Successfully'
            try:
                f = open(server_config_file_name, "w")
                js = json.loads(resp.text)
                js["email"] = email
                js["password"] = password
                json.dump(js, f)
                f.close()
                reg_ok = True
            except:
                print "ERROR: Couldn't create 'serverconf.json' file."
                sys.exit()
        else:
            js = json.loads(resp.text)
            if "address" in js.keys():
                print "ERROR ("+ str(resp.status_code)+"): "+str(js["address"][0])
                ip_ok = False

            if "name" in js.keys():
                print "ERROR ("+ str(resp.status_code)+"): "+str(js["name"][0])
                name_ok = False

            if "detail" in js.keys():
                print "ERROR ("+ str(resp.status_code)+"): "+str(js["detail"][0])
                email_ok = False
                cred_ok = False

    return True
    