from flask import Flask , render_template , session , flash
from flask import request , redirect , url_for , jsonify
from flask_mail import Mail , Message
import pandas as pd
import os
from recommender import *
from connect import *


app = Flask(__name__)
app.secret_key = '1234'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'yaghuduk@gmail.com'
app.config['MAIL_PASSWORD'] = 'gnst suft ajuf ital'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

@app.route("/")
def home():
    return redirect("/login")

@app.route("/sign-up" , methods = ["POST" , "GET"])
def register():
    if "username" not in session:
        message = ""
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            t = 0
            file = open("users.txt" , "r+")
            for line in file:
                if username == line.strip().split(" ")[0]:
                    t += 1

            if t == 0:
                file.write(f"{username} {password}" + "\n")
                file.close()

                userInfo = {"username" : [username] ,
                            "password" : [password] ,
                            "profile photo" : ["profile.png"] ,
                            "email" : ["empty"] ,
                            "crop" : ["empty"] ,
                            "temperature" : ["empty"] ,
                            "humidity" : ["empty"]}

                newUser = open(f"{username}.csv" , "a")
                pd.DataFrame(userInfo).to_csv(newUser)
                newUser.close()

                return "<script>alert('Done! You can login now.');window.location.href = '/login';</script>"
            else:
                #return "<script>alert('Username already taken. Try another.');window.location.href = '/sign-up';</script>"
                message = "Username already taken. Try another."

        return render_template("sign-up.html" , message = message)
    else:
        return redirect("/profile")


@app.route("/login" , methods = ["POST" , "GET"])
def login():
    if "username" in session:
        return redirect("/profile")
    else:
        message = ""
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            file = open("users.txt")
            t = 0
            for line in file:
                if username == line.strip().split(" ")[0]:
                    t += 1
                    if password == line.strip().split(" ")[1]:
                        session["username"] = username
                        return redirect("/profile")
                    else:
                        message = "Invalid password."


            if t == 0:
                message = "You don't have an account. Try to sign up first."
            file.close()

        return render_template("login.html" , message = message)


@app.route("/panel" , methods = ["POST" , "GET"])
def panel():
    if "username" in session:
        df = pd.read_csv(f"{session['username']}.csv")
        data = pd.read_csv("data.csv")
        if df['crop'][0] == "empty":
            message = "There is no crop. Feel free to choose one."
            crops = pd.read_csv("data.csv")["Crop"]
            tempStatus = ""
            humStatus = ""
        else:
            crops = list(pd.read_csv("data.csv")["Crop"])
            crops.remove(df['crop'][0])
            message = f"The greenhouse contains {df['crop'][0]}. Feel free to change the crop."
            tempStatus = f"The desired temperature is {round(df['temperature'][0])}°C"
            humStatus = f"The desired humidity is {round(df['humidity'][0])}%"
            for i in range(len(data["Crop"])):
                if data["Crop"][i] == df['crop'][0]:
                    data = {"Nitrogen": round(data["Nitrogen"][i] , 2) ,
                    "Phosphorus" : round(data["Phosphorus"][i],2) ,
                    "Potassium" : round(data["Potassium"][i] , 2) ,
                    "pH value" : round(data["pH_Value"][i] , 2)}
                    break

        return render_template("panel.html" , message = message , tempStatus = tempStatus , humStatus = humStatus , crops = crops , df=df , data = data)
    else:
        return redirect("/login")


@app.route("/apply", methods=["POST", "GET"])
def apply():
    if "username" in session:
        df = pd.read_csv(f"{session['username']}.csv")
        data = pd.read_csv("data.csv")
        if request.method == "POST":
            try:
                crop = request.form["crops"]
                df["crop"][0] = crop
                temp, humidity = 0 , 0
                for i in range(len(data["Crop"])):
                    if data["Crop"][i] == crop:
                        temp = data["Temperature"][i]
                        humidity = data["Humidity"][i]
                        break
                df["temperature"][0] = temp
                df["humidity"][0] = humidity
                df.to_csv(f"{session['username']}.csv")

                thread = threading.Thread(target=send_data , args = (f"{temp},{humidity}\r\n" , "ws://192.168.43.49:81"))
            except:
                return redirect("/panel")

        return redirect("/panel")

    else:
        return redirect("/login")

