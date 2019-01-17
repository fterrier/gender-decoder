from flask import Flask
from flask import render_template, redirect, request
from wtforms.validators import ValidationError
import datetime
from app import app, db
from app.forms import JobAdForm
from app.models import JobAd
from app.text import Text

@app.route('/', methods=['GET', 'POST'])
def home():
    form = JobAdForm()
    if request.method == "POST" and form.validate_on_submit():
        text = Text(form.texttotest.data)
        ad = JobAd(text, form.name.data, form.company.data, form.email.data)

        return redirect('results/{0}'.format(ad.hash))
    return render_template('home.html', form=form)


@app.route('/results/<ad_hash>')
def results(ad_hash):
    job_ad = JobAd.query.get_or_404(ad_hash)
    masculine_coded_words, feminine_coded_words = job_ad.list_words()
    return render_template('results.html', job_ad=job_ad,
        masculine_coded_words=masculine_coded_words,
        feminine_coded_words=feminine_coded_words)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
