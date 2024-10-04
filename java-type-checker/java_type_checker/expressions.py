# -*- coding: utf-8 -*-

from .types import JavaBuiltInTypes, JavaTypeError


class JavaExpression(object):
    """AST for simple Java expressions.

    Note that this library deals only with compile-time types, and this class therefore does not
    actually *evaluate* expressions.
    """

    def static_type(self):
        pass

    def check_types(self):
        """Examines the structure of this expression for static type errors.

        Raises a JavaTypeError if there is an error. If there is no error, this method has no effect
        and returns nothing.

        Subclasses must override this method.
        """
        raise NotImplementedError(type(self).__name__ + " must override check_types()")


class JavaVariable(JavaExpression):
    """An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.

    In a real Java language implementation, the declared_type would be filled in by a name resolver
    after the initial construction of the AST. In this sample project, however, we simply specify
    the declared_type for every variable reference.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable (str)
        self.declared_type = declared_type  #: The declared type of the variable (JavaType)

    def static_type(self):
        return self.declared_type
    
    def check_types(self):
        pass


class JavaLiteral(JavaExpression):
    """A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (JavaType)
    
    def static_type(self):
        return self.type

    def check_types(self):
        pass


class JavaNullLiteral(JavaLiteral):
    """The literal value `null` in Java code.
    """
    def __init__(self):
        super().__init__("null", JavaBuiltInTypes.NULL)

    def static_type(self):
        return JavaBuiltInTypes.NULL


class JavaAssignment(JavaExpression):
    """The assignment of a new value to a variable.

    Attributes:
        lhs (JavaVariable): The variable whose value this assignment updates.
        rhs (JavaExpression): The expression whose value will be assigned to the lhs.
    """
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    
    def static_type(self):
        return self.lhs.static_type()
    
    def check_types(self):
        lhs_type = self.lhs.static_type()
        rhs_type = self.rhs.static_type()
        if not rhs_type.is_subtype_of(lhs_type):
            raise JavaTypeMismatchError("Cannot assign {0} to variable {1} of type {2}".format(rhs_type.name, self.lhs.name, lhs_type.name))


class JavaMethodCall(JavaExpression):
    """A Java method invocation.

    For example, in this Java code::

        foo.bar(0, 1)

    - The receiver is `JavaVariable(foo, JavaObjectType(...))`
    - The method_name is `"bar"`
    - The args are `[JavaLiteral("0", JavaBuiltInTypes.INT), ...etc...]`

    Attributes:
        receiver (JavaExpression): The object whose method we are calling
        method_name (String): The name of the method to call
        args (list of Expressions): The arguments to pass to the method
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver
        self.method_name = method_name
        self.args = args
        
    def check_types(self):
        if not self.receiver.static_type():
            return
        receiver_type = self.receiver.static_type()
        if receiver_type is None:
            raise JavaTypeError("Receiver's type is not defined for method call.")

        method = receiver_type.method_named(self.method_name)
        if method is None:
            raise JavaTypeError(f"{receiver_type.name} has no method named {self.method_name}")

        expected_count = len(method.parameter_types)
        actual_count = len(self.args)

        if actual_count != expected_count:
            raise JavaArgumentCountError(
                f"Wrong number of arguments for {receiver_type.name}.{self.method_name}(): expected {expected_count}, got {actual_count}"
            )

        for arg, param_type in zip(self.args, method.parameter_types):
            arg_type = arg.static_type()
            if not arg_type.is_subtype_of(param_type):
                raise JavaTypeMismatchError(
                    f"{receiver_type.name}.{self.method_name}() expects arguments of type ({', '.join(pt.name for pt in method.parameter_types)}), but got ({', '.join(str(at.static_type().name) for at in self.args)})"
                )





        

class JavaConstructorCall(JavaExpression):
    """
    A Java object instantiation

    For example, in this Java code::

        new Foo(0, 1, 2)

    - The instantiated_type is `JavaObjectType("Foo", ...)`
    - The args are `[JavaLiteral("0", JavaBuiltInTypes.INT), ...etc...]`

    Attributes:
        instantiated_type (JavaType): The type to instantiate
        args (list of Expressions): Constructor arguments
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type
        self.args = args

    def static_type(self):
        return self.instantiated_type
    
    def check_types(self):
        if not self.instantiated_type.is_instantiable:
            raise JavaIllegalInstantiationError(
                "{0} is not instantiable".format(self.instantiated_type.name)
            )

        # Check the argument count
        constructor = self.instantiated_type.constructor
        if len(self.args) != len(constructor.param_types):
            raise JavaArgumentCountError(
                "Wrong number of arguments for {0} constructor: expected {1}, got {2}".format(
                    self.instantiated_type.name, len(constructor.param_types), len(self.args)
                )
            )

        # Check the argument types
        for arg, param_type in zip(self.args, constructor.param_types):
            arg_type = arg.static_type()
            if not arg_type.is_subtype_of(param_type):
                raise JavaTypeMismatchError(
                    "{0} constructor expects arguments of type {1}, but got {2}".format(
                        self.instantiated_type.name, param_type.name, arg_type.name
                    )
                )

        # Recursively check the types of all arguments
        for arg in self.args:
            arg.check_types()


class JavaTypeMismatchError(JavaTypeError):
    """Indicates that one or more expressions do not evaluate to the correct type.
    """
    pass


class JavaArgumentCountError(JavaTypeError):
    """Indicates that a call to a method or constructor has the wrong number of arguments.
    """
    pass


class JavaIllegalInstantiationError(JavaTypeError):
    """Raised in response to `new Foo()` where `Foo` is not an instantiable type.
    """
    pass


def _names(named_things):
    """Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