@app.route("/recommender" , methods = ["GET" , "POST"])
def recommender():
    if "username" in session:
        result = "empty"
        data = ""
        if request.method == "POST":
            df = pd.read_csv('dataset.csv')
            data = pd.read_csv("data.csv")

            temp = request.form["temperature"]
            humidity = request.form["humidity"]
            rain = request.form["rainfall"]

            wanted_columns = ['Temperature', 'Humidity', 'Rainfall' , 'Crop']
            df_selected = df[wanted_columns]
            test = pd.DataFrame([[float(temp) , float(humidity) , float(rain)]])

            result , neigh = knn(df_selected , test , 3)
            for i in range(len(data["Crop"])):
                if data["Crop"][i] == result:
                    data = {"Nitrogen": round(data["Nitrogen"][i] , 2) ,
                    "Phosphorus" : round(data["Phosphorus"][i],2) ,
                    "Potassium" : round(data["Potassium"][i] , 2) ,
                    "pH value" : round(data["pH_Value"][i] , 2)}
                    break

            return render_template("recommender.html" , result = result , data = data)

        return render_template("recommender.html" , result = result , data = data)
    else:
        return redirect("/login")

@app.route("/profile" , methods = ["POST" , "GET"])
def profile():
    if "username" in session:
        df = pd.read_csv(f"{session['username']}.csv")
        profilePhoto = f"static/{df['profile photo'][0]}"
        email = df["email"][0]
        if request.method == "POST":
            if request.files["file"].filename != "":
                f = request.files["file"]
                f.save(f"static/{session['username']}.png")
                df["profile photo"][0] = f"{session['username']}.png"
                df.to_csv(f"{session['username']}.csv")
            if request.form["newpass"] != "" and request.form["newpass"] == request.form["secondnewpass"]:
                df["password"][0] = request.form["newpass"]
                df.to_csv(f"{session['username']}.csv")
                with open("users.txt" , "r") as file:
                    inputFilelines = file.readlines()
                    with open("users.txt" , "w") as file:
                        for line in inputFilelines:
                            if line.strip().split(" ")[0] != session["username"]:
                                file.write(line)
                file.close()
                file = open("users.txt" , "a+")
                file.write(f"{df['username'][0]} {request.form['newpass']}" + "\n")
                file.close()

            if request.form["email"] != "":
                df["email"][0] = request.form["email"]
                df.to_csv(f"{session['username']}.csv")

            if request.form["newpass"] != "" and request.form["newpass"] != request.form["secondnewpass"]:
                return "<script>alert('Your passwords are not the same');window.location.href = '/profile';</script>"

            return redirect("/profile")
        return render_template("profile.html" , profilePhoto = profilePhoto , email = email)
    else:
        return redirect("/logout")

@app.route("/remove-photo")
def removePhoto():
    if "username" in session:
        df = pd.read_csv(f"{session['username']}.csv")
        if df["profile photo"][0] != "profile.png":
            os.remove(f"static/{df['profile photo'][0]}")
            df["profile photo"][0] = "profile.png"
            df.to_csv(f"{session['username']}.csv")
        return redirect("/profile")

    else:
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/delete-account")
def delete():
    if "username" in session:
        df = pd.read_csv(f"{session['username']}.csv")
        if df["profile photo"][0] != "profile.png":
            os.remove(f"static/{session['username']}.png")
        os.remove(f"{session['username']}.csv")
        with open("users.txt" , "r") as file:
            inputFilelines = file.readlines()
            with open("users.txt" , "w") as file:
                for line in inputFilelines:
                    if line.strip().split(" ")[0] != session["username"]:
                        file.write(line)

        session.clear()
        file.close()
        return "<script>alert('Your account has been deleted successfully');window.location.href = '/login';</script>"
    else:
        return redirect(url_for("login"))


@app.route("/recovery" , methods = ["GET" , "POST"])
def recovery():
    if "username" not in session:
        message = ""
        if request.method == "POST":
            email = request.form["email"]
            file = open("users.txt")
            t = 0
            users = []
            for line in file:
                users.append(f"{line.strip().split(' ')[0]}.csv")
                if line.strip().split(" ")[0] == email:
                        t = 1
                        msg = Message('Restore your account', sender = 'yaghuduk@gmail.com', recipients = [email])
                        msg.body = f"Your username is {line.strip().split(' ')[0]} and your password is {line.strip().split(' ')[1]}. Keep them safe."
                        mail.send(msg)
                        return "<script>alert('We sent you an email. Check it and login to your account');window.location.href = '/login';</script>"

                if t == 0:
                    count = 0
                    for user in users:
                        df = pd.read_csv(user)
                        if df["email"][0] == email:
                            count = 1
                            msg = Message('Restore your account', sender = 'yaghuduk@gmail.com', recipients = [email])
                            msg.body = f"Your username is {df['username'][0]} and your password is {df['password'][0]}. Keep them safe."
                            mail.send(msg)
                            break

                    if count == 0:
                        message = "There are no accounts created with this email."

                    else:
                        return "<script>alert('We sent you an email. Check it and login to your account');window.location.href = '/login';</script>"

        return render_template("recovery.html" , message = message)

    else:
        return redirect(url_for("panel"))
