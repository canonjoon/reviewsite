from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo

from datetime import datetime
from bson.objectid import ObjectId
from flask import abort
import time
from flask import redirect
from flask import url_for


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/reviewsite"
mongo = PyMongo(app)


@app.template_filter("formatdatetime")  # 작성시간 구하기 함수
def form_datetime(value):
    if value is None:
        return""
    now_tstamp = time.time()
    offset = datetime.fromtimestamp(now_tstamp) - datetime.utcfromtimestamp(now_tstamp)
    value = datetime.fromtimestamp(int(value) / 1000) + offset
    return value.strftime('%Y-%m-%d-%H-%M-%S')


@app.route("/view/<idx>")  # 팬시 스타일로 바꿈, 요즘 스타일임.
def board_view(idx):  # 팬시 스타일로 할 때,idx를 인자로 받아버림.
    # idx = request.args.get("idx") # 팬시 스타일로 바뀌면서 필요 없어짐
    if idx is not None:
        board = mongo.db.board
        data = board.find_one({"_id": ObjectId(idx)})

        if data is not None:
            result = {
                "id": data.get("_id"),
                "name": data.get("name"),
                "title": data.get("title"),
                "contents": data.get("contents"),
                "pubdate": data.get("pubdate"),
                "view": data.get("view"),

            }
            return render_template("view.html", result=result)
    return abort(400)


@app.route("/write", methods=["GET", "POST"])
def board_write():
    if request.method == "POST":
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")
        print(name, title, contents)

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)  # 기준시 밀리세컨드 * 1000, round로 반올림 

        board = mongo.db.board
        post = {
            "name": name,
            "title": title,
            "contents": contents,
            "pubdate": current_utc_time,
            "view": 0,
        }

        x = board.insert_one(post)
        x.inserted_id

        return redirect(url_for("board_view", idx=x.inserted_id))  # 리다이렉트(유알엘포로 board_view함수가 지정하는 주소로 이동)
    else:
        return render_template("write.html")


if __name__ == "__main__":
    app.run(debug=True, port=9000)  # host="0.0.0.0"으로 외부접속 가능하게... 현재는 에러남
