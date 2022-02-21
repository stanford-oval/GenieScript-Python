import inspect
import types
from abc import ABC
from typing import Callable, Optional


class GenieVar(ABC):
    pass


class GenieInt(GenieVar, int):
    pass


class GenieString(GenieVar, str):
    pass


def make_dialog():
    registry: {Optional[Callable]: {}} = {None: {}}
    current_function = [None]
    exit_message = None
    inspection_mode = False

    def verify_function(func):
        signature = inspect.signature(func)
        for key, value in signature.parameters.items():
            if not issubclass(value.annotation.__class__, GenieVar.__class__):
                raise Exception(f"Input parameter {key} of {func.__name__} is not a {GenieVar.__name__}.")
        if signature.return_annotation is not None:
            if not issubclass(signature.return_annotation.__class__, GenieVar.__class__):
                raise Exception("Return value of {func.__name__} is not a {GenieVar.__name__}.")
        return True

    def combined_registry():
        combined = {}
        for registry_item in registry.values():
            combined.update(registry_item)
        return combined

    def create_enter_func(wrapped_func):
        def func():
            # print(f"entering wrapped_func {wrapped_func.original_func}")
            nonlocal current_function
            current_function += [wrapped_func]
            registry[wrapped_func] = {}
        return func

    def create_exit_func(wrapped_func):
        def func(force=False):
            if (not inspection_mode) or force:
                # print(f"exiting {wrapped_func.original_func}")
                del registry[wrapped_func]
                assert current_function[-1] == wrapped_func
                current_function.pop()
        return func

    def register_action(func, interactive, prompt=None):
        if prompt is None:
            prompt = ""
        # print(f"registering {func} under {current_function[-1]}")
        verify_function(func)

        def wrapped_func(*args, **kwargs):
            enter_func = create_enter_func(wrapped_func)
            exit_func = create_exit_func(wrapped_func)
            if interactive:
                enter_func()
            new_args = []
            for arg in args:
                if isinstance(arg, types.GeneratorType):
                    result = yield from arg
                    new_args += [result]
                else:
                    new_args += [arg]
            new_kwargs = {}
            for kwarg_key, kwarg_value in kwargs.items():
                if isinstance(kwarg_value, types.GeneratorType):
                    result = yield from kwarg_value
                    new_kwargs[kwarg_key] = result
                else:
                    new_kwargs[kwarg_key] = kwarg_value
            return_value = func(*new_args, **new_kwargs)
            if interactive:
                while True:
                    yield "prompt", prompt, registry, wrapped_func.original_func.__qualname__
                    action = yield
                    result = eval(action, combined_registry())

                    result_start = True
                    result_break = False
                    while True:
                        try:
                            if result_start:
                                result_yield = next(result)
                                result_start = False
                            else:
                                result_action = yield
                                next(result)
                                result_yield = result.send(result_action)
                            if result_yield[0] == "prompt":
                                yield result_yield
                            else:
                                assert result_yield[0] == "exit"
                                assert result_yield[1] in current_function
                                if wrapped_func == result_yield[1]:
                                    return_value = result_yield[2]
                                    result_break = True
                                    break
                                else:
                                    exit_func()
                                    yield result_yield
                        except StopIteration:
                            break
                    if result_break:
                        break
                exit_func()
            nonlocal exit_message
            if exit_message is not None:
                exit_message_temp = exit_message
                exit_message = None
                yield exit_message_temp

            return return_value

        wrapped_func.original_func = func
        wrapped_func.interactive = interactive
        registry[current_function[-1]][func.__name__] = wrapped_func
        return wrapped_func  # normally a decorator returns a wrapped function,
        # but here we return func unmodified, after registering it

    def skill(func):
        return register_action(func, False)

    def task(func, prompt=None):
        return register_action(func, True, prompt)

    def say(content: str):
        if not inspection_mode:
            print(f"agent says: \"{content}\"")

    def exit(exit_value=None, func=None):
        if func is None:
            func = current_function[-1]
        nonlocal exit_message
        exit_message = "exit", func, exit_value

    def execute(function):
        obj = function()
        prompt = print(next(obj))
        while True:
            print(f"prompt: {prompt}")
            next(obj)
            prompt = obj.send(input())

    def render_dialog(function, input_list):
        obj = function()
        prompt = next(obj)
        for input_cmd in input_list:
            # print(f"prompt: {prompt}")
            print(f"context: {prompt[3]}")
            next(obj)
            print(f"user: {input_cmd}")
            prompt = obj.send(input_cmd)

    def inspect_context(function):
        nonlocal inspection_mode, registry, current_function
        inspection_mode = True
        inspect_context_impl(function)
        inspection_mode = False

    def inspect_context_impl(function):
        result = function()
        try:
            next(result)
        except StopIteration:
            pass
        print(f"context: {function.original_func.__qualname__}, available actions: {combined_registry().keys()}")
        for local_action in registry[current_function[-1]].values():
            if local_action.interactive:
                inspect_context_impl(local_action)
        create_exit_func(function)(force=True)

    dialog_ctx = type('', (object,), {})()
    dialog_ctx.all_actions = registry
    dialog_ctx.skill = skill
    dialog_ctx.task = task
    dialog_ctx.say = say
    dialog_ctx.exit = exit
    dialog_ctx.render_dialog = render_dialog
    dialog_ctx.inspect_context = inspect_context

    return dialog_ctx

