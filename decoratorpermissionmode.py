command_perms =  {
                    "function1": {123, 456},
                    "function2": {234, 345}
                  }


def perm(wrapped_handler):
    def handler(event):
        if 123 in command_perms[wrapped_handler.__name__]:
            wrapped_handler(event)
    return handler

@perm
def function1(event):
    print("wow1")

@perm
def function2(event):
    print("wow2")


function1(0)
function2(0)
