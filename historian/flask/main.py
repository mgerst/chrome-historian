import json

from flask import Flask, render_template, request

from historian.history import History

app = Flask(__name__)


@app.route('/')
def index():
    date_lt = request.args.get('date_lt', None)
    date_gt = request.args.get('date_gt', None)
    url_match = request.args.get('url_match', None)
    title_match = request.args.get('title_match', None)

    hist = History(app.config['HISTORIES'])
    hist.get_urls(date_lt=date_lt, date_gt=date_gt, url_match=url_match, title_match=title_match)

    return render_template('index.html', hist=hist, date_lt=date_lt, date_gt=date_gt, url_match=url_match,
                           title_match=title_match)


@app.route('/graph/<id>')
def graph(id):
    hist = History(app.config['HISTORIES'])
    url = hist.get_url_by_id(id)

    return render_template('view_graph.html', hist=hist, url=url)


@app.route('/graph/<id>/json')
def graph_ajax(id):
    hist = History(app.config['HISTORIES'])
    url = hist.get_url_by_id(id)
    visits = set(url.visits)
    data = []
    left = True
    visited = set()

    while left:
        visit = visits.pop()
        visited.add(visit)
        data.append({
            "id": visit.id,
            "url_id": visit.url_id,
            "url": visit.url.url,
            "url_title": visit.url.title,
            "from": visit.from_visit_raw,
        })

        if visit.from_visit_raw:
            from_visit = visit.from_visit
            if from_visit not in visited:
                visits.add(from_visit)

        to = visit.to_visit
        if len(to) > 0 and len(visits) < 50 and len(visited) < 50:
            for to_visit in to:
                if to_visit not in visited:
                    visits.add(to_visit)

        if len(visits) == 0:
            left = False

    return json.dumps(data)
