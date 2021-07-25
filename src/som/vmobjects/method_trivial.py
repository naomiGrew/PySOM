from rlib.jit import elidable_promote, unroll_safe
from som.interpreter.ast.frame import FRAME_AND_INNER_RCVR_IDX
from som.interpreter.bc.frame import stack_pop_old_arguments_and_push_result
from som.interpreter.send import lookup_and_send_2

from som.vmobjects.method import AbstractMethod


@unroll_safe
def determine_outer_self(rcvr, context_level):
    outer_self = rcvr
    for _ in range(0, context_level):
        outer_self = outer_self.get_from_outer(FRAME_AND_INNER_RCVR_IDX)
    return outer_self


class AbstractTrivialMethod(AbstractMethod):
    def get_number_of_locals(self):  # pylint: disable=no-self-use
        return 0

    def get_maximum_number_of_stack_elements(self):  # pylint: disable=no-self-use
        return 0

    def set_holder(self, value):
        self._holder = value

    @elidable_promote("all")
    def get_number_of_arguments(self):
        return self._signature.get_number_of_signature_arguments()

    @elidable_promote("all")
    def get_number_of_signature_arguments(self):
        return self._signature.get_number_of_signature_arguments()


class LiteralReturn(AbstractTrivialMethod):
    _immutable_fields_ = ["_value"]

    def __init__(self, signature, value):
        AbstractTrivialMethod.__init__(self, signature)
        self._value = value

    def invoke_1(self, _rcvr):
        return self._value

    def invoke_2(self, _rcvr, _arg1):
        return self._value

    def invoke_3(self, _rcvr, _arg1, _arg2):
        return self._value

    def invoke_n(self, stack, stack_ptr):
        return stack_pop_old_arguments_and_push_result(
            stack,
            stack_ptr,
            self._signature.get_number_of_signature_arguments(),
            self._value,
        )


class GlobalRead(AbstractTrivialMethod):
    _immutable_fields_ = ["_assoc?", "_global_name", "_context_level", "universe"]

    def __init__(self, signature, global_name, context_level, universe):
        AbstractTrivialMethod.__init__(self, signature)
        self._assoc = None
        self._global_name = global_name
        self._context_level = context_level

        self.universe = universe

    def invoke_1(self, rcvr):
        if self._assoc is not None:
            return self._assoc.value

        if self.universe.has_global(self._global_name):
            self._assoc = self.universe.get_globals_association(self._global_name)
            return self._assoc.value

        return lookup_and_send_2(
            determine_outer_self(rcvr, self._context_level),
            self._global_name,
            "unknownGlobal:",
        )

    def invoke_2(self, rcvr, _arg1):
        return self.invoke_1(rcvr)

    def invoke_3(self, rcvr, _arg1, _arg2):
        return self.invoke_1(rcvr)

    def invoke_n(self, stack, stack_ptr):
        num_args = self._signature.get_number_of_signature_arguments()
        rcvr = stack[stack_ptr - (num_args - 1)]
        value = self.invoke_1(rcvr)
        return stack_pop_old_arguments_and_push_result(
            stack,
            stack_ptr,
            num_args,
            value,
        )


class FieldRead(AbstractTrivialMethod):
    _immutable_fields_ = ["_field_idx", "_context_level"]

    def __init__(self, signature, field_idx, context_level):
        AbstractTrivialMethod.__init__(self, signature)
        self._field_idx = field_idx
        self._context_level = context_level

    def invoke_1(self, rcvr):
        if self._context_level == 0:
            return rcvr.get_field(self._field_idx)

        outer_self = determine_outer_self(rcvr, self._context_level)
        return outer_self.get_field(self._field_idx)

    def invoke_2(self, rcvr, _arg1):
        return self.invoke_1(rcvr)

    def invoke_3(self, rcvr, _arg1, _arg2):
        return self.invoke_1(rcvr)

    def invoke_n(self, stack, stack_ptr):
        num_args = self._signature.get_number_of_signature_arguments()
        rcvr = stack[stack_ptr - (num_args - 1)]
        value = self.invoke_1(rcvr)
        return stack_pop_old_arguments_and_push_result(
            stack,
            stack_ptr,
            num_args,
            value,
        )


class FieldWrite(AbstractTrivialMethod):
    _immutable_fields_ = ["_field_idx", "_arg_idx"]

    def __init__(self, signature, field_idx, arg_idx):
        AbstractTrivialMethod.__init__(self, signature)
        self._field_idx = field_idx
        self._arg_idx = arg_idx

    def invoke_1(self, _rcvr):
        raise NotImplementedError(
            "Not supported, should never be called. We need an argument"
        )

    def invoke_2(self, rcvr, arg1):
        rcvr.set_field(self._field_idx, arg1)
        return rcvr

    def invoke_3(self, rcvr, arg1, arg2):
        if self._arg_idx == 1:
            return self.invoke_2(rcvr, arg1)
        return self.invoke_2(rcvr, arg2)

    def invoke_n(self, stack, stack_ptr):
        num_args = self._signature.get_number_of_signature_arguments()
        rcvr = stack[stack_ptr - (num_args - 1)]
        arg = stack[stack_ptr - (num_args - self._arg_idx)]
        self.invoke_2(rcvr, arg)
        return stack_pop_old_arguments_and_push_result(
            stack,
            stack_ptr,
            num_args,
            rcvr,
        )
