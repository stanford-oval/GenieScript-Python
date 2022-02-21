from geniescript import *

dlg = make_dialog()


class Variable(GenieVar):
    def __init__(self, name: GenieString, number: GenieInt):
        self.number = number
        self.name = name


@dlg.task
def calculator() -> None:
    variables: {GenieString: Variable} = {}

    @dlg.skill
    def create_variable(name: GenieString, number: GenieInt) -> None:
        dlg.say(f"{name} created.")
        var = Variable(name, number)
        variables[name] = var

    @dlg.skill
    def get_variable(name: GenieString) -> GenieInt:
        return variables[name].number

    @dlg.skill
    def add(a: GenieInt, b: GenieInt) -> GenieInt:
        return GenieInt(a + b)

    @dlg.task
    def add_many() -> GenieInt:
        numbers: [GenieInt] = []
        dlg.say(f"Sure! let me know what would you like to add")

        @dlg.skill
        def add_once(number: GenieInt) -> None:
            dlg.say(f"{number} added")
            nonlocal numbers
            numbers += [number]

        @dlg.skill
        def exit_add() -> None:
            dlg.exit(GenieInt(sum(numbers)), add_many)

    @dlg.skill
    def assign(name: GenieString, number: GenieInt) -> None:
        if name in variables:
            dlg.say(f"{name} assigned as {number}.")
            variables[name].number = number
        else:
            dlg.say(f"{name} not exist")

    @dlg.skill
    def speak_number(number: GenieInt) -> None:
        dlg.say(f"The result is {number}.")

    @dlg.skill
    def end_calculator() -> None:
        dlg.say("Bye.")

    dlg.say("You can ask me to do simple calculation operators!")


print("Dialog example \n================")
# runtime
dlg.render_dialog(calculator, [
    # basic genie stuff, compound skills
    "speak_number(add(1, 2))",
    "create_variable(\"a\", 1)",
    "create_variable(\"b\", add(get_variable(\"a\"), 1))",
    "assign(\"a\", add(get_variable(\"a\"), get_variable(\"b\")))",
    "speak_number(get_variable(\"a\"))",
    # enters a computer guided conversation
    "speak_number(add_many())",
    "add_once(1)",
    # In a computer guided conversation, user can still call some other functions in the outer scope
    "speak_number(add(1, 2))",
    # User can also use functions in the outer scope to help the task in the current scope
    "assign(\"b\", add(get_variable(\"a\"), get_variable(\"b\")))",
    "add_once(get_variable(\"b\"))",
    "exit_add()"
])

print("\n\n\nContext + actions in the program\n================")
# inspect all the different context in the program, and the supported actions in the context.
dlg.inspect_context(calculator)
