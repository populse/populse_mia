# -*- coding: utf-8 -*-
"""
A proof that the auto-formatter works.
"""

# Original code

# fmt: off

def print_your_age(age:int)-> None:
    """Documentation"""

       # Creates the print message
    print_message = f'Your age is {age}.'

    # Prints it
    print( print_message )

def super_complex_function(arg_1: int, arg_2: int, arg_3: int) -> bool:
   """This function is very complex and thus has a very long documentation that certainly exceeds the pep8 line length standard."""
   if(arg_1*arg_2*arg_3 + arg_1*arg_2*arg_3 + arg_1*arg_2*arg_3 + arg_1*arg_2*arg_3 + arg_1*arg_2*arg_3 + arg_1*arg_2*arg_3 + arg_1*arg_2*arg_3 > 1000):
      return False
   else:
      return True

# Auto-formatted code

# fmt: on


def print_your_age(age: int) -> None:
    """Documentation"""

    # Creates the print message
    print_message = f"Your age is {age}."

    # Prints it
    print(print_message)


def super_complex_function(arg_1: int, arg_2: int, arg_3: int) -> bool:
    """This function is very complex and thus has a very long documentation that certainly exceeds the pep8 line length standard."""
    if (
        arg_1 * arg_2 * arg_3
        + arg_1 * arg_2 * arg_3
        + arg_1 * arg_2 * arg_3
        + arg_1 * arg_2 * arg_3
        + arg_1 * arg_2 * arg_3
        + arg_1 * arg_2 * arg_3
        + arg_1 * arg_2 * arg_3
        > 1000
    ):
        return False
    else:
        return True


if __name__ == "__main__":
    print_your_age(22)
    print(f"result = {super_complex_function(12, 13, 14)}")
