#-------------------------------------------------------------------------------
# Hapis Interfaces
# ------------------------------------------------------------------------------
from zope.interface import Interface
from zope.interface import Attribute

class IOrderMatch(Interface):
    """
    An object that can be used to match against orders
    (Used by OrderBroker)
    """
    matchbuy      = Attribute("Match buy orders")
    matchsell     = Attribute("Match sell orders")
    product       = Attribute("Product to match")
    compliance    = Attribute("Compliance to match (no compliance means "
                              "sell orders must have no compliance, "
                              "buy orders can have any)")
    productdesc   = Attribute("Product+compliance description")
    dlvyperiod    = Attribute("Delivery period to match")
    fromcountries = Attribute("List of countries the order can be from")
    tocountries   = Attribute("List of countries the order must be to")

