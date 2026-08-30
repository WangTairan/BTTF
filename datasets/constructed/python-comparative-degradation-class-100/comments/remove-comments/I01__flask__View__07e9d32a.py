from __future__ import annotations
import typing as t
from . import typing as ft
from .globals import current_app
from .globals import request

class View:
    

     
     
     
    methods: t.ClassVar[t.Collection[str] | None] = None

     
     
     
    provide_automatic_options: t.ClassVar[bool | None] = None

     
     
     
     
     
     
    decorators: t.ClassVar[list[t.Callable[..., t.Any]]] = []

     
     
     
     
     
     
     
     
     
     
    init_every_request: t.ClassVar[bool] = True

    def dispatch_request(self) -> ft.ResponseReturnValue:
        
        raise NotImplementedError()

    @classmethod
    def as_view(
        cls, name: str, *class_args: t.Any, **class_kwargs: t.Any
    ) -> ft.RouteCallable:
        
        if cls.init_every_request:

            def view(**kwargs: t.Any) -> ft.ResponseReturnValue:
                self = view.view_class(   
                    *class_args, **class_kwargs
                )
                return current_app.ensure_sync(self.dispatch_request)(**kwargs)   

        else:
            self = cls(*class_args, **class_kwargs)   

            def view(**kwargs: t.Any) -> ft.ResponseReturnValue:
                return current_app.ensure_sync(self.dispatch_request)(**kwargs)   

        if cls.decorators:
            view.__name__ = name
            view.__module__ = cls.__module__
            for decorator in cls.decorators:
                view = decorator(view)

         
         
         
         
         
        view.view_class = cls   
        view.__name__ = name
        view.__doc__ = cls.__doc__
        view.__module__ = cls.__module__
        view.methods = cls.methods   
        view.provide_automatic_options = cls.provide_automatic_options   
        return view
