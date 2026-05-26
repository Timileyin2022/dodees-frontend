from flask import Flask, request, render_template, jsonify, redirect, session, Response
import csv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from io import StringIO

app = Flask(__name__)
app.secret_key = "supersecretkey"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dodees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# WAITLIST MODEL
class Waitlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))

# Contact MODEL
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    message = db.Column(db.Text)

# Investor MODEL
class Investor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    company = db.Column(db.String(120))

# FAQ MODEL
class FAQ(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Text, nullable=False)
    helpful = db.Column(db.Integer, default=0)
    not_helpful = db.Column(db.Integer, default=0)

#SEARCH LOG MODEL
class SearchLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    search_text = db.Column(db.String(255))


#____________PAGE ROUTE_______________
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact_page():
    return render_template("contact.html")

@app.route("/investors")
def investors_page():
    return render_template("investors.html")
    
@app.route("/faq")
def faq():
    return render_template("faq.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/payment_terms")
def payment_terms():
    return render_template("payment_terms.html")

@app.route("/safety")
def safety():
    return render_template("safety.html")

@app.route("/guidelines")
def guidelines():
    return render_template("guidelines.html")

@app.route("/ai_features")
def ai_features():
    return render_template("ai_features.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/export-waitlist")
def export_waitlist():

    users = Waitlist.query.all()

    def generate():

        data = []

        data.append("ID,Name,Email,Phone\n")
        for user in users:
            data.append(
                f"{userid}, {user.name}, {user.email}, {user.phone}\n"
            )
        return "".join(data)
    return Response(generate(), mimetype="text/csv",
        headers={"Content-Disposition":"attachment;filename=waitlist.csv"})

@app.route("/delete/<table>/<int:id>")
def delete(table, id):

    models = {
        "waitlist": Waitlist,
        "contact": Contact,
        "investors": Investor
    }
    
    model = models.get(table)

    if not model:
        return "Invalid table"

    item = model.query.get(id)

    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect("/admin")

@app.route("/faq-feedback/<int:id>", methods=["POST"])
def faq_feedback(id):

    faq = FAQ.query.get_or_404(id)

    data = request.get_json()

    action = data.get("action")

    if action == "helpful":
        faq.helpful += 1

    elif action == "not_helpful":
        faq.not_helpful += 1

    db.session.commit()

    return jsonify({
        "message":"Feedback Saved"
    })

@app.route("/faq_suggestions")
def faq_suggestions():

    suggestions = FAQ.query.order_by(
        FAQ.helpful.desc()
    ).limit(5).all()

    return jsonify([
        {
            "question": faq.question,
            "helpful": faq.helpful
        }
        for faq in suggestions
    ])

@app.route("/debug-search")
def debug_search():

    logs = SearchLog.query.all()

    output = []

    for log in logs:
        output.append(log.search_text)
    return jsonify(output)


@app.route("/add_faq", methods=["POST"])
def add_faq():

    question = request.form.get("question")
    answer = request.form.get("answer")

    new_faq = FAQ(question=question, answer=answer)

    db.session.add(new_faq)
    db.session.commit()

    return redirect("/admin")

@app.route("/login", methods=["GET", "POST"])
def login():

    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin123":
            session["admin"] = True
            session["admin_username"] = username
            return redirect("/admin")
        else:
            error = "Invaild username or password"
    return render_template("login.html", error=error)

#___________FAQ ROUTE_______________
@app.route("/faqs")
def faqs():
    all_faqs = FAQ.query.all()

    return jsonify([
        {
            "id": f.id,
            "question": f.question,
            "answer": f.answer,
            "helpful": f.helpful,
            "not_helpful": f.not_helpful
        }
        for f in all_faqs
    ])

@app.route("/edit_faq/<int:id>", methods=["GET", "POST"])
def edit_faq(id):
    faq = FAQ.query.get_or_404(id)

    if request.method == "POST":
        faq.question = request.form.get("question")
        faq.answer = request.form.get("answer")

        db.session.commit()
        return redirect("/admin")

    return render_template("edit_faq.html", faq=faq)

