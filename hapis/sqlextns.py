#---------------------------------------------------------------------------
# Various extensions to use with SQLAlchemy
#---------------------------------------------------------------------------
import decimal
import datetime
import sqlalchemy.orm

#---------------------------------------------------------------------------
# Simple pagination of either a query or a list-like thing
#---------------------------------------------------------------------------
def paginate(items, start, length):
    if isinstance(items, sqlalchemy.orm.query.Query):
        count = items.count()
        if start == "last-page":
            start = ((count - 1) // length) * length
        else:
            start = int(start)
        qry = items.slice(start, start+length)
        return (qry, count)
    else:
        count = len(items)
        if start == "last-page":
            start = ((count - 1) // length) * length
        else:
            start = int(start)
        items = items[start : start+length]
        return (items, count)

#---------------------------------------------------------------------------
#---------------------------------------------------------------------------
def expandQuery(statement, bind=None):
    """
    get a query, with values filled in, for debugging purposes *only*
    for security, you should always separate queries from their values
    please also note that this function is quite slow
    from http://stackoverflow.com/questions/5631078
    """
    if isinstance(statement, sqlalchemy.orm.Query):
        if bind is None:
            bind = statement.session.get_bind(
                    statement._mapper_zero_or_none()
            )
        statement = statement.statement
    elif bind is None:
        bind = statement.bind

    dialect = bind.dialect
    compiler = statement._compiler(dialect)
    class LiteralCompiler(compiler.__class__):
        def visit_bindparam(self, bindparam, within_columns_clause=False,
                            literal_binds=False, **kwargs):
            return super(LiteralCompiler, self).render_literal_bindparam(
                    bindparam, within_columns_clause=within_columns_clause,
                    literal_binds=literal_binds, **kwargs)
        def render_literal_value(self, value, type_):
            """Render the value of a bind parameter as a quoted literal.
            This is used for statement sections that do not accept bind
            paramters on the target driver/database.
            This should be implemented by subclasses using the quoting services
            of the DBAPI.
            """
            if isinstance(value, str):
                value = value.replace("'", "''")
                return "'%s'" % value
            elif value is None:
                return "NULL"
            elif isinstance(value, (float, int)):
                return repr(value)
            elif isinstance(value, decimal.Decimal):
                return str(value)
            elif isinstance(value, datetime.datetime):
                # custom render of datetime.datetime type for Oracle
                return "TO_DATE('%s','YYYY-MM-DD HH24:MI:SS')" % value.strftime("%Y-%m-%d %H:%M:%S")

            else:
                raise NotImplementedError(
                            "Don't know how to literal-quote value %r" % value)

    compiler = LiteralCompiler(dialect, statement)
    return str(compiler.process(statement))

#---------------------------------------------------------------------------
