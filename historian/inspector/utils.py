def print_visit(visit, full=False):
    """
    :param historian.Visit visit:
    """
    print("Visit: ", visit.id)
    print("Timestamp: ", visit.visit_time)

    if full:
        print("Transition: ", visit.transition)
        print("From Visit: ", visit.from_visit_raw)
        print("Visit Duration: ", visit.visit_duration)


def print_url(url, full=False):
    """
    :param historian.Url url:
    """
    print("ID: ", url.id)
    print("Url: ", url.url)
    if url.title:
        print("Title: ", url.title)
    print("Visit Count: ", url.visit_count)
    print("Last Visit: ", url.latest_visit.id)

    if full:
        print("Typed Count: ", url.typed_count)