@app.route("/delete_faq/<int:id>")
def delete_faq(id):

    faq = FAQ.query.get(id)

    if faq:

        db.session.delete(faq)
        db.session.commit()

    return redirect("/admin")

@app.route("/track_search", methods=["POST"])
def track_search():

    data = request.json

    log = SearchLog(query=data.get("query"))
    db.session.add(log)
    db.session.commit()

    return jsonify({"status":"ok"})

#____________LOG SEARCH________________
@app.route("/log-search", methods=["POST"])
def log_search():

    data = request.get_json()
    query = data.get("query")

    if query:
        log = SearchLog(
            search_text=query
        )

        db.session.add(log)
        db.session.commit()

    return jsonify({"message": "Search logged"})

#____________DOWNLOAD WAITLIST__________
@app.route("/download_waitlist")
def download_waitlist():

    output = StringIO()

    writer = csv.writer(output)

    # HEADER
    writer.writerow([
        "Name",
        "Email",
        "Phone Number"
    ])

    waitlist = Waitlist.query.all()

    for user in waitlist:
        writer.writerow([
            user.name,
            user.email,
            user.phone
        ])

    output.seek(0)

    return Response(
        output,
        mimetype="text/csv",
        headers={
            "Content-Disposition":
            "attachment;filename=waitlist.csv"
        }
    )


#____________ADMIN PAGE____________
@app.route("/admin")
def admin():

    if not session.get("admin"):
        return redirect("/login")

    waitlist = Waitlist.query.all()
    all_contacts = Contact.query.all()
    all_investors = Investor.query.all()
    faqs = FAQ.query.all()
    
    top_searches = db.session.query(
        SearchLog.search_text,
        func.count(SearchLog.id)
    ).group_by(
        SearchLog.search_text
    ).order_by(
        func.count(SearchLog.id).desc()
    ).all()

    return render_template(
        "admin.html",
        waitlist=waitlist,
        contacts=all_contacts,
        investors=all_investors,
        faqs=faqs,

        total_waitlist=Waitlist.query.count(),
        total_contact=Contact.query.count(),
        total_investors=Investor.query.count(),

        top_searches=top_searches
    )


with app.app_context():

    db.create_all()

    # ADD SAMPLE FAQ IF DATABASE IS EMPTY
    if FAQ.query.count() == 0:
        faq1 = FAQ(
            question="What is Dodees?",
            answer="Dodees is a video-first dating platform."
        )

        faq2 = FAQ(
            question="Is Dodees free?",
            answer="Yes, Dodees offers free access."
        )

        faq3 = FAQ(
            question="How does matching work?",
            answer="User connect through video profiles and interests."
        )

        db.session.add(faq1)
        db.session.add(faq2)
        db.session.add(faq3)

        db.session.commit()

        print("Sample FAQs added successfully")

#____________WAITLIST ROUTE______________
@app.route("/api/waitlist", methods=["POST"])
def waitlist_api():

    new_user = Waitlist(
        name=request.form.get("name"),
        email=request.form.get("email"),
        phone=request.form.get("phone")
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "Successfully joined waitlist"
    })

@app.route("/api/contact", methods=["POST"])
def contact_api():

    new_contact =Contact(
        name=request.form.get("name"),
        email=request.form.get("email"),
       message=request.form.get("message")
    )

    db.session.add(new_contact)
    db.session.commit()

    return jsonify({
        "message": "Message received"
    })

#____________INVESTOR ROUTE______________
@app.route("/api/investors", methods=["POST"])
def investors_api():

    new_investor = Investor(
        name=request.form.get("name"),
        email=request.form.get("email"),
        company=request.form.get("company")
    )

    db.session.add(new_investor)
    db.session.commit()

    return jsonify({
        "message": "Investor inquiry received"
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)