# ------------------------------------------------------------------------------
# Taurus Mill Factory, makes Mills to make objects of some Cls
# ------------------------------------------------------------------------------
# TODO: compare with https://github.com/rebeccaframework/rebecca.sqla
from .security import Root
from . import models

import logging
log = logging.getLogger(__name__)

def MillFactory(Cls):
    def mill_init(self, request):
        self.request = request
    def mill_getitem(self, objId):
        log.debug("{}Mill.__getitem__ {}".format(Cls.__name__, objId))
        objName = Cls.__name__.lower()
        try:
            obj = Cls.getById(int(objId))
        except (TypeError, ValueError):
            obj = None
        if obj:
            log.debug(" Found {} {} for id {}".format(objName, obj, objId))
        else:
            log.debug(" {}#{} not found".format(objName, objId))
        return obj
    Mill = type("{}Mill".format(Cls.__name__), (Root,),
                {'__init__'   : mill_init,
                 '__getitem__': mill_getitem})
    return Mill

OrderMill    = MillFactory(models.Order)
StreamMill   = MillFactory(models.Stream)
TrdSpecMill  = MillFactory(models.TradeSpecificStream)
UserMill     = MillFactory(models.User)
LinkMill     = MillFactory(models.CompanyLink)
CompanyMill  = MillFactory(models.Company)
TpcMill      = MillFactory(models.TradedProdCompliance)
SpecMill     = MillFactory(models.TradedProdSpec)
