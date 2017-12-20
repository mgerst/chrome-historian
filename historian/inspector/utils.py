from terminaltables import AsciiTable


def print_visit(visit, full=False):
    """
    :param historian.Visit visit:
    """
    rows = []
    rows.append(['Visit', visit.id])
    rows.append(['Timestamp', visit.visited])
    rows.append(['URL (ID)', visit.url])

    if full:
        rows.append(['URL (FULL)', visit.url_obj.url])
        rows.append(['Transition Type', visit.transition_core])
        rows.append(['Transition Flags', visit.transition_qualifier])
        rows.append(['From Visit', visit.from_visit])
        rows.append(['Visit Duration', visit.visit_duration])

    table = AsciiTable(rows)
    table.inner_heading_row_border = False
    print(table.table)


def print_url(url, full=False):
    """
    :param historian.Url url:
    """
    rows = []
    rows.append(['ID', url.id])
    rows.append(['Url', url.url])
    if url.title:
        rows.append(['Title', url.title])
    rows.append(['Visit Count', url.visit_count])
    rows.append(['Last Visit', url.last_visit])

    if full:
        rows.append(['Typed Count', url.typed_count])
    table = AsciiTable(rows)
    table.inner_heading_row_border = False
    print(table.table)
