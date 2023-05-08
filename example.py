output = str(
    b'username roy privilege 15 secret 5 $1$dBCf$BnIgKcvYOICKi6jxMDU.G0\r\nusername poio password 0 poio\r\n')
output = str(b'username roy privilege 15 secret 5 $1$XK37$R8iLSsJ4SF3buHOEmFReo1\\r\\nusername cisco privilege 15 password 0 cisco \\r\\nusername poio password 0 poio\\r\\n')
splitted_out_by_user = output.split("username")
user_list = []
for unformated_user in splitted_out_by_user:
    splited_unformated_user = unformated_user.split(" ")
    if len(splited_unformated_user)>1:
        user = splited_unformated_user[1]
        if splited_unformated_user[2] == "privilege":
            privilege = splited_unformated_user[3]
            password_type = splited_unformated_user[4]
        else:
            privilege = "None"
            password_type = splited_unformated_user[2]
        user_json = {
            "user": user,
            "privilege": privilege,
            "password_type": password_type
        }
        user_list.append(user_json)  

print(user_list)
