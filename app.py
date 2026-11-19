import os
import requests
from flask import Flask, request, redirect, render_template, jsonify
import sqlite3

# 自动定位到当前文件夹
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 核心修改：判断是否在云端（Render），如果是，使用持久化硬盘路径 /data
if os.path.exists('/data'):
    DB_PATH = '/data/website_data.db'
    UPLOAD_FOLDER = '/data/images'
else:
    DB_PATH = os.path.join(BASE_DIR, 'website_data.db')
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static')

# 确保上传文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 强制绑定模板和静态文件夹（图片路径如果是云端，也指向挂载盘）
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=UPLOAD_FOLDER)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    for table in ['posts_index', 'posts_detail', 'posts_schedule', 'posts_rankings', 'posts_history', 'posts_contact']:
        conn.execute(f'''CREATE TABLE IF NOT EXISTS {table} 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      title TEXT, content TEXT)''')
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = sqlite3.connect(DB_PATH)
    posts = conn.execute("SELECT * FROM posts_index ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('index.html', posts=posts)


@app.route('/detail')
def detail():
    conn = sqlite3.connect(DB_PATH)
    posts = conn.execute("SELECT * FROM posts_detail ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('detail.html', posts=posts)


@app.route('/schedule')
def schedule():
    conn = sqlite3.connect(DB_PATH)
    posts = conn.execute("SELECT * FROM posts_schedule ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('schedule.html', posts=posts)


@app.route('/rankings')
def rankings():
    conn = sqlite3.connect(DB_PATH)
    posts = conn.execute("SELECT * FROM posts_rankings ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('rankings.html', posts=posts)


@app.route('/history')
def history():
    conn = sqlite3.connect(DB_PATH)
    posts = conn.execute("SELECT * FROM posts_history ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('history.html', posts=posts)


@app.route('/contact')
def contact():
    conn = sqlite3.connect(DB_PATH)
    posts = conn.execute("SELECT * FROM posts_contact ORDER BY id DESC").fetchall()
    conn.close()
    return render_template('contact.html', posts=posts)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        page = request.form['page']
        title = request.form['title']
        content = request.form['content']
        table = f"posts_{page}"

        conn = sqlite3.connect(DB_PATH)
        conn.execute(f"INSERT INTO {table} (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        conn.close()
        return redirect('/admin')

    conn = sqlite3.connect(DB_PATH)
    all_posts = {}
    for page in ['index', 'detail', 'schedule', 'rankings', 'history', 'contact']:
        all_posts[page] = conn.execute(f"SELECT * FROM posts_{page} ORDER BY id DESC").fetchall()
    conn.close()

    return render_template('admin_settings.html', all_posts=all_posts)


@app.route('/delete/<page>/<int:post_id>')
def delete(page, post_id):
    table = f"posts_{page}"
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"DELETE FROM {table} WHERE id = ?", (post_id,))
    conn.commit()
    conn.close()
    return redirect('/admin')


@app.route('/edit/<page>/<int:post_id>', methods=['GET', 'POST'])
def edit(page, post_id):
    table = f"posts_{page}"
    conn = sqlite3.connect(DB_PATH)

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        conn.execute(f"UPDATE {table} SET title=?, content=? WHERE id=?", (title, content, post_id))
        conn.commit()
        conn.close()
        return redirect('/admin')

    post = conn.execute(f"SELECT * FROM {table} WHERE id = ?", (post_id,)).fetchone()
    conn.close()

    return f"""
    <body style="background:#f4f5f7; font-family:'Microsoft YaHei'; padding:40px; color:#333;">
        <div style="max-width:500px; margin:0 auto; background:#fff; padding:30px; border-radius:10px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">
            <h2 style="border-bottom:2px solid #0056b3; padding-bottom:15px; margin-top:0;">✏️ 编辑内容</h2>
            <form method="POST">
                <input name="title" value="{post[1] if post[1] else ''}" placeholder="标题（不填则显示为纯文字）" style="width:100%; margin-bottom:15px; padding:12px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box;">
                <textarea name="content" rows="5" style="width:100%; margin-bottom:20px; padding:12px; border:1px solid #ccc; border-radius:4px; box-sizing:border-box;" required>{post[2]}</textarea>
                <button type="submit" style="background:#0056b3; color:#fff; padding:12px 20px; border:none; border-radius:4px; width:100%; cursor:pointer; font-size:16px;">保存修改</button>
            </form>
            <div style="text-align:center; margin-top:20px;">
                <a href="/admin" style="color:#666; text-decoration:none; font-size:15px;">取消并返回后台</a>
            </div>
        </div>
    </body>
    """


# ================= 能读取网站信息的 AI 聊天接口 =================
@app.route('/api/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')

    conn = sqlite3.connect(DB_PATH)
    all_posts = {}
    for page in ['index', 'detail', 'schedule', 'rankings', 'history', 'contact']:
        all_posts[page] = conn.execute(f"SELECT title, content FROM posts_{page} ORDER BY id DESC").fetchall()
    conn.close()

    context = "【系统指令】\n你现在是“猪头王第一届积分锦标赛”的官方 AI 客服助手。你的回答必须口语化、热情、简洁，绝对不能直接大段复制原文，要用自己的话总结。如果用户的问题在资料里找不到，直接回答“抱歉，目前赛事官网还没有相关记录哦”。\n\n"
    context += "【官网参考资料】\n"

    page_names = {'index': '主页动态', 'detail': '赛事详情', 'schedule': '比赛安排', 'rankings': '积分排名',
                  'history': '比赛记录', 'contact': '联系方式'}

    for page, posts in all_posts.items():
        if posts:
            context += f"=== {page_names[page]} ===\n"
            for post in posts:
                if post[0]:
                    context += f"- 标题：{post[0]}\n"
                context += f"- 内容：{post[1]}\n"

    try:
        # 用你之前跑通的免费接口（如果你申请了 Key，可以直接换掉这里）
        response = requests.post(
            "https://text.pollinations.ai/",
            json={
                "messages": [
                    {"role": "system", "content": context},
                    {"role": "user",
                     "content": f"用户问题：{user_message}\n（请根据上面的参考资料，用你自己的话简要回答，别照抄！）"}
                ]
            },
            timeout=20
        )

        reply_text = response.text

        if "【系统指令】" in reply_text or "参考资料" in reply_text:
            reply_text = "抱歉，我刚才走神了，请你换个问法再试一次~"

        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"reply": "AI 大脑过载了，请稍后再试！"})


# =======================================================

if __name__ == '__main__':
    init_db()
    # 上线时注释掉下面这行
    app.run(debug=True)