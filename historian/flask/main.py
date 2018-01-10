import json

from flask import Flask, render_template, request

from ..models import Visits, Urls

app = Flask(__name__)


@app.route('/')
def index():
    date_lt = request.args.get('date_lt', None)
    date_gt = request.args.get('date_gt', None)
    url_match = request.args.get('url_match', None)
    title_match = request.args.get('title_match', None)
    limit = request.args.get('limit', 25)
    start = request.args.get('start', 0)
    username = request.args.get('username', None)

    if limit:
        limit = int(limit)
    if start:
        start = int(start)

    hist = app.config['HISTORIES']

    will_paginate = False
    url_count = hist.get_url_count()
    if limit:
        if url_count > limit:
            will_paginate = True

    hist.get_urls(date_lt=date_lt, date_gt=date_gt, url_match=url_match, title_match=title_match, limit=limit,
                  start=start)

    user_list = hist.get_users()
    users = [u.name for u in user_list]
    user = list(filter(lambda u: u.name == username, user_list))[0] if username in users else None
    urls = hist.get_urls(username=username, date_lt=date_lt, date_gt=date_gt, url_match=url_match,
                         title_match=title_match, limit=limit, start=start)

    return render_template('index.html', hist=hist, date_lt=date_lt, date_gt=date_gt, url_match=url_match,
                           title_match=title_match, will_paginate=will_paginate, limit=limit, start=start,
                           url_count=url_count, users=users, current_user=user, urls=urls)


@app.route('/graph/<id>')
def graph(id):
    hist = app.config['HISTORIES']
    url = hist.get_url_by_id(id)
    print(url.id)

    return render_template('view_graph.html', hist=hist, url=url)


@app.route('/graph/<id>/json')
def graph_ajax(id):
    hist = app.config['HISTORIES']
    visits = set(Visits.select().where(Visits.url == id))
    data = []
    left = True
    visited = set()

    while left:
        visit = visits.pop()
        visited.add(visit)
        url = Urls.select().where(Urls.id == visit.url).get()
        data.append({
            "id": visit.id,
            "url_id": visit.url,
            "url": url.url,
            "url_title": url.title,
            "from": visit.from_visit,
        })

        if visit.from_visit:
            from_visit = visit.from_visit
            if from_visit not in visited:
                from_visit = Visits.select().where(Visits.id == from_visit).get()
                visits.add(from_visit)

        to = Visits.select().where(Visits.from_visit == visit.id)
        if len(to) > 0 and len(visits) < 50 and len(visited) < 50:
            for to_visit in to:
                if to_visit not in visited:
                    visits.add(to_visit)

        if len(visits) == 0:
            left = False

    return json.dumps(data)


@app.route('/user/')
def user_list():
    hist = app.config['HISTORIES']
    users = [user.username for user in hist.get_users()]
    return json.dumps(users)
