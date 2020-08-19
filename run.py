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
import math


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/reviewsite"
mongo = PyMongo(app)


@app.template_filter("formatdatetime")  # 작성시간 구하기 함수
def form_datetime(value):
    if value is None:
        return" "
    now_tstamp = time.time()
    offset = datetime.fromtimestamp(now_tstamp) - datetime.utcfromtimestamp(now_tstamp)
    value = datetime.fromtimestamp(int(value) / 1000) + offset
    return value.strftime('%Y-%m-%d-%H-%M-%S')


@app.route("/list")
def list():
    # 페이지 값 (없을경우 기본값은 1)
    page = request.args.get("page", 1, type=int)
    # 한페이지당 몇개를 출력할지
    limit = request.args.get("limit", 3, type=int)
    board = mongo.db.board
    datas = board.find({}).skip((page - 1) * limit).limit(limit)  # 스킵 사용 페이지

    # 게시물 총 갯수
    tot_count = board.find({}).count()
    # 마지막 페이지의 수를 구함.
    last_page_num = math.ceil(tot_count / limit)

    # 페이지 블럭을 5개씩 보기
    block_size = 5
    # 현재 블럭의 위치.
    block_num = int((page - 1) / block_size)
    # 블럭의 시작 위치.
    block_start = int((block_size * block_num) + 1)
    block_last = math.ceil(block_start + (block_size - 1))
    return render_template(
        "list.html",
        datas=datas,
        limit=limit,
        page=page,
        block_start=block_start,
        block_last=block_last,
        last_page_num=last_page_num)


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
