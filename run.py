from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo

from datetime import datetime
from bson.objectid import ObjectId
from flask import abort
import time
from datetime import timedelta
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from functools import wraps
import math


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/reviewsite"
app.config["SECRET_KEY"] = "abcd"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=1)
mongo = PyMongo(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("member_login", next_url=request.url))
        return f(*args, **kwargs)
    return decorated_function


@app.template_filter("formatdatetime")  # 작성시간 구하기 함수
def form_datetime(value):
    if value is None:
        return" "
    now_tstamp = time.time()
    offset = datetime.fromtimestamp(now_tstamp) - datetime.utcfromtimestamp(now_tstamp)
    value = datetime.fromtimestamp(int(value) / 1000) + offset
    return value.strftime('%Y-%m-%d-%H-%M-%S')


@app.route("/list")
def lists():
    # 페이지 값 (없을경우 기본값은 1)
    page = request.args.get("page", 1, type=int)
    # 한페이지당 몇개를 출력할지
    limit = request.args.get("limit", 5, type=int)

    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", type=str)
    if keyword is None:
        keyword = ""

    # 최종적으로 완성된 쿼리를 만들 변수
    query = {}
    # 검색어 상태를 추가할 리스트 변수
    search_list = []
    
    if search == 0:
        search_list.append({"title": {"$regex": keyword}})
        print(search_list)
    elif search == 1:
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 2:
        search_list.append({"title": {"$regex": keyword}})
        search_list.append({"contents": {"$regex": keyword}})
    elif search == 3:
        search_list.append({"name": {"$regex": keyword}})

    # 검색된게 한개라도 있을때 query 변수에  $or 리스트를 쿼리함.
    if len(search_list) > 0:
        query = {"$or": search_list}
    # print(query)

    board = mongo.db.board
    datas = board.find(query).skip((page - 1) * limit).limit(limit)  # 스킵 사용 페이지

    # 게시물 총 갯수
    tot_count = board.find(query).count()
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
        last_page_num=last_page_num,
        search=search,
        keyword=keyword)


@app.route("/view/<idx>")  # 팬시 스타일로 바꿈, 요즘 스타일임.
@login_required
def board_view(idx):  # 팬시 스타일로 할 때,idx를 인자로 받아버림.
    # idx = request.args.get("idx") # 팬시 스타일로 바뀌면서 필요 없어짐
    if idx is not None:
        page = request.args.get("page", 1, type=int)
        search = request.args.get("search", -1, type=int)
        keyword = request.args.get("keyword", type=str)
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
            return render_template("view.html", result=result,page=page,search=search,keyword=keyword)
    return abort(400)


@app.route("/write", methods=["GET", "POST"])
@login_required
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


@app.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        pass1 = request.form.get("pass", type=str)
        pass2 = request.form.get("pass2", type=str)

        if name =="" or email =="" or pass1 =="" or pass2 =="":
            flash("입력되지 않는 값이 있습니다")
            return render_template("join.html")
        if pass1 != pass2:
            flash("비밀번호가 일치하지 않습니다")
            return render_template("join.html")
        
        members = mongo.db.members
        cnt = members.find({"email": email}).count()
        if cnt > 0:
            flash("중복된 이메일이 있습니다.")
            return render_template("join.html")

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)       
        post = {
            "name": name,
            "email": email,
            "pass": pass1,
            "joindate": current_utc_time,
            "logintime": "",
            "logincount": 0,
        }

        members.insert_one(post)

        return ""
    else:
        return render_template("join.html")


@app.route("/login", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("pass")
        next_url = request.form.get("next_url")

        members = mongo.db.members
        data = members.find_one({"email": email})
        if data is None:
            flash("회원 정보가 없습니다.")
            return render_template("login.html")
        else:
            if data.get("pass") == password:
                session["email"] = email  # 로그인 성공시 세션에 임시로 저장. 
                session["name"] = data.get("name")
                session["id"] = str(data.get("_id"))
                session.permanent = True
                if next_url is not None:
                    return redirect(next_url)
                else:
                    return redirect(url_for("lists"))
            else:
                flash("비밀번호가 일치하지 않습니다")
                return render_template("login.html")

        return ""
    else:
        next_url = request.args.get("next_url", type=str)
        if next_url is not None:
            return render_template("login.html", next_url=next_url)
        else:
            return render_template("login.html")
  


if __name__ == "__main__":
    app.run(debug=True, port=9000)  # host="0.0.0.0"으로 외부접속 가능하게... 현재는 에러남
