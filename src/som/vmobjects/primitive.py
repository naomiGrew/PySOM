from som.vmobjects.abstract_object    import AbstractObject


class Primitive(AbstractObject):
    _immutable_fields_ = ["_invoke", "_is_empty", "_signature", "_holder",
                          "_universe"]
        
    def __init__(self, signature_string, universe, invoke, is_empty=False):
        AbstractObject.__init__(self)
        
        self._signature = universe.symbol_for(signature_string)
        self._invoke    = invoke
        self._is_empty  = is_empty
        self._holder    = None
        self._universe  = universe

    def get_universe(self):
        return self._universe

    def invoke(self, rcvr, args):
        inv = self._invoke
        return inv(self, rcvr, args)

    def invoke_void(self, rcvr, args):
        self.invoke(rcvr, args)

    def is_primitive(self):
        return True
    
    def is_invokable(self):
        """In the RPython version, we use this method to identify methods 
           and primitives
        """
        return True

    def get_signature(self):
        return self._signature

    def get_holder(self):
        return self._holder

    def set_holder(self, value):
        self._holder = value

    def is_empty(self):
        # By default a primitive is not empty
        return self._is_empty
    
    def get_class(self, universe):
        return universe.primitiveClass

    def __str__(self):
        return ("Primitive(" + self.get_holder().get_name().get_string() + ">>"
                + str(self.get_signature()) + ")")



def empty_primitive(signature_string, universe):
    """ Return an empty primitive with the given signature """
    return Primitive(signature_string, universe, _invoke, True)


def _invoke(ivkbl, rcvr, args):
    """ Write a warning to the screen """
    print "Warning: undefined primitive %s called" % ivkbl.get_signature()
