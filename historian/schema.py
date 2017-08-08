import graphene
from graphene import relay
from graphene_sqlalchemy import SQLAlchemyObjectType, SQLAlchemyConnectionField
from .models import db_session, User as UserModel, Url as UrlModel, Visit as VisitModel


class Visit(SQLAlchemyObjectType):
    class Meta:
        model = VisitModel
        interfaces = (relay.Node,)


class Url(SQLAlchemyObjectType):
    class Meta:
        model = UrlModel
        interfaces = (relay.Node,)


class User(SQLAlchemyObjectType):
    class Meta:
        model = UserModel

    url = graphene.List(Url, url=graphene.String(required=True))

    def resolve_url(self, args, context, info):
        query = Url.get_query(context)

        url = args.get('url')

        return query.filter_by(url=url).all()


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    users = graphene.List(User, username=graphene.String(), id=graphene.Int())
    url = graphene.List(Url, username=graphene.String(), id=graphene.Int(), localId=graphene.Int())
    urls = SQLAlchemyConnectionField(Url, username=graphene.String(), visit_before=graphene.String(),
                                     visit_after=graphene.String())
    visit = graphene.List(Visit)
    visits = SQLAlchemyConnectionField(Visit)

    def resolve_user(self, args, context, info):
        query = User.get_query(context)

        id = args.get('id', None)
        if id:
            return [query.get(id)]

        username = args.get('username', None)
        if username:
            query = query.filter_by(username=username)

        return query.all()

    def resolve_urls(self, args, context, info):
        query = Url.get_query(context)

        username = args.get('username', None)
        if username:
            query = query.filter(UrlModel.user.has(username=username))

        visit_before = args.get('visit_before', None)
        if visit_before:
            query = query.filter(UrlModel.last_visit_time < int(visit_before))

        visit_after = args.get('visit_after', None)
        if visit_after:
            query = query.filter(UrlModel.last_visit_time > int(visit_after))

        return query.all()

    def resolve_url(self, args, context, info):
        query = Url.get_query(context)

        username = args.get('username', None)
        if username:
            query = query.filter(UrlModel.user.has(username=username))

        return query.all()

    def resolve_visit(self, args, context, info):
        query = Visit.get_query(context)

        return query.all()


schema = graphene.Schema(query=Query)
